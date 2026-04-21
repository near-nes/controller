"""Neurocontroller: closed-loop cerebellar control of a robotic arm."""

try:
    from neurocontroller._version import __version__  # type: ignore[attr-defined]
except ImportError:
    # Source tree without a generated _version.py yet (e.g. build without
    # setuptools-scm, or a fresh clone before ``pip install``).
    __version__ = "0+unknown"

__all__ = ["__version__"]
