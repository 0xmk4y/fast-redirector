import os
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from supabase import create_client, Client
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class SupabaseService:
    _client: Optional[Client] = None
    
    @classmethod
    def init(cls) -> None:
        """Initialize the Supabase client."""
        url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        
        if not url or not key:
            logger.error("Supabase credentials not found in environment variables")
            raise RuntimeError("Missing Supabase credentials")
            
        cls._client = create_client(url, key)
        logger.info("Supabase client initialized successfully")
    
    @classmethod
    def get_client(cls) -> Client:
        """Get the initialized Supabase client."""
        if cls._client is None:
            logger.error("Attempted to access Supabase client before initialization")
            raise RuntimeError("Supabase client not initialized")
        return cls._client

# Application lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    logger.info("Starting application...")
    SupabaseService.init()
    yield
    logger.info("Shutting down application...")

# FastAPI application
app = FastAPI(
    title="Alpha redirect",
    description="",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") == "development" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") == "development" else None,
    openapi_url="/openapi.json" if os.getenv("ENVIRONMENT") == "development" else None,
    lifespan=lifespan
)

def get_supabase():
    """Dependency to get the Supabase client."""
    return SupabaseService.get_client()

@app.get("/r/{path}")
async def redirect_short_url(path: str, request: Request, supabase: Client = Depends(get_supabase)):
    """Redirect short URLs to their original destinations."""
    try:
        # Handle special cases
        if len(path) > 11:
            logger.warning(f"Blocked suspicious long path: {path}")
            return RedirectResponse(url="https://www.google.com", status_code=302)
            
        if path == 'favicon.ico':
            return RedirectResponse(url="https://www.google.com", status_code=302)
        
        # Look up the short URL in Supabase
        logger.info(f"Looking up slug path: {path}")
        response = supabase.table("_redirects").select("*").eq("slug", path).execute()
        
        # Handle the redirect
        if response.data:
            target_url = response.data[0].get("target_url")
            if target_url:
                # Ensure URL has a protocol
                if not target_url.startswith(("http://", "https://")):
                    target_url = f"https://{target_url}"
                
                # Only append email parameter if provided
                email = request.query_params.get('email')
                if email:
                    # Check if target URL already has query parameters
                    if '?' in target_url:
                        target_url = f"{target_url}&email={email}"
                    else:
                        target_url = f"{target_url}?email={email}"
                
                logger.info(f"Redirecting to: {target_url}")
                return RedirectResponse(url=target_url, status_code=302)
        
        # Default redirect for non-existent paths
        logger.info(f"No match found for path: {path}")
        return RedirectResponse(url="https://www.google.com", status_code=302)
        
    except Exception as e:
        logger.exception("Error during redirect handling")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# For local development only
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)