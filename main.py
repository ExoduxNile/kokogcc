from fastapi.requests import Request
from starlette.exceptions import HTTPException as StarletteHTTPException

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
    # Fallback to default handler for other status codes
    return await http_exception_handler(request, exc)
