import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
import uvicorn
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

def supabase_client() -> Client:
    url: str = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key: str = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    return create_client(url, key)

@app.get("/{path}")
def redirector(path: str):
    supabase: Client = supabase_client()
    try:
        if len(path) >= 6:
            raise HTTPException(status_code=400)
        response = supabase.table("urls").select("*").eq("short", path).execute()
        print(response)
        
        if response.data:
            original_link = response.data[0].get("original_link")
            if original_link:
                # Ensure the URL starts with "http://" or "https://"
                if not original_link.startswith(("http://", "https://")):
                    original_link = "https://" + original_link  
                print(original_link)
                return RedirectResponse(url=original_link, status_code=302)
        
        raise HTTPException(status_code=404, detail="error")
    except Exception as e:
        raise HTTPException(status_code=500, detail="error")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
