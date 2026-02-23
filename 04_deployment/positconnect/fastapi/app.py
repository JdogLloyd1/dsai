"""
Minimal FastAPI application for Posit Connect deployment.
"""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
import asyncio

# Create the FastAPI ASGI application
fastapi_app = FastAPI(
    title="FastAPI Example API",
    description="FastAPI example description.",
    version="1.0.0"
)


@fastapi_app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "FastAPI is running!", "docs": "/docs"}


@fastapi_app.get("/echo")
async def echo(msg: str = ""):
    """Echo back the input."""
    return {"msg": f"The message is: '{msg}'"}


@fastapi_app.post("/sum")
async def sum_numbers(a: float, b: float):
    """Return the sum of two numbers."""
    return {"result": a + b}


@fastapi_app.get("/__docs__/")
async def docs_redirect():
    """Redirect to FastAPI interactive documentation."""
    return RedirectResponse(url="/docs")


# WSGI wrapper for ASGI application (needed for Posit Connect/Gunicorn)
class ASGItoWSGI:
    """Convert ASGI application to WSGI-compatible interface."""
    
    def __init__(self, asgi_app):
        self.asgi_app = asgi_app
    
    def __call__(self, environ, start_response):
        """WSGI application interface."""
        # Convert WSGI environ to ASGI scope
        scope = {
            "type": "http",
            "http_version": environ.get("SERVER_PROTOCOL", "HTTP/1.1").split("/")[1],
            "method": environ["REQUEST_METHOD"],
            "scheme": environ.get("wsgi.url_scheme", "http"),
            "path": environ.get("PATH_INFO", ""),
            "raw_path": environ.get("PATH_INFO", "").encode(),
            "query_string": environ.get("QUERY_STRING", "").encode(),
            "root_path": environ.get("SCRIPT_NAME", ""),
            "headers": [
                (k.replace("HTTP_", "").lower().replace("_", "-").encode(), v.encode())
                for k, v in environ.items()
                if k.startswith("HTTP_")
            ],
            "client": (environ.get("REMOTE_ADDR", ""), int(environ.get("REMOTE_PORT", 0) or 0)),
            "server": (environ.get("SERVER_NAME", ""), int(environ.get("SERVER_PORT", 80) or 80)),
        }
        
        # Read request body
        request_body = b""
        if "CONTENT_LENGTH" in environ:
            content_length = int(environ.get("CONTENT_LENGTH", 0))
            if content_length > 0:
                request_body = environ["wsgi.input"].read(content_length)
        
        body_chunks = [request_body] if request_body else []
        body_index = 0
        
        async def receive():
            nonlocal body_index
            if body_index < len(body_chunks):
                chunk = body_chunks[body_index]
                body_index += 1
                return {"type": "http.request", "body": chunk, "more_body": body_index < len(body_chunks)}
            return {"type": "http.request", "body": b"", "more_body": False}
        
        response_status = None
        response_headers = []
        response_body_chunks = []
        
        async def send(message):
            nonlocal response_status, response_headers
            if message["type"] == "http.response.start":
                status_code = message["status"]
                status_text = message.get("status_text", "OK")
                response_status = f"{status_code} {status_text}"
                response_headers = [
                    (k.decode() if isinstance(k, bytes) else k, 
                     v.decode() if isinstance(v, bytes) else v)
                    for k, v in message.get("headers", [])
                ]
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                if body:
                    response_body_chunks.append(body)
        
        # Run the ASGI application
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        loop.run_until_complete(self.asgi_app(scope, receive, send))
        
        # Start WSGI response
        start_response(response_status, response_headers)
        
        # Return response body
        return response_body_chunks


# Detect if we're running under WSGI (Gunicorn/Posit Connect) or ASGI (uvicorn)
# WSGI servers set wsgi.* keys in environ, but we can't check that here
# Instead, we'll check for common WSGI environment indicators
import os

# For Posit Connect: use WSGI wrapper (Gunicorn expects WSGI)
# For local uvicorn: use FastAPI directly (uvicorn expects ASGI)
# We detect by checking if we're likely in a WSGI environment
# Posit Connect typically sets certain environment variables, but as a fallback,
# we'll make 'app' be the WSGI wrapper for production deployments
# and use 'fastapi_app' directly for local testing via uvicorn

# Default to WSGI wrapper for Posit Connect compatibility
# For local testing, use: uvicorn app:fastapi_app
app = ASGItoWSGI(fastapi_app)
