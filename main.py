#!/usr/bin/env python3
import os
import sys
import time
import logging
import threading
from datetime import datetime
from pathlib import Path
import argparse
from src.services.instagram_service import InstagramService

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.handlers.lambda_handler import lambda_handler
from src.config import config
# from src.web_server import start_web_server
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_main_application():
    """Run the main Instagram auto-posting application."""
    logger.info("Starting Instagram Auto-Posting Service")
    
    try:
        # Validate configuration (optional for web server)
        try:
            if config.validate():
                logger.info("Configuration validated successfully")
                
                # Run the main handler
                response = lambda_handler({}, None)
                logger.info(f"Handler response: {response}")
                
                return response
            else:
                logger.warning("Configuration validation failed")
                logger.info("Web server will continue running without Instagram functionality")
                return {"status": "web_server_only", "message": "Configuration validation failed"}
        except Exception as e:
            logger.warning(f"Configuration validation failed: {e}")
            logger.info("Web server will continue running without Instagram functionality")
            return {"status": "web_server_only", "message": str(e)}
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise

def main():
    """Main application entry point."""
    os.makedirs("logs", exist_ok=True)

    # Run main application once
    try:
        result = run_main_application()
        logger.info("Main application completed successfully")
    except Exception as e:
        logger.error(f"Main application failed: {e}")
    
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