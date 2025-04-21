from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import asyncio
from typing import List, Dict

app = FastAPI()

# Define semaphore at the module level
semaphore = asyncio.Semaphore(100)

class UrlRequest(BaseModel):
    urls: List[str]

async def check_availability(url: str) -> Dict[str, str]:
    """
    Check if a website is available by making an HTTP HEAD request.
    Considered available if returns 2xx/3xx status code within 5 seconds.
    """
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.head(
                url,
                follow_redirects=True,
                headers={"User-Agent": "AvailabilityChecker/1.0"}
            )
            status = "available" if response.status_code < 400 else "unavailable"
    except (httpx.RequestError, httpx.HTTPError):
        status = "unavailable"
    
    return {url: status}

@app.post("/")
async def check_urls(request: UrlRequest) -> Dict[str, Dict[str, str]]:
    """
    Endpoint to check website availability. 
    Processes up to 100 URLs concurrently.
    """
    if not request.urls:
        raise HTTPException(status_code=400, detail="No URLs provided")
    
    if len(request.urls) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 URLs allowed")

    # Process URLs concurrently with semaphore to limit simultaneous connections
    async def limited_check(url):
        async with semaphore:
            return await check_availability(url)

    tasks = [limited_check(url) for url in request.urls]
    results = await asyncio.gather(*tasks)
    
    return {"results": {k: v for res in results for k, v in res.items()}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)