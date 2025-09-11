from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routes.inference_router import router as inference_router
from routes.auth_router import router as auth_router
from routes.prompt_history_router import router as prompt_history_router
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Create logger for this module
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Reprompt Chatbot API",
    description="A FastAPI application for AI-powered prompt optimization with authentication",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
logger.info("Including inference router...")
app.include_router(inference_router, prefix="/api/v1", tags=["inference"])

logger.info("Including auth router...")
app.include_router(auth_router, prefix="/api/v1", tags=["authentication"])

logger.info("Including prompt history router...")
app.include_router(prompt_history_router, prefix="/api/v1", tags=["prompt-history"])

logger.info("All routers included successfully")

@app.get("/")
async def root():
    """Redirect to auth page by default"""
    return FileResponse("static/auth.html")

@app.get("/auth")
async def auth_page():
    """Serve the authentication page"""
    return FileResponse(os.path.join("static", "auth.html"))

@app.get("/chatbot")
async def chatbot_page():
    """Serve the chatbot page"""
    return FileResponse(os.path.join("static", "chatbot.html"))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="debug")
