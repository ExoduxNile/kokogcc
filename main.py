from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 503:
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head><title>503 Service Unavailable</title></head>
            <body>
                <h1>503 - Service Unavailable</h1>
                <p>The server is under heavy load or maintenance. Try again later. 🚧</p>
            </body>
            </html>
            """,
            status_code=503,
        )
    return await http_exception_handler(request, exc)

