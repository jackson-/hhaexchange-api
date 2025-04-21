# Website Availability Checker Server

A high-performance web service for checking website availability statuses. Built with FastAPI and designed for efficient, concurrent processing of URL checks while maintaining responsible server behavior.

## Features

- **Concurrent Processing**: Checks up to 100 URLs simultaneously
- **Validation**: Enforces maximum 100 URLs per request
- **Error Resilience**: Gracefully handles network errors and timeouts
- **Security**: Includes timeout protection and user-agent identification
- **Efficiency**: Uses HEAD requests to minimize bandwidth usage

## Installation

```bash
pip install -r requirements.txt
```

## Start Server
```bash
uvicorn main:app --reload
```

## Sample Request
```bash
curl -X POST "http://localhost:8000/" \
-H "Content-Type: application/json" \
-d '{"urls": ["https://google.com", "https://nonexistent.website"]}'
```

## Sample Response
```json
{
  "results": {
    "https://google.com": "available",
    "https://nonexistent.website": "unavailable"
  }
}
```

## Testing
`python test.py` for quick tests
`pytest -v -s --asyncio-mode=auto test_main.py` for unit tests

## Limits and Trade-offs
1. Concurrency limit is fixed at 100 and may need adjustment based on server resources
2. 5 second timeout might be too short for some international sites
3. There is no retry logic and transient errors marked as unavailable
4. There is potential for false negatives as some sites may block HEAD requests

## Possible solution for transient errors
We can implement configurable retry logic to make sure that it is actually unavailable if it falls within
a certain list of temporary error codes like 429 and 503. For now, I've left this out because one of the
requirements was to think about how I could lower the response time for this endpoint.
```python
async def check_availability(url, retries=2):
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.head(url, follow_redirects=True)
                if response.status_code < 400:
                    return {url: "available"}
                elif response.status_code in (429, 503):  # Retry on these
                    await asyncio.sleep(1)  # Backoff
                    continue
                else:
                    return {url: "unavailable"}
        except (httpx.RequestError, httpx.HTTPError):
            if attempt == retries - 1:  # Final attempt failed
                return {url: "unavailable"}
            await asyncio.sleep(1)  # Wait before retry
    return {url: "unavailable"}
```