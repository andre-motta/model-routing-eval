"""Derive wheel ``.dist-info`` directory names

https://peps.python.org/pep-0376/

A wheel's ``.dist-info`` directory uses the distribution name as spelled in the
wheel filename (``MarkupSafe``, not ``markupsafe``) and the version verbatim
from the filename. Wheels can also carry ``.dist-info`` directories of vendored
packages, so callers must build the exact name instead of searching for one.
"""

from packaging.utils import parse_wheel_filename


def verbatim_dist_name(wheel_filename: str) -> str:
    """Return the distribution name exactly as spelled in a wheel filename.

    Args:
        wheel_filename: Wheel filename, e.g. ``MarkupSafe-3.0.2-py3-none-any.whl``

    Returns:
        The verbatim distribution name, e.g. ``MarkupSafe``

    Raises:
        packaging.utils.InvalidWheelFilename: If the filename is not a valid wheel name
    """
    name, _ = _split_wheel_filename(wheel_filename)
    return name


def dist_info_name(wheel_filename: str) -> str:
    """Return the ``.dist-info`` directory name for a wheel filename.

    Args:
        wheel_filename: Wheel filename, e.g. ``MarkupSafe-3.0.2-py3-none-any.whl``

    Returns:
        ``{verbatim_name}-{version}.dist-info``, e.g. ``MarkupSafe-3.0.2.dist-info``

    Raises:
        packaging.utils.InvalidWheelFilename: If the filename is not a valid wheel name
    """
    name, version = _split_wheel_filename(wheel_filename)
    return f"{name}-{version}.dist-info"


def _split_wheel_filename(wheel_filename: str) -> tuple[str, str]:
    """Validate a wheel filename and return its verbatim name and version.

    The wheel spec escapes ``-`` in distribution names, so the first two
    dash-separated fields are always the name and the version.
    """
    # Raises InvalidWheelFilename for malformed names and non-wheel extensions.
    parse_wheel_filename(wheel_filename)
    name, version = wheel_filename.split("-")[:2]
    return name, version
