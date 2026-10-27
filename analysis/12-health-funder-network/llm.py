"""Ask the local open-weight model, and remember every answer.

Each answer goes into llm_cache/<task>.jsonl (committed with the code), keyed by a hash of the exact prompt, so a rerun
replays the same answers without the model. Only prompts with no cached answer reach the model. The model runs in
Ollama; set OLLAMA_URL if it is not at http://127.0.0.1:11435 (see README for starting it on the integrated GPU).

Temperature 0 and a fixed seed keep answers stable, but the model is not bit-for-bit deterministic when requests are
batched, which is why the cache, not the model, is the record.
"""
import hashlib
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

MODEL = "gpt-oss:20b"
URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11435")
CACHE = Path(__file__).parent / "llm_cache"
PARALLEL = 4
OPTIONS = {"temperature": 0, "seed": 1, "num_ctx": 2048}  # prompts are under 1,000 tokens
_lock = threading.Lock()


def key_of(prompt):
    return hashlib.sha256(prompt.encode()).hexdigest()[:20]


def model_digest():
    tags = requests.get(f"{URL}/api/tags", timeout=30).json()["models"]
    return next(m["digest"][:12] for m in tags if m["name"] == MODEL)


def load(task):
    f = CACHE / f"{task}.jsonl"
    if not f.exists():
        return {}
    return {r["key"]: r for r in map(json.loads, f.read_text().splitlines())}


def _ask(prompt, schema):
    r = requests.post(f"{URL}/api/chat", timeout=600, json={
        "model": MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False,
        "format": schema, "think": "low", "options": OPTIONS})
    r.raise_for_status()
    return json.loads(r.json()["message"]["content"])


def ask_many(task, prompts, schema, progress=500):
    """prompts: {id: prompt}. Returns {id: answer dict}; answers already in the cache are not asked again."""
    CACHE.mkdir(exist_ok=True)
    cache = load(task)
    keys = {i: key_of(p) for i, p in prompts.items()}
    todo = {k: prompts[i] for i, k in keys.items() if k not in cache}
    if todo:
        digest = model_digest()
        print(f"  {task}: asking the model {len(todo):,} new prompts ({len(cache):,} cached)", flush=True)
        f = open(CACHE / f"{task}.jsonl", "a")
        done = 0

        def one(item):
            nonlocal done
            k, p = item
            ans = _ask(p, schema)
            row = {"key": k, "model": MODEL, "digest": digest, "answer": ans}
            with _lock:
                f.write(json.dumps(row, separators=(",", ":")) + "\n")
                f.flush()
                os.fsync(f.fileno())  # an answer on disk survives a power cut
                cache[k] = row
                done += 1
                if done % progress == 0:
                    print(f"    {done:,} / {len(todo):,}", flush=True)

        with ThreadPoolExecutor(PARALLEL) as ex:
            list(ex.map(one, todo.items()))
        f.close()
    return {i: cache[k]["answer"] for i, k in keys.items()}
