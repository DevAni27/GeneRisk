import base64
import io

import httpx
import numpy as np
import asyncio
import hashlib

from app.config import (
    EVO2_BASE_URL,
    EVO2_MODEL,
    EVO2_CACHE_MAXSIZE,
    EVO2_CACHE_TTL_SECONDS,
    NVIDIA_API_KEY,
)

from cachetools import TTLCache

from app.config import (
    EVO2_BASE_URL,
    EVO2_MODEL,
    NVIDIA_API_KEY,
)


class Evo2ServiceError(Exception):
    """Raised when Evo2 inference fails."""
    
# ---------------------------------------------------------
# Evo2 in-memory score cache
# ---------------------------------------------------------

_score_cache: TTLCache[str, float] = TTLCache(
    maxsize=EVO2_CACHE_MAXSIZE,
    ttl=EVO2_CACHE_TTL_SECONDS,
)

_cache_lock = asyncio.Lock()

_cache_hits = 0
_cache_misses = 0

def build_score_cache_key(
    sequence: str,
) -> str:
    """
    Build a stable cache key for an Evo2 sequence score.

    Model name is included so scores from different Evo2
    models can never accidentally share the same cache entry.
    """

    sequence = validate_dna_sequence(
        sequence
    )

    sequence_hash = hashlib.sha256(
        sequence.encode("ascii")
    ).hexdigest()

    return (
        f"{EVO2_MODEL}:"
        f"mean-loglik-v1:"
        f"{sequence_hash}"
    )


def validate_dna_sequence(sequence: str) -> str:
    """
    Normalize and validate a DNA sequence before sending it to Evo2.
    """

    sequence = "".join(sequence.split()).upper()

    if not sequence:
        raise ValueError("DNA sequence cannot be empty.")

    valid_bases = set("ACGTN")

    invalid_bases = set(sequence) - valid_bases

    if invalid_bases:
        raise ValueError(
            f"Invalid DNA bases found: {sorted(invalid_bases)}"
        )

    return sequence


async def forward_sequence(
    sequence: str,
) -> dict:
    """
    Run an Evo2 forward pass through NVIDIA's hosted API
    and return the raw model response containing final logits.
    """

    if not NVIDIA_API_KEY:
        raise Evo2ServiceError(
            "NVIDIA_API_KEY is not configured."
        )

    sequence = validate_dna_sequence(sequence)

    url = (
        f"{EVO2_BASE_URL}/"
        f"{EVO2_MODEL}/forward"
    )

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "sequence": sequence,
        "output_layers": [
            "unembed",
        ],
    }

    try:
        async with httpx.AsyncClient(
            timeout=120.0,
        ) as client:

            response = await client.post(
                url,
                headers=headers,
                json=payload,
            )

    except httpx.TimeoutException as exc:
        raise Evo2ServiceError(
            "Evo2 request timed out."
        ) from exc

    except httpx.RequestError as exc:
        raise Evo2ServiceError(
            f"Could not connect to Evo2: {exc}"
        ) from exc

    if response.status_code != 200:
        raise Evo2ServiceError(
            (
                f"Evo2 returned HTTP "
                f"{response.status_code}: "
                f"{response.text[:500]}"
            )
        )

    try:
        return response.json()

    except ValueError as exc:
        raise Evo2ServiceError(
            "Evo2 returned a non-JSON response."
        ) from exc
        
def decode_logits(response: dict) -> np.ndarray:
    """
    Decode the base64-encoded NumPy NPZ returned by NVIDIA Evo2.

    Expected tensor:
        unembed.output

    Expected shape:
        (batch, sequence_length, 512)
    """

    encoded_data = response.get("data")

    if not encoded_data:
        raise Evo2ServiceError(
            "Evo2 response does not contain 'data'."
        )

    try:
        binary_data = base64.b64decode(encoded_data)

        with np.load(
            io.BytesIO(binary_data),
            allow_pickle=False,
        ) as arrays:

            if "unembed.output" not in arrays:
                raise Evo2ServiceError(
                    (
                        "Evo2 response does not contain "
                        "'unembed.output'. "
                        f"Available arrays: {list(arrays.keys())}"
                    )
                )

            logits = arrays["unembed.output"].copy()

    except Evo2ServiceError:
        raise

    except Exception as exc:
        raise Evo2ServiceError(
            f"Could not decode Evo2 logits: {exc}"
        ) from exc

    if logits.ndim != 3:
        raise Evo2ServiceError(
            (
                "Unexpected Evo2 logits shape: "
                f"{logits.shape}. "
                "Expected (batch, sequence_length, vocabulary)."
            )
        )

    return logits
  
def compute_log_likelihood(
    sequence: str,
    logits: np.ndarray,
) -> float:
    """
    Compute autoregressive sequence log-likelihood.

    Evo2 logits at position i predict the nucleotide
    at position i + 1.

    DNA bases use their ASCII values as vocabulary indices:
        A -> 65
        C -> 67
        G -> 71
        T -> 84
    """

    sequence = validate_dna_sequence(sequence)

    if logits.ndim == 3:
        logits = logits[0]

    if logits.ndim != 2:
        raise Evo2ServiceError(
            (
                "Expected logits with shape "
                "(sequence_length, vocabulary), "
                f"got {logits.shape}."
            )
        )

    n = min(
        len(sequence),
        logits.shape[0],
    )

    if n < 2:
        return 0.0

    # logits[i] predicts sequence[i + 1]
    prediction_logits = logits[: n - 1]

    # Numerically stable log-softmax denominator:
    #
    # log(sum(exp(x)))
    #
    max_logits = np.max(
        prediction_logits,
        axis=1,
        keepdims=True,
    )

    log_normalizer = (
        max_logits[:, 0]
        + np.log(
            np.exp(
                prediction_logits - max_logits
            ).sum(axis=1)
        )
    )

    # Evo2 uses byte-level token IDs.
    next_token_ids = np.frombuffer(
        sequence[1:n].encode("ascii"),
        dtype=np.uint8,
    )

    chosen_logits = prediction_logits[
        np.arange(n - 1),
        next_token_ids,
    ]

    token_log_probs = (
        chosen_logits
        - log_normalizer
    )

    return float(
        np.mean(token_log_probs)
    )
    
async def score_sequence(
    sequence: str,
) -> float:
    """
    Return Evo2 mean log-likelihood for a DNA sequence.

    Scores are cached in memory so repeated sequences do
    not trigger additional NVIDIA inference requests.
    """

    global _cache_hits
    global _cache_misses

    sequence = validate_dna_sequence(
        sequence
    )

    cache_key = build_score_cache_key(
        sequence
    )

    # -------------------------------------------------
    # 1. Check cache
    # -------------------------------------------------

    async with _cache_lock:

        cached_score = _score_cache.get(
            cache_key
        )

        if cached_score is not None:

            _cache_hits += 1

            print(
                "[Evo2 cache HIT]",
                cache_key[:35] + "...",
            )

            return cached_score

        _cache_misses += 1

    # -------------------------------------------------
    # 2. Cache miss -> call NVIDIA Evo2
    # -------------------------------------------------

    print(
        "[Evo2 cache MISS]",
        cache_key[:35] + "...",
    )

    response = await forward_sequence(
        sequence
    )

    logits = decode_logits(
        response
    )

    score = compute_log_likelihood(
        sequence=sequence,
        logits=logits,
    )

    # -------------------------------------------------
    # 3. Save score
    # -------------------------------------------------

    async with _cache_lock:
        _score_cache[
            cache_key
        ] = score

    return score

def get_evo2_cache_stats() -> dict:
    """
    Return basic cache statistics.
    """

    total = (
        _cache_hits
        + _cache_misses
    )

    hit_rate = (
        _cache_hits / total
        if total > 0
        else 0.0
    )

    return {
        "entries": len(
            _score_cache
        ),

        "max_size":
            EVO2_CACHE_MAXSIZE,

        "ttl_seconds":
            EVO2_CACHE_TTL_SECONDS,

        "hits":
            _cache_hits,

        "misses":
            _cache_misses,

        "hit_rate":
            hit_rate,
    }
    
def clear_evo2_cache() -> None:
    """
    Clear all cached Evo2 scores.
    """

    global _cache_hits
    global _cache_misses

    _score_cache.clear()

    _cache_hits = 0
    _cache_misses = 0