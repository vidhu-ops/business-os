"""
IIDATECH Learning Engine v4.1
──────────────────────────────
Persistent memory + continuous self-updating intelligence layer.

Architecture:
  ┌─────────────────────────────────────────────┐
  │  Live Feed Harvester  (RSS + Exa + Tavily)  │
  │  ↓                                          │
  │  ChromaDB Vector Store  (local, on-disk)    │
  │  ↓                                          │
  │  Context Injector  (RAG into synthesis)     │
  │  ↓                                          │
  │  Self-Eval Loop  (grade → store feedback)   │
  └─────────────────────────────────────────────┘
"""

import json
import os
import time
import hashlib
import logging
import threading
import requests
import feedparser
import chromadb
from chroma_config import chroma_db_path
from datetime import datetime, timezone
from pathlib import Path
from iidatech.retrieval.embedding import embed_text
from apscheduler.schedulers.background import BackgroundScheduler

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [LEARN] %(message)s")
log = logging.getLogger("iidatech.learning")

APP_DIR = Path(__file__).resolve().parent
PRODUCTION_ENV_CANDIDATES = (
    APP_DIR / "research_upload" / "research_llm_production" / ".env",
    APP_DIR.parent / "research_upload" / "research_llm_production" / ".env",
)


def read_env_value(name: str) -> str:
    """Read a value from environment, Streamlit secrets, or local project .env files."""
    if os.getenv(name):
        return os.getenv(name, "").strip()
    try:
        import streamlit as st

        value = st.secrets.get(name, "")
        if value:
            return str(value).strip()
    except Exception:
        pass
    for env_path in (APP_DIR / ".env", *PRODUCTION_ENV_CANDIDATES):
        if not env_path.exists():
            continue
        try:
            for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                if key.strip() == name:
                    return value.strip().strip('"').strip("'")
        except OSError:
            continue
    return ""

# Updated keys — old keys removed
DEEPSEEK_KEY = read_env_value("DEEPSEEK_KEY") or read_env_value("DEEPSEEK_API_KEY")
EXA_KEY = read_env_value("EXA_KEY") or read_env_value("EXA_API_KEY")

# Live RSS feeds — auto-refresh every 30 min
LIVE_FEEDS = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://techcrunch.com/feed/",
    "https://feeds.feedburner.com/venturebeat/SZYF",
    "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "https://www.moneycontrol.com/rss/MCtopnews.xml",
    "https://inc42.com/feed/",
    "https://yourstory.com/feed",
    "https://www.business-standard.com/rss/markets-106.rss",
    "https://www.livemint.com/rss/markets",
]

# ─────────────────────────────────────────────
# CORE LEARNING ENGINE
# ─────────────────────────────────────────────
class LearningEngine:

    def __init__(self):
        self._client    = chromadb.PersistentClient(path=str(chroma_db_path()))
        self._col       = self._client.get_or_create_collection(
            name="iidatech_knowledge",
            metadata={"hnsw:space": "cosine"},
        )
        self._scheduler = None
        self._lock      = threading.Lock()
        log.info(f"ChromaDB loaded — {self._col.count()} documents in memory")

    # ── RAG: retrieve relevant context ───────────────────────────────────────
    def get_context(self, query: str, top_k: int = 5) -> str:
        if self._col.count() == 0:
            return ""
        try:
            n = min(top_k, self._col.count())
            results = self._col.query(
                query_embeddings=[embed_text(query)],
                n_results=n,
                include=["documents", "metadatas"],
            )
            chunks = []
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                source = meta.get("source", "unknown")
                ts     = meta.get("timestamp", "")[:19]
                chunks.append(f"[{source} | {ts}]\n{doc}")
            return "\n\n---\n\n".join(chunks)
        except Exception as e:
            log.warning(f"Context retrieval failed: {e}")
            return ""

    # ── Store completed report sections ──────────────────────────────────────
    def store_report_memory(self, report: dict, industry: str, target: str):
        ts   = datetime.now(timezone.utc).isoformat()
        docs, ids, metas, embeds = [], [], [], []
        for sec_id, content in report.items():
            text = content if isinstance(content, str) else json.dumps(content)[:3000]
            uid  = hashlib.md5(f"{industry}_{target}_{sec_id}_{ts}".encode()).hexdigest()
            docs.append(text)
            ids.append(uid)
            metas.append({
                "source":    "self_report",
                "industry":  industry,
                "target":    target,
                "section":   str(sec_id),
                "timestamp": ts,
            })
            embeds.append(embed_text(text))
        with self._lock:
            self._col.upsert(documents=docs, ids=ids, metadatas=metas, embeddings=embeds)
        log.info(f"Stored {len(docs)} report sections [{industry} / {target}]")

    # ── Manual text ingestion ─────────────────────────────────────────────────
    def ingest_text(self, text: str, source: str = "manual", metadata: dict = None) -> str:
        meta = metadata or {}
        meta.update({"source": source, "timestamp": datetime.now(timezone.utc).isoformat()})
        uid = hashlib.md5(f"{source}_{text[:200]}".encode()).hexdigest()
        with self._lock:
            self._col.upsert(
                documents=[text[:8000]],
                ids=[uid],
                metadatas=[meta],
                embeddings=[embed_text(text)],
            )
        log.info(f"Ingested text from [{source}] — {len(text)} chars")
        return uid

    # ── RSS harvest ───────────────────────────────────────────────────────────
    def harvest_live_feeds(self):
        log.info("🌐 Harvesting live RSS feeds…")
        new_count = 0
        for url in LIVE_FEEDS:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:5]:
                    title   = entry.get("title", "")
                    summary = entry.get("summary", entry.get("description", ""))
                    link    = entry.get("link", url)
                    text    = f"{title}\n\n{summary}"
                    if len(text) < 50:
                        continue
                    uid = hashlib.md5(link.encode()).hexdigest()
                    try:
                        existing = self._col.get(ids=[uid])
                        if existing["ids"]:
                            continue
                    except Exception:
                        pass
                    with self._lock:
                        self._col.upsert(
                            documents=[text[:4000]],
                            ids=[uid],
                            metadatas=[{
                                "source":    feed.feed.get("title", url)[:80],
                                "link":      link,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "type":      "live_feed",
                            }],
                            embeddings=[embed_text(text)],
                        )
                    new_count += 1
            except Exception as e:
                log.warning(f"Feed failed [{url}]: {e}")
        log.info(f"✅ Harvest done — {new_count} new articles (total: {self._col.count()})")

    # ── Exa deep topic learning ───────────────────────────────────────────────
    def deep_learn_topic(self, topic: str, num_results: int = 10) -> int:
        log.info(f"🔬 Deep learning: {topic}")
        if not EXA_KEY:
            log.info("Exa deep learning skipped because EXA_API_KEY is not configured.")
            return 0
        try:
            res = requests.post(
                "https://api.exa.ai/search",
                headers={"x-api-key": EXA_KEY, "Content-Type": "application/json"},
                json={
                    "query":         topic,
                    "numResults":    num_results,
                    "useAutoprompt": True,
                    "contents":      {"text": True},
                },
                timeout=30,
            )
            if res.status_code != 200:
                log.warning(f"Exa deep learn failed: {res.status_code}")
                return 0
            stored = 0
            for item in res.json().get("results", []):
                text  = item.get("text", item.get("title", ""))
                url   = item.get("url", "")
                title = item.get("title", "")
                if not text or len(text) < 100:
                    continue
                uid = hashlib.md5(url.encode()).hexdigest()
                with self._lock:
                    self._col.upsert(
                        documents=[f"{title}\n\n{text[:6000]}"],
                        ids=[uid],
                        metadatas=[{
                            "source":    "exa_deep_learn",
                            "topic":     topic,
                            "url":       url,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "type":      "deep_research",
                        }],
                        embeddings=[embed_text(text)],
                    )
                stored += 1
            log.info(f"✅ Deep learned {stored} articles on [{topic}]")
            return stored
        except Exception as e:
            log.error(f"Deep learn error: {e}")
            return 0

    # ── Self-evaluation ───────────────────────────────────────────────────────
    def self_evaluate_and_improve(self, section_output: str, section_title: str) -> dict:
        if not DEEPSEEK_KEY:
            return {"overall_score": None, "weaknesses": ["Self-evaluation skipped because DEEPSEEK_API_KEY is not configured."]}
        prompt = f"""You are a PhD research quality controller.

Section: {section_title}
Output (first 3000 chars):
{section_output[:3000]}

Grade on:
1. Data specificity (real numbers cited?)
2. Source diversity (multiple data points?)
3. Analytical depth (beyond surface observations?)
4. Actionability (concrete recommendations?)

Respond ONLY with this JSON object:
{{
  "overall_score": <0-10>,
  "data_specificity": <0-10>,
  "analytical_depth": <0-10>,
  "actionability": <0-10>,
  "weaknesses": ["...", "..."],
  "improvement_prompt_additions": "Instructions to improve future outputs: ..."
}}"""
        try:
            r = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_KEY}",
                    "Content-Type":  "application/json",
                },
                json={
                    "model":           "deepseek-chat",
                    "messages":        [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature":     0.1,
                    "max_tokens":      512,
                },
                timeout=60,
            )
            if r.status_code == 200:
                result = json.loads(r.json()['choices'][0]['message']['content'])
                self.ingest_text(
                    text=f"Quality feedback for {section_title}:\n{json.dumps(result)}",
                    source="self_eval",
                    metadata={"type": "training_signal", "section": section_title},
                )
                return result
            return {"overall_score": None, "weaknesses": ["Self-evaluation service unavailable."]}
        except Exception as e:
            log.warning(f"Self-eval failed: {e}")
            return {"overall_score": None, "weaknesses": ["Self-evaluation service unavailable."]}

    # ── Background scheduler ──────────────────────────────────────────────────
    def start_background_updater(self, feed_interval_minutes: int = 30):
        if self._scheduler and self._scheduler.running:
            return
        self._scheduler = BackgroundScheduler(daemon=True)
        self._scheduler.add_job(
            self.harvest_live_feeds,
            trigger="interval",
            minutes=feed_interval_minutes,
            id="live_feed_harvest",
            next_run_time=datetime.now(timezone.utc),
        )
        self._scheduler.start()
        log.info(f"✅ Background updater started — refreshes every {feed_interval_minutes} min")

    def stop_background_updater(self):
        if self._scheduler and self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    # ── Stats ─────────────────────────────────────────────────────────────────
    def get_stats(self) -> dict:
        total = self._col.count()
        try:
            all_meta = self._col.get(include=["metadatas"])["metadatas"]
            by_source = {}
            for m in all_meta:
                src = m.get("source", "unknown")
                by_source[src] = by_source.get(src, 0) + 1
            latest = max((m.get("timestamp", "") for m in all_meta), default="never")
        except Exception:
            by_source = {}
            latest    = "unknown"
        return {
            "total_documents": total,
            "by_source":       by_source,
            "latest_update":   latest,
            "db_path":         str(chroma_db_path()),
        }

    # ── Clear ─────────────────────────────────────────────────────────────────
    def clear_memory(self):
        self._client.delete_collection("iidatech_knowledge")
        self._col = self._client.get_or_create_collection(
            name="iidatech_knowledge",
            metadata={"hnsw:space": "cosine"},
        )
        log.info("⚠️ Memory cleared")
