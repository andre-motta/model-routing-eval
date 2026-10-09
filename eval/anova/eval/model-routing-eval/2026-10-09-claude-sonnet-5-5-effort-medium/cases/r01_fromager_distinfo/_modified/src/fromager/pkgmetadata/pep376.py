"""PEP 376 dist-info directory names

The dist-info directory in a wheel uses the verbatim distribution name and
version from the wheel filename, not the normalized forms.
"""

from packaging.utils import parse_wheel_filename


def verbatim_dist_name(wheel_filename: str) -> str:
    """Distribution name as spelled in the wheel filename (``MarkupSafe``).

    Raises `packaging.utils.InvalidWheelFilename` for invalid filenames.
    """
    parse_wheel_filename(wheel_filename)
    return wheel_filename.split("-", 1)[0]


def dist_info_name(wheel_filename: str) -> str:
    """Name of the dist-info directory: ``{name}-{version}.dist-info``.

    Name and version are taken verbatim from the wheel filename.
    Raises `packaging.utils.InvalidWheelFilename` for invalid filenames.
    """
    parse_wheel_filename(wheel_filename)
    name, version = wheel_filename.split("-", 2)[:2]
    return f"{name}-{version}.dist-info"
