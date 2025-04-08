import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import uvicorn
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class SupabaseService:
    client: Client = None

    @classmethod
    def init(cls):
        url: str = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        key: str = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        if not url or not key:
            logger.error("Supabase credentials not found in environment variables.")
            raise RuntimeError("Missing Supabase credentials.")
        cls.client = create_client(url, key)
        logger.info("Supabase client initialized.")

    @classmethod
    def get_client(cls) -> Client:
        if cls.client is None:
            logger.error("Attempted to access Supabase client before initialization.")
            raise RuntimeError("Supabase client not initialized.")
        return cls.client

@asynccontextmanager
async def lifespan(app: FastAPI):
    SupabaseService.init()
    yield
    # Add shutdown logic here if needed
    logger.info("Shutting down app...")

app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan
)

@app.get("/{path}")
def redirector(path: str):
    supabase = SupabaseService.get_client()
    try:
        if len(path) > 11:
            logger.warning(f"Blocked suspicious long path: {path}")
            return RedirectResponse(url="https://www.google.com", status_code=302)
        if path == 'favicon.ico':
            return RedirectResponse(url="https://www.google.com", status_code=302)

        logger.info(f"Looking up short path: {path}")
        response = supabase.table("urls").select("*").eq("short", path).execute()
        logger.debug(f"Supabase response: {response}")

        if response.data:
            original_url = response.data[0].get("original_url")
            if original_url:
                if not original_url.startswith(("http://", "https://")):
                    original_url = "https://" + original_url
                logger.info(f"Redirecting to: {original_url}")
                return RedirectResponse(url=original_url, status_code=302)

        logger.info(f"No match found for path: {path}")
        return RedirectResponse(url="https://www.google.com", status_code=302)

    except Exception as e:
        logger.exception("Error during redirect handling.")
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    uvicorn.run("run:app", host="0.0.0.0", port=80, reload=True)