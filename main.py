import logging
import os
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from controllers import langchain_controller
from slowapi.errors import RateLimitExceeded
from limiter import limiter
from fastapi.openapi.utils import get_openapi

from security import validate_jwt

# Configure Logging
logging.basicConfig(
    level=logging.INFO,  # Set the desired log level (INFO or DEBUG)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI()

logger.info('API is starting up')

# Allowed origins
origins = [
    "http://localhost",
    "https://localhost:3000",
]

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TEMPORARY ONLY
    allow_credentials=True,  # Allow credentials like cookies
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning(f"Rate limit exceeded for {request.url}: {exc}")
    return PlainTextResponse(str(exc), status_code=429)

# Define the HTTP Bearer dependency
http_bearer = HTTPBearer()


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    # Generate OpenAPI schema
    openapi_schema = get_openapi(
        title="Langchain FastAPI",
        version="1.0.0",
        description="API for chatbot",
        routes=app.routes,
    )

    # Add BearerAuth to the components
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    # Apply BearerAuth globally to all endpoints
    openapi_schema["security"] = [{"BearerAuth": []}]
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Override FastAPI's default OpenAPI schema
app.openapi = custom_openapi

# Include routers from different controllers
app.include_router(langchain_controller.router, prefix="/api/langchain", tags=["LangChain"])



DEBUG = os.getenv('DEBUG', 'False').lower() in ['true', '1', 't']
logger.info(f"DEBUG environment variable is set to: {DEBUG}")

# Attach the limiter to the app
app.state.limiter = limiter

# Log requests middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.get("/health")
async def checkHealth(payload = Depends(validate_jwt)):
    logger.info("Health check endpoint was accessed.")
    return {"message": "healthy"}
