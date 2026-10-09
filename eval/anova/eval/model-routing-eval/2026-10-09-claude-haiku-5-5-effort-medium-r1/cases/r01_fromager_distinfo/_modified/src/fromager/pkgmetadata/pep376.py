"""Wheel filename helpers for PEP 376 ``.dist-info`` directory names

https://peps.python.org/pep-0376/

``packaging.utils.parse_wheel_filename`` normalizes the distribution name,
but the ``.dist-info`` directory inside a wheel keeps the spelling from the
filename (e.g. ``MarkupSafe``, not ``markupsafe``). These helpers return the
verbatim name and version instead.
"""

from packaging.utils import parse_wheel_filename


def _split_wheel_filename(wheel_filename: str) -> tuple[str, str]:
    """Split a wheel filename into its verbatim name and version.

    Raises:
        packaging.utils.InvalidWheelFilename: If the filename is not a valid wheel.
    """
    # Validate first. The split below relies on the name having no dashes,
    # which parse_wheel_filename guarantees.
    parse_wheel_filename(wheel_filename)
    name, version, *_ = wheel_filename.removesuffix(".whl").split("-")
    return name, version


def verbatim_dist_name(wheel_filename: str) -> str:
    """Return the distribution name exactly as spelled in the wheel filename.

    Args:
        wheel_filename: Wheel filename, e.g. ``MarkupSafe-3.0.2-py3-none-any.whl``.

    Returns:
        The verbatim name, e.g. ``MarkupSafe``.

    Raises:
        packaging.utils.InvalidWheelFilename: If the filename is not a valid wheel.
    """
    name, _ = _split_wheel_filename(wheel_filename)
    return name


def dist_info_name(wheel_filename: str) -> str:
    """Return the ``.dist-info`` directory name for a wheel filename.

    The name and version are taken verbatim from the filename, so the result
    matches the directory the wheel builder wrote into the archive.

    Args:
        wheel_filename: Wheel filename, e.g. ``MarkupSafe-3.0.2-py3-none-any.whl``.

    Returns:
        Directory name, e.g. ``MarkupSafe-3.0.2.dist-info``.

    Raises:
        packaging.utils.InvalidWheelFilename: If the filename is not a valid wheel.
    """
    name, version = _split_wheel_filename(wheel_filename)
    return f"{name}-{version}.dist-info"
