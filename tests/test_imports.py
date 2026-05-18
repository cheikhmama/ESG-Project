"""Smoke tests: all three packages must be importable with the correct version."""

import esg_api
import esg_core
import esg_data


def test_esg_core_importable() -> None:
    assert esg_core.__version__ == "0.1.0"


def test_esg_data_importable() -> None:
    assert esg_data.__version__ == "0.1.0"


def test_esg_api_importable() -> None:
    assert esg_api.__version__ == "0.1.0"
