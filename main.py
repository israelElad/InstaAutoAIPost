#!/usr/bin/env python3
import os
import sys
import time
import logging
import datetime

LOCK_FILE_PATH = "/app/locks/login_failed.lock"

# Set up logging first
# Ensure basicConfig is only called once to prevent duplicate loggers
if not logging.root.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )
logger = logging.getLogger(__name__)

def wait_on_lock():
    while os.path.exists(LOCK_FILE_PATH):
        logging.warning(f"Lock file {LOCK_FILE_PATH} exists. Waiting for it to be deleted...")
        time.sleep(60)

# Wait on lock logic BEFORE any Instagram-related imports
wait_on_lock()

import threading
from pathlib import Path
import argparse
from src.services.instagram_service import InstagramService
import subprocess

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.handlers.lambda_handler import lambda_handler
from src.config import config
# from src.web_server import start_web_server
import json

LOCK_FILE = "login_failed.lock"
DEPLOY_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE_PATH = "/app/session.json"

# (No need to wait again in main or other functions)

def debug_aws_env_and_metadata():
    logger.info("[DEBUG] Printing AWS-related environment variables:")
    for k, v in os.environ.items():
        if k.startswith("AWS"):
            logger.info(f"[ENV] {k}={v}")
        elif k == "INSTAGRAM_USERNAME":
            logger.info(f"[ENV] {k}={v}")
        elif k == "INSTAGRAM_PASSWORD":
            logger.info(f"[ENV] {k} is set: {'yes' if v else 'no'} (value hidden)")
        elif k == "S3_BUCKET_NAME":
            logger.info(f"[ENV] {k}={v}")
    try:
        logger.info("[DEBUG] Attempting to curl EC2 instance metadata for IAM info...")
        result = subprocess.run([
            "curl", "-s", "http://169.254.169.254/latest/meta-data/iam/info"
        ], capture_output=True, text=True, timeout=2)
        logger.info(f"[IMDS] {result.stdout.strip() if result.stdout else 'No response'}")
    except Exception as e:
        logger.warning(f"[IMDS] Could not reach instance metadata: {e}")

def run_main_application():
    """Run the main Instagram auto-posting application."""
    logger.info("Starting Instagram Auto-Posting Service")
    # (Removed: Lockout mechanism: exit immediately if lock file exists)
    try:
        # Validate configuration (optional for web server)
        try:
            if config.validate():
                logger.info("Configuration validated successfully")
                try:
                    # Run the main handler
                    response = lambda_handler({}, None)
                    logger.info(f"Handler response: {response}")
                    # If handler failed due to Instagram login/session, create lock file and exit 0
                    if isinstance(response, dict):
                        body = response.get("body")
                        if body and ("login" in body.lower() or "session" in body.lower() or "unexpected error" in body.lower()):
                            logger.error("Instagram login/session error detected. Creating lock file and waiting for manual intervention.")
                            with open(LOCK_FILE_PATH, "w") as f:
                                f.write(f"[{datetime.datetime.utcnow().isoformat()} UTC] Instagram login/session failure. Manual intervention required.\n")
                            # Instead of exit, wait for lock file to be deleted
                            wait_on_lock()
                    return response
                except Exception as e:
                    logger.error(f"Handler error: {e}")
                    logger.error("Creating lock file and waiting for manual intervention (handler error)")
                    with open(LOCK_FILE_PATH, "w") as f:
                        f.write(f"[{datetime.datetime.utcnow().isoformat()} UTC] Handler error: {e}\n")
                    wait_on_lock()
            else:
                logger.warning("Configuration validation failed")
                logger.info("Web server will continue running without Instagram functionality")
                logger.info("Exiting with code 0 to avoid restart loop (web server only mode)")
                sys.exit(0)
        except Exception as e:
            logger.warning(f"Configuration validation failed: {e}")
            logger.info("Web server will continue running without Instagram functionality")
            logger.info("Exiting with code 0 to avoid restart loop (config exception)")
            sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}")
        logger.info("Creating lock file and waiting for manual intervention (application error)")
        with open(LOCK_FILE_PATH, "w") as f:
            f.write(f"[{datetime.datetime.utcnow().isoformat()} UTC] Application error: {e}\n")
        wait_on_lock()

def main():
    """Main application entry point."""
    os.makedirs("logs", exist_ok=True)

    debug_aws_env_and_metadata()

    # Run main application once
    try:
        result = run_main_application()
        logger.info("Main application completed successfully")
        # If config failed, exit 0 to avoid restart loop
        if isinstance(result, dict) and result.get("status") == "web_server_only":
            logger.info("Exiting with code 0 to avoid restart loop (web server only mode)")
            sys.exit(0)
    except Exception as e:
        logger.error(f"Main application failed: {e}")
    finally:
        # Ensure all logs are flushed before exiting
        logging.shutdown()
        # Exit 0 to avoid restart loop on failure
        sys.exit(0)
    
    # Keep the application running
    # logger.info("Keeping application running...")
    # try:
    #     while True:
    #         time.sleep(60)  # Sleep for 1 minute
    #         logger.debug("Application heartbeat")
    # except KeyboardInterrupt:
    #     logger.info("Application stopped by user")
    # except Exception as e:
    #     logger.error(f"Application error: {e}")
    #     raise

if __name__ == "__main__":
    main()
