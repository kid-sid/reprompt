from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from routes.inference_router import router as inference_router
from routes.auth_router import router as auth_router
import logging

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

logger.info("All routers included successfully")

@app.get("/")
async def root():
    return {"message": "Welcome to Reprompt Chatbot API"}

@app.get("/frontend")
async def frontend():
    """Serve the frontend application"""
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")

@app.get("/auth")
async def auth_page():
    """Serve the authentication page"""
    from fastapi.responses import FileResponse
    return FileResponse("static/auth.html")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="debug")
