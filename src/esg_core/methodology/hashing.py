"""Methodology hashing — canonical SHA-256 fingerprint.

The hash is used to tie a CompanyScore to the exact methodology that produced
it, enabling independent third-party verification. Two Methodology objects with
the same logical content must always produce the same hash regardless of the
order of keys in the source YAML.

Reproducibility: canonical JSON serialisation (sorted keys, no whitespace
variability) ensures byte-identical hashes for logically identical objects.
"""

import hashlib
import json
from typing import Any

from esg_core.models.methodology import Methodology


def _canonical_dict(obj: Any) -> Any:
    """Recursively sort all dict keys for canonical JSON serialisation.

    Reproducibility: Python dict ordering is insertion-ordered, not sorted.
    Always sorting ensures two Methodology objects with keys in different
    orders produce the same canonical form.
    """
    if isinstance(obj, dict):
        return {k: _canonical_dict(v) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        return [_canonical_dict(item) for item in obj]
    return obj


def methodology_hash(methodology: Methodology) -> str:
    """Compute a stable SHA-256 fingerprint of a Methodology.

    Args:
        methodology: A validated :class:`Methodology` instance.

    Returns:
        64-character lowercase hexadecimal SHA-256 digest.

    Reproducibility: The hash is computed over a canonical JSON form
    (sorted keys, no extra whitespace, UTF-8 encoded). Two methodologies
    that are logically identical — even if their source YAML had different
    key ordering — will produce the same hash.

    Example:
        >>> from pathlib import Path
        >>> from esg_core.methodology.loader import load_methodology
        >>> from esg_core.methodology.hashing import methodology_hash
        >>> m = load_methodology(Path("methodologies/default_v1.yaml"))
        >>> methodology_hash(m)
        'a3f4...'  # 64 hex characters
    """
    raw: dict[str, Any] = json.loads(methodology.model_dump_json())
    canonical = _canonical_dict(raw)
    serialised = json.dumps(canonical, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialised.encode("utf-8")).hexdigest()
