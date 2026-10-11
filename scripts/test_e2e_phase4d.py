# -*- coding: utf-8 -*-
"""
Phase 4D - Complete End-to-End Verification Script (Fixed for Windows cp1252)
Tests: Ship 30 essay, Groq Cloud, session persistence, retrieval
"""
import json
import time
import urllib.request
import sys
import os

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

BACKEND = "http://127.0.0.1:8000/api/v1"
PI_AGENT = "http://127.0.0.1:8001"

results = {}
all_passed = True

def test(name, fn):
    global all_passed
    t0 = time.time()
    try:
        ok, detail = fn()
        elapsed = time.time() - t0
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_passed = False
        results[name] = {"status": status, "elapsed": f"{elapsed:.2f}s", "detail": detail}
        print(f"  [{status}] {name} ({elapsed:.2f}s) -- {detail}")
    except Exception as e:
        elapsed = time.time() - t0
        all_passed = False
        results[name] = {"status": "ERROR", "elapsed": f"{elapsed:.2f}s", "detail": str(e)}
        print(f"  [ERROR] {name} ({elapsed:.2f}s) -- {e}")

def http_get(url, timeout=15):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def http_post(url, data, timeout=180):
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"),
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


print("\n=== PHASE 4D END-TO-END VERIFICATION ===\n")

# TEST 1: Backend Health
def test_health():
    d = http_get(f"{BACKEND}/health")
    ok = d.get("status") == "ok" and d.get("database") == "connected"
    return ok, f"status={d.get('status')}, db={d.get('database')}"
test("Backend Health + PostgreSQL", test_health)

# TEST 2: Pi Agent Health
def test_pi_health():
    d = http_get(f"{PI_AGENT}/health")
    ok = d.get("status") == "ok" and "pi-coding-agent" in d.get("sdk", "")
    return ok, f"sdk={d.get('sdk')}, version={d.get('version')}"
test("Pi Agent SDK Health", test_pi_health)

# TEST 3: Providers Status
def test_providers():
    d = http_get(f"{BACKEND}/providers/status")
    providers = {p["id"]: p for p in d.get("providers", [])}
    ollama_ok = providers.get("ollama", {}).get("is_available", False)
    groq_ok = providers.get("groq", {}).get("is_configured", False)
    return ollama_ok and groq_ok, f"ollama_avail={ollama_ok}, groq_configured={groq_ok}"
test("Providers: Ollama + Groq", test_providers)

# TEST 4: Hybrid Retrieval
def test_retrieval():
    d = http_post(f"{BACKEND}/retrieval/search", {"query": "product-led growth Elena Verna", "top_k": 3})
    passages = d.get("passages", [])
    latency = d.get("latency_ms", 0)
    ok = len(passages) >= 1 and latency < 5000
    guests = [p.get("guest", "") for p in passages[:3]]
    return ok, f"passages={len(passages)}, latency={latency}ms, guests={guests}"
test("Hybrid Retrieval Search", test_retrieval)

# TEST 5: Create Session
session_id = None
def test_create_session():
    global session_id
    d = http_post(f"{BACKEND}/sessions", {"title": "Ship 30 E2E Test", "model_provider": "ollama", "model_name": "llama3.2"})
    session_id = d.get("id")
    ok = session_id is not None
    return ok, f"session_id={session_id}"
test("Create Session", test_create_session)

# TEST 6: Ship 30 Essay Generation with Session Persistence
def test_ship30():
    d = http_post(f"{BACKEND}/skills/ship30", {
        "topic": "Finding Product-Market Fit in B2B SaaS",
        "target_audience": "Product Managers & Early Founders",
        "model_provider": "ollama",
        "model_name": "llama3.2",
        "session_id": session_id,
    }, timeout=180)
    headline = d.get("headline", "")
    word_count = d.get("word_count", 0)
    citations = d.get("citations", [])
    artifact_id = d.get("artifact_id")
    ok = word_count >= 500 and len(citations) >= 1
    safe_headline = headline[:60].encode("ascii", errors="replace").decode("ascii")
    return ok, f"headline='{safe_headline}', words={word_count}, citations={len(citations)}, artifact_id={artifact_id}"
test("Ship 30 Essay Generation + Persistence", test_ship30)

# TEST 7: Session History
def test_session_history():
    d = http_get(f"{BACKEND}/sessions/{session_id}/history")
    messages = d.get("messages", [])
    assistant_msgs = [m for m in messages if m.get("role") == "assistant"]
    ok = len(assistant_msgs) >= 1
    detail = f"total_messages={len(messages)}, assistant_msgs={len(assistant_msgs)}"
    if assistant_msgs:
        first_content = assistant_msgs[0].get("content", "")[:60]
        safe_content = first_content.encode("ascii", errors="replace").decode("ascii")
        detail += f", preview='{safe_content}'"
    return ok, detail
test("Session History Persistence", test_session_history)

# TEST 8: Artifacts Persisted
def test_artifacts():
    d = http_get(f"{BACKEND}/sessions/{session_id}/artifacts")
    # Endpoint may return list or dict with artifacts key
    artifacts = d if isinstance(d, list) else d.get("artifacts", [])
    ok = len(artifacts) >= 1
    detail = f"total_artifacts={len(artifacts)}"
    if artifacts:
        first = artifacts[0] if isinstance(artifacts[0], dict) else {}
        title = first.get("title", "")[:50]
        safe_title = title.encode("ascii", errors="replace").decode("ascii")
        detail += f", title='{safe_title}', type={first.get('artifact_type')}"
    return ok, detail
test("Artifact PostgreSQL Persistence", test_artifacts)

# TEST 9: Groq Cloud Live via Pi Agent SDK
def test_groq_pi():
    d = http_post(f"{PI_AGENT}/chat", {
        "message": "What did Brian Chesky say about founder mode?",
        "model_provider": "groq",
        "model_name": "openai/gpt-oss-20b",
    }, timeout=30)
    content = d.get("content", "")
    citations = d.get("citations", [])
    provider = d.get("provider", "")
    ok = provider == "groq" and len(citations) >= 1
    return ok, f"provider={provider}, content_len={len(content)}, citations={len(citations)}"
test("Groq Cloud via Pi Agent SDK (Live)", test_groq_pi)

# TEST 10: Chat RAG (Ollama)
def test_chat_rag():
    d = http_post(f"{BACKEND}/chat", {
        "message": "How does Shreyas Doshi define high-agency product managers?",
        "session_id": session_id,
        "model_provider": "ollama",
        "model_name": "llama3.2",
    }, timeout=120)
    content = d.get("content", "")
    citations = d.get("citations", [])
    ok = len(content) > 50 and len(citations) >= 1
    return ok, f"content_len={len(content)}, citations={len(citations)}"
test("Chat RAG Completion (Ollama)", test_chat_rag)

# TEST 11: Cleanup
def test_cleanup():
    req = urllib.request.Request(f"{BACKEND}/sessions/{session_id}", method="DELETE")
    with urllib.request.urlopen(req, timeout=10) as r:
        body = r.read().decode("utf-8")
        if body.strip():
            d = json.loads(body)
            ok = d.get("deleted", False)
        else:
            ok = r.status in (200, 204)
    return ok, f"deleted=True (status={r.status})"
test("Session Cleanup", test_cleanup)


# SUMMARY
print("\n" + "=" * 60)
passed = sum(1 for r in results.values() if r["status"] == "PASS")
failed = sum(1 for r in results.values() if r["status"] != "PASS")
print(f"RESULTS: {passed}/{len(results)} passed, {failed} failed")

if all_passed:
    print("STATUS: ALL TESTS PASSED")
else:
    print("STATUS: SOME TESTS FAILED")
    for name, r in results.items():
        if r["status"] != "PASS":
            safe_detail = r["detail"].encode("ascii", errors="replace").decode("ascii")
            print(f"  FAILED: {name} -- {safe_detail}")

sys.exit(0 if all_passed else 1)
