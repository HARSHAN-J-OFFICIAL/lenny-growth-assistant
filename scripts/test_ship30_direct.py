import urllib.request
import json
import time

payload = {
    "topic": "Finding Product-Market Fit in B2B SaaS",
    "model_provider": "ollama",
    "model_name": "llama3.2"
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/v1/skills/ship30",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

print("Starting Ship 30 direct backend test...")
t0 = time.time()
try:
    with urllib.request.urlopen(req, timeout=180) as resp:
        elapsed = time.time() - t0
        data = json.loads(resp.read().decode("utf-8"))
        print(f"COMPLETED in {elapsed:.2f}s!")
        print(f"Status: {resp.status}")
        print(f"Headline: {data.get('headline')}")
        print(f"Word Count: {data.get('word_count')}")
        print(f"Guest References: {data.get('guest_references')}")
        print(f"Citations Count: {len(data.get('citations', []))}")
        print(f"Artifacts Count: {len(data.get('artifacts', []))}")
        print("Essay Preview:\n" + data.get("content", "")[:350] + "\n...")
except Exception as e:
    elapsed = time.time() - t0
    print(f"FAILED after {elapsed:.2f}s: {e}")
