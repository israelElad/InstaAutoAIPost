# from fastapi import FastAPI, Request
# from fastapi.responses import JSONResponse
# import socket
# import os
#
# app = FastAPI()
#
# @app.get("/health")
# def health():
#     return {"status": "healthy"}
#
# @app.get("/status")
# def status():
#     return {"status": "ok", "service": "InstaAutoAIPost"}
#
# @app.get("/debug/session")
# def debug_session():
#     session_file = os.getenv("INSTAGRAM_SESSION_FILE", "/app/session.json")
#     if os.path.exists(session_file):
#         return {"session_file": session_file, "exists": True}
#     else:
#         return {"session_file": session_file, "exists": False}
#
# @app.get("/debug/ip")
# def debug_ip(request: Request):
#     client_host = request.client.host
#     server_ip = socket.gethostbyname(socket.gethostname())
#     return {"client_ip": client_host, "server_ip": server_ip}
#
# @app.get("/debug/device")
# def debug_device():
#     return {"platform": os.sys.platform, "python_version": os.sys.version}
#
# @app.get("/debug/rate_limit")
# def debug_rate_limit():
#     # Placeholder for rate limit info
#     return {"rate_limit": "not_implemented"}
#
# def start_web_server():
#     import threading
#     import uvicorn
#     thread = threading.Thread(target=uvicorn.run, args=("src.web_server:app",), kwargs={"host": "0.0.0.0", "port": 8000, "log_level": "info"}, daemon=True)
#     thread.start()
#     return thread 