"""PEP 376 dist-info naming helpers"""

from packaging.utils import parse_wheel_filename


def verbatim_dist_name(wheel_filename: str) -> str:
    """Distribution name exactly as spelled in the wheel filename.

    ``parse_wheel_filename`` normalizes the name, but the ``.dist-info``
    directory uses the verbatim spelling (e.g. ``MarkupSafe``).

    Raises `packaging.utils.InvalidWheelFilename` for invalid filenames.
    """
    parse_wheel_filename(wheel_filename)
    return wheel_filename.split("-", 1)[0]


def dist_info_name(wheel_filename: str) -> str:
    """Name of the ``.dist-info`` directory for a wheel filename.

    Returns ``{name}-{version}.dist-info`` with name and version taken
    verbatim from the filename.

    Raises `packaging.utils.InvalidWheelFilename` for invalid filenames.
    """
    parse_wheel_filename(wheel_filename)
    name, version, _ = wheel_filename.split("-", 2)
    return f"{name}-{version}.dist-info"
