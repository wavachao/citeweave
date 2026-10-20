import hashlib
import logging
import os
import secrets
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import config
from .cache import AnswerCache
from .engine import Engine
from .resources import gpu_session
from .security import RequestLimiter, authorized, denied
from .web import retrieve

app = FastAPI(title="CiteWeave", version="0.1.0")
logger = logging.getLogger("citeweave")
engine = Engine()
request_lock = threading.Lock()
limiter = RequestLimiter(limit=config.RATE_LIMIT)
answer_cache = AnswerCache(config.DATA / "cache/answers.sqlite3", ttl=config.CACHE_TTL)
static = Path(__file__).parent / "static"
runtime_fingerprint = hashlib.sha256(
    b"".join(p.read_bytes() for p in sorted(Path(__file__).parent.glob("*.py")))
).hexdigest()
images_dir = config.DATA / "images"
images_dir.mkdir(parents=True, exist_ok=True)
cache_dir = config.DATA / "cache/images"
cache_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=images_dir), name="media")
app.mount("/cache", StaticFiles(directory=cache_dir), name="cache")
app.mount("/static", StaticFiles(directory=static), name="static")


@app.middleware("http")
async def admission(request: Request, call_next):
    request_id = secrets.token_hex(8)
    request.state.request_id = request_id
    protected = request.url.path.startswith(("/api/search", "/cache/", "/media/"))
    if protected and not authorized(request):
        return denied("Access token required. Connect this workspace to continue.")
    if request.method == "POST":
        if not request.headers.get("content-type", "").startswith("application/json"):
            return denied("Expected application/json", 415)
        if len(await request.body()) > 16384:
            return denied("Request body exceeds 16 KiB", 413)
        if not limiter.allow(request.client.host):
            return JSONResponse(
                {"detail": "Too many requests. Please try again in one minute."},
                status_code=429,
                headers={"Retry-After": "60"},
            )
    response = await call_next(request)
    response.headers.update(
        {
            "X-Request-ID": request_id,
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
            "X-Frame-Options": "DENY",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; "
            "font-src 'self'; img-src 'self' https: http: data:; connect-src 'self'; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'none'",
        }
    )
    if request.url.path.startswith(("/api/", "/cache/", "/media/")):
        response.headers["Cache-Control"] = "no-store"
    return response


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=3000)
    urls: list[str] = Field(default_factory=list, max_length=5)
    verify_images: bool = True
    refresh: bool = False


class SessionRequest(BaseModel):
    token: str = Field(min_length=1, max_length=256)


@app.post("/api/session")
def session(request: Request, body: SessionRequest):
    if not config.ACCESS_TOKEN or not secrets.compare_digest(
        body.token.encode(), config.ACCESS_TOKEN.encode()
    ):
        raise HTTPException(401, "Invalid access token")
    response = JSONResponse({"connected": True})
    response.set_cookie(
        "citeweave_session",
        body.token,
        httponly=True,
        samesite="strict",
        secure=request.url.scheme == "https",
        max_age=8 * 60 * 60,
    )
    return response


@app.delete("/api/session")
def disconnect():
    response = JSONResponse({"connected": False})
    response.delete_cookie("citeweave_session")
    return response


def browser_answer(answer, mode):
    preview_images = [s["preview_image"] for s in answer["sources"] if s.get("preview_image")]
    for image in answer["images"] + preview_images:
        relative = urlparse(image.get("cached_image_url", "")).path.lstrip("/")
        if relative and (images_dir / relative).is_file():
            image["render_url"] = "/media/" + relative
        elif image.get("local_path") and Path(image["local_path"]).is_file():
            image["render_url"] = "/cache/" + Path(image["local_path"]).name
        else:
            image["render_url"] = image["url"]
        image.pop("local_path", None)
        image.pop("cached_image_url", None)
    answer.pop("raw_response", None)
    answer["mode"] = mode
    return answer


@app.get("/")
def home():
    return FileResponse(static / "index.html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "backend": os.getenv("CITEWEAVE_BACKEND", "local"),
        "local_model_ready": (Path(config.MODEL) / "model.safetensors.index.json").exists(),
        "trained_ranker_ready": (config.RUNS / "crossencoder/selected.json").exists()
        or config.RANKER.exists(),
    }


@app.get("/api/status")
def status(request: Request):
    return {
        "authentication_enabled": bool(config.ACCESS_TOKEN),
        "authentication_required": not authorized(request),
        "backend": os.getenv("CITEWEAVE_BACKEND", "local"),
    }


@app.get("/ready")
def ready():
    paths = [Path(config.EMBEDDING_MODEL), Path(config.VISION_MODEL)]
    if os.getenv("CITEWEAVE_BACKEND", "local") == "local":
        paths.append(Path(config.MODEL))
    available = all((p / "config.json").is_file() for p in paths)
    return JSONResponse({"ready": available}, status_code=200 if available else 503)


def cache_parameters(request):
    resources = []
    for path in (
        Path(config.MODEL) / "source.json",
        Path(config.VISION_MODEL) / "source.json",
        Path(config.EMBEDDING_MODEL) / "source.json",
        config.RUNS / "crossencoder/selected.json",
        config.RUNS / "crossencoder/best/model.safetensors",
        config.RANKER,
    ):
        if path.is_file():
            stat = path.stat()
            resources.append((str(path), stat.st_size, stat.st_mtime_ns))
    return {
        "query": request.query,
        "urls": request.urls,
        "verify_images": request.verify_images,
        "implementation": runtime_fingerprint,
        "resources": resources,
        "backend": os.getenv("CITEWEAVE_BACKEND", "local"),
        "api_model": os.getenv("CITEWEAVE_API_MODEL", "deepseek-flash"),
        "api_base": os.getenv("CITEWEAVE_API_BASE", "https://api.deepseek.com"),
        "search": os.getenv("SEARXNG_URL", ""),
        "budgets": [config.MAX_INPUT, config.MAX_NEW, config.MAX_IMAGES],
    }


@app.post("/api/search")
def ask(request: SearchRequest, http_request: Request):
    started = time.monotonic()
    key = answer_cache.key(cache_parameters(request))
    cached = answer_cache.get(key) if not request.refresh else None
    if cached:
        cached.update(cache_hit=True, total_seconds=round(time.monotonic() - started, 2))
        return browser_answer(cached, "live_web")
    if not request_lock.acquire(blocking=False):
        raise HTTPException(
            409,
            "A search is already running. Please retry when it finishes.",
            headers={"Retry-After": "10"},
        )
    try:
        with gpu_session(blocking=False):
            try:
                retrieval_query = request.query
                if any(ord(c) > 127 for c in request.query):
                    translation = engine.generator.complete(
                        "Translate this search question to English. Preserve names, numbers and formulas. "
                        "Output only the translated question, do not answer it:\n" + request.query
                    )
                    retrieval_query = translation["response"].strip()
                sources, images, errors = retrieve(retrieval_query, request.urls)
                if request.verify_images and images:
                    from .vision import caption_images

                    candidates = engine.ranker.select(retrieval_query, images, limit=8)
                    if not candidates:
                        candidates = images[:8]
                    images = caption_images(candidates, engine.generator, limit=8)
                answer = engine.answer(
                    request.query, sources, images, retrieval_query=retrieval_query
                )
                answer["retrieval_errors"] = errors
                answer["total_seconds"] = round(time.monotonic() - started, 2)
                answer["created_at"] = time.time()
                answer["cache_hit"] = False
                answer_cache.put(key, answer)
                return browser_answer(answer, "live_web")
            finally:
                engine.generator.unload()
                engine.ranker.unload()
    except BlockingIOError as e:
        raise HTTPException(
            409, "The compute worker is busy. Please retry shortly.", headers={"Retry-After": "10"}
        ) from e
    except Exception as e:
        logger.exception("Search failed; request_id=%s", http_request.state.request_id)
        raise HTTPException(
            503,
            "Search could not be completed. Try another question or specify a public source URL.",
        ) from e
    finally:
        request_lock.release()
