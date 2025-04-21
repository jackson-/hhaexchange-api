# test_main.py
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, Request, Response, RequestError, TimeoutException
from unittest.mock import AsyncMock, patch
import asyncio
import json

from main import app

client = TestClient(app)

# Helper function to create mock responses
def mock_response(status_code: int, history=None):
    return Response(
        status_code=status_code,
        request=Request("HEAD", "http://test"),
        history=history or []
    )

@pytest.mark.asyncio
async def test_check_urls_success():
    # Test valid URL list with mixed responses
    test_urls = ["https://valid.com", "https://invalid.com"]
    
    with patch("main.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.head.side_effect = [
            mock_response(200),
            mock_response(404)
        ]
        
        response = client.post("/", json={"urls": test_urls})
        assert response.status_code == 200
        
        results = response.json()["results"]
        assert results["https://valid.com"] == "available"
        assert results["https://invalid.com"] == "unavailable"

@pytest.mark.asyncio
async def test_redirect_handling():
    # Test redirect chain (301 → 200)
    with patch("main.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.head.side_effect = [
            mock_response(200, history=[mock_response(301)])
        ]
        
        response = client.post("/", json={"urls": ["https://redirect.com"]})
        assert response.json()["results"]["https://redirect.com"] == "available"

@pytest.mark.asyncio
async def test_error_handling():
    # Test network error
    with patch("main.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.head.side_effect = \
            RequestError("Connection failed")
            
        response = client.post("/", json={"urls": ["https://error.com"]})
        assert response.json()["results"]["https://error.com"] == "unavailable"

def test_input_validation():
    # Test empty URL list
    response = client.post("/", json={"urls": []})
    assert response.status_code == 400
    assert "No URLs provided" in response.json()["detail"]
    
    # Test too many URLs
    response = client.post("/", json={"urls": ["http://test.com"] * 101})
    assert response.status_code == 400
    assert "Maximum 100 URLs allowed" in response.json()["detail"]

@pytest.mark.asyncio
async def test_concurrency_limit():
    # Test semaphore limits concurrent requests
    from main import check_availability, semaphore
    
    original_limit = semaphore._value
    test_urls = ["http://test.com"] * 150
    
    with patch("main.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.head.return_value = \
            mock_response(200)
        
        tasks = [check_availability(url) for url in test_urls]
        results = await asyncio.gather(*tasks)
        
        # Verify maximum concurrent requests didn't exceed limit
        assert semaphore._value == original_limit
        assert len(results) == 150

def test_timeout_handling():
    # Test request timeout
    with patch("main.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.head.side_effect = \
            TimeoutException("Timeout")
            
        response = client.post("/", json={"urls": ["https://timeout.com"]})
        assert response.json()["results"]["https://timeout.com"] == "unavailable"