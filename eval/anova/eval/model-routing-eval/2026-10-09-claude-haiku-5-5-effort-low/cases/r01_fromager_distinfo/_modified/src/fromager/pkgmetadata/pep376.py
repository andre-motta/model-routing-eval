"""Wheel ``.dist-info`` directory names

https://peps.python.org/pep-0376/
"""

from packaging.utils import parse_wheel_filename


def _wheel_parts(wheel_filename: str) -> list[str]:
    """Split a validated wheel filename into its verbatim parts.

    Raises:
        packaging.utils.InvalidWheelFilename: If the filename is not a valid wheel name.
    """
    parse_wheel_filename(wheel_filename)
    return wheel_filename.removesuffix(".whl").split("-")


def verbatim_dist_name(wheel_filename: str) -> str:
    """Return the distribution name as spelled in the wheel filename.

    Example: ``MarkupSafe-3.0.2-py3-none-any.whl`` returns ``MarkupSafe``.
    """
    return _wheel_parts(wheel_filename)[0]


def dist_info_name(wheel_filename: str) -> str:
    """Return the ``.dist-info`` directory name for a wheel filename.

    Name and version are taken verbatim from the filename.
    Example: ``MarkupSafe-3.0.2-py3-none-any.whl`` returns
    ``MarkupSafe-3.0.2.dist-info``.
    """
    parts = _wheel_parts(wheel_filename)
    return f"{parts[0]}-{parts[1]}.dist-info"
