"""Methodology YAML loader — parses and validates methodology files.

Reproducibility: every loaded Methodology is immediately validated by Pydantic.
Any malformed weight or semver will raise a clear ValueError before any score
is computed.
"""

from pathlib import Path

import yaml
from pydantic import ValidationError

from esg_core.models.methodology import Methodology


def load_methodology(path: Path) -> Methodology:
    """Parse and validate a methodology YAML file.

    Args:
        path: Absolute or relative path to a ``.yaml`` methodology file.

    Returns:
        A fully validated, immutable :class:`Methodology` instance.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the file cannot be parsed as YAML.
        ValidationError: If the parsed data fails Pydantic validation
            (e.g. weights don't sum to 1.0, invalid semver).

    Reproducibility: Two calls with identical file content produce
    identical Methodology instances (structural equality guaranteed
    by frozen Pydantic models).
    """
    if not path.exists():
        msg = f"Methodology file not found: {path}"
        raise FileNotFoundError(msg)

    with path.open("r", encoding="utf-8") as fh:
        raw: object = yaml.safe_load(fh)

    if not isinstance(raw, dict):
        msg = f"Methodology file must be a YAML mapping, got {type(raw).__name__}: {path}"
        raise TypeError(msg)

    try:
        return Methodology.model_validate(raw)
    except ValidationError as exc:
        msg = f"Invalid methodology in {path}:\n{exc}"
        raise ValueError(msg) from exc
