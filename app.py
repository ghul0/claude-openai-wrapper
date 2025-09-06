"""
FastAPI server implementing OpenAI Chat Completions API with Claude Code backend
"""
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
from contextlib import asynccontextmanager
from models import ChatCompletionRequest, ChatCompletionResponse, ErrorResponse, ErrorDetail
from claude_wrapper import ClaudeCodeWrapper

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global wrapper instance
claude_wrapper = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global claude_wrapper
    
    # Startup
    logger.info("Starting Claude Code OpenAI API server...")
    claude_wrapper = ClaudeCodeWrapper()
    logger.info("Server initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down server...")


# Create FastAPI app
app = FastAPI(
    title="Claude Code OpenAI API",
    description="OpenAI-compatible API server using Claude Code SDK",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for browser-based clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Claude Code OpenAI API",
        "version": "1.0.0",
        "endpoints": {
            "chat_completions": "/v1/chat/completions",
            "health": "/health",
            "models": "/v1/models"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "claude-code-openai-api"
    }


@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI API compatibility)"""
    models = [
        {
            "id": "claude-3-5-sonnet-20241022",
            "object": "model",
            "owned_by": "anthropic"
        },
        {
            "id": "claude-3-5-haiku-20241022",
            "object": "model",
            "owned_by": "anthropic"
        },
        # Aliases for easier use
        {
            "id": "gpt-4",
            "object": "model",
            "owned_by": "claude-proxy"
        },
        {
            "id": "gpt-3.5-turbo",
            "object": "model",
            "owned_by": "claude-proxy"
        }
    ]
    
    return {
        "object": "list",
        "data": models
    }


@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    authorization: str = Header(None, regex="^Bearer .+")
):
    """
    Main endpoint implementing OpenAI Chat Completions API
    """
    try:
        # Validate authorization (optional)
        api_key = None
        if authorization:
            api_key = authorization.replace("Bearer ", "")
        
        # Check API key if configured
        expected_key = os.getenv("API_KEY")
        if expected_key and api_key != expected_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
        
        # Log request
        logger.info(f"Processing chat completion request - Model: {request.model}, Messages: {len(request.messages)}")
        
        # Validate request
        if request.n != 1:
            raise HTTPException(
                status_code=400,
                detail="Only n=1 is supported"
            )
        
        if request.stream:
            raise HTTPException(
                status_code=400,
                detail="Streaming is not yet supported"
            )
        
        # Process with Claude
        response = await claude_wrapper.process_request(request)
        
        logger.info(f"Request completed successfully - Tokens: {response.usage.total_tokens}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        
        # Create error response
        error = ErrorDetail(
            message=str(e),
            type="internal_error",
            code="internal_server_error"
        )
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(error=error).model_dump()
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions in OpenAI format"""
    error = ErrorDetail(
        message=exc.detail,
        type="invalid_request_error",
        code=str(exc.status_code)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=error).model_dump()
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")