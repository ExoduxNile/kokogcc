from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tropley.com"],  # Your frontend origin
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],  # Allow GET and OPTIONS for simplicity
    allow_headers=["*"]
)

@app.get("/", response_class=HTMLResponse)
async def serve_hello_world():
    """Serve a simple Hello World HTML page."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hello World</title>
    </head>
    <body>
        <h1>Hello World!</h1>
        <p>This is a test page served by the FastAPI server to confirm connectivity.</p>
    </body>
    </html>
    """	
