import time
import httpx

# Generate 100 test URLs (mix of valid, invalid, and redirects)
test_urls = [
    # Valid URLs (30)
    "https://google.com",
    "https://github.com",
    "https://httpbin.org/status/200",
    *[f"https://example.com/valid-{i}" for i in range(27)],

    # Redirects (30)
    "http://github.com",  # Redirects to HTTPS
    "http://bit.ly/3sXGJ6h",  # Example short link (replace with valid)
    "https://httpbin.org/redirect/2",
    *[f"https://httpbin.org/redirect/{i}" for i in range(27)],

    # Invalid URLs (40)
    "https://thisdomain.doesnotexist123",
    "https://httpbin.org/status/404",
    "http://localhost:9999",  # Unreachable
    *[f"https://invalid-{i}.com" for i in range(37)]
]

# Test the endpoint
start_time = time.time()
response = httpx.post(
    "http://localhost:8000/",
    json={"urls": test_urls},
    timeout=30
)
duration = time.time() - start_time

print(f"Response Time: {duration:.2f}s")
print(f"Status Code: {response.status_code}")
print("Results Summary:")
results = response.json()["results"]
print(f"Available: {sum(1 for v in results.values() if v == 'available')}")
print(f"Unavailable: {sum(1 for v in results.values() if v == 'unavailable')}")


## Validation Test
print("Running Validaton Test:")
# Generate 150 URLs
too_many_urls = [f"https://example.com/{i}" for i in range(150)]

response = httpx.post(
    "http://localhost:8000/",
    json={"urls": too_many_urls}
)

print(f"Status Code: {response.status_code}")  # Should be 400
print(response.json())  # Expect "Maximum 100 URLs allowed"