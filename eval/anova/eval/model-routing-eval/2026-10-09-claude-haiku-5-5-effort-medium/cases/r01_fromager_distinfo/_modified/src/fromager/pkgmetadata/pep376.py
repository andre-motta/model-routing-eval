"""Wheel ``.dist-info`` directory names

https://peps.python.org/pep-0376/

A wheel's ``.dist-info`` directory is named after the distribution name and
version in the wheel filename. The helpers here derive that name from the
filename, validating it first.
"""

from packaging.utils import parse_wheel_filename


def verbatim_dist_name(wheel_filename: str) -> str:
    """Return the distribution name as spelled in a wheel filename.

    ``parse_wheel_filename()`` normalizes the name, so the first segment of
    the filename is returned as is. For example, ``MarkupSafe-3.0.2-...whl``
    gives ``MarkupSafe``.

    Raises:
        packaging.utils.InvalidWheelFilename: If the filename is not a valid
            wheel filename.
    """
    parse_wheel_filename(wheel_filename)
    return wheel_filename.split("-", 1)[0]


def dist_info_name(wheel_filename: str) -> str:
    """Return the ``.dist-info`` directory name for a wheel filename.

    The name is ``{verbatim_name}-{version}.dist-info``. The version is taken
    verbatim from the filename, and the optional build tag is not included.

    Raises:
        packaging.utils.InvalidWheelFilename: If the filename is not a valid
            wheel filename.
    """
    name = verbatim_dist_name(wheel_filename)
    version = wheel_filename.split("-")[1]
    return f"{name}-{version}.dist-info"
