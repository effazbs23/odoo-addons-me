"""Optional semantic (embedding-based) product-name matcher.

Wraps a small local sentence-embedding model (``fastembed`` /
BAAI/bge-small-en-v1.5 — ONNX runtime, no PyTorch, ~130MB, CPU-only) so a
customer's free-text product description (typos, reworded names, no SKU at
all) can still be matched to the catalog by meaning, not just literal
spelling — which is what plain string-fuzzy matching (``difflib``) misses.

Kept fully optional and side-effect-free at import time: if ``fastembed``
isn't installed, or the model fails to load, every function here returns
``None`` and callers (see ``quick_paste_wizard.py::_match_product``) fall
back to exact/string-fuzzy matching. The module is never required for the
addon to install or function.
"""
from __future__ import annotations

import logging
import os
import threading

from odoo.tools import config

_logger = logging.getLogger(__name__)

MODEL_NAME = 'BAAI/bge-small-en-v1.5'

_model = None
_model_lock = threading.Lock()
_model_unavailable = False


def _cache_dir() -> str:
    # Persisted under Odoo's own data_dir (not /tmp) so the ~130MB model
    # weights survive server restarts/redeploys instead of being
    # re-downloaded from Hugging Face every time.
    return os.path.join(config['data_dir'], 'bs_smart_invoice_import', 'fastembed_cache')


def _get_model():
    global _model, _model_unavailable
    if _model is not None or _model_unavailable:
        return _model
    with _model_lock:
        if _model is not None or _model_unavailable:
            return _model
        try:
            from fastembed import TextEmbedding
        except ImportError:
            _model_unavailable = True
            _logger.info(
                "fastembed not installed; bs_smart_invoice_import will use "
                "string-fuzzy matching only for product names. Run `pip "
                "install fastembed` to enable semantic (typo/synonym "
                "tolerant) matching."
            )
            return None
        try:
            os.makedirs(_cache_dir(), exist_ok=True)
            _model = TextEmbedding(model_name=MODEL_NAME, cache_dir=_cache_dir())
        except Exception:
            _model_unavailable = True
            _logger.warning(
                "Failed to load embedding model %s; bs_smart_invoice_import "
                "will fall back to string-fuzzy matching.", MODEL_NAME,
                exc_info=True,
            )
            return None
    return _model


def is_available() -> bool:
    return _get_model() is not None


def embed(texts):
    """Return a list of embedding vectors (list[float]) for ``texts``, or
    None if the embedding model isn't available."""
    model = _get_model()
    if model is None:
        return None
    return [list(vec) for vec in model.embed(list(texts))]


def cosine_similarity(vec_a, vec_b) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)
