import pytest
from packaging.utils import InvalidWheelFilename

from fromager.pkgmetadata import dist_info_name, verbatim_dist_name


@pytest.mark.parametrize(
    ("wheel_filename", "expected"),
    [
        ("MarkupSafe-3.0.2-py3-none-any.whl", "MarkupSafe"),
        ("MarkupSafe-3.0.2-1-py3-none-any.whl", "MarkupSafe"),
        ("my_pkg-1.0-py3-none-any.whl", "my_pkg"),
    ],
)
def test_verbatim_dist_name_keeps_filename_spelling(
    wheel_filename: str, expected: str
) -> None:
    """Verify the name is returned as spelled in the filename, not normalized."""
    # Arrange / Act
    result = verbatim_dist_name(wheel_filename)
    # Assert
    assert result == expected


def test_dist_info_name_uses_verbatim_version() -> None:
    """Verify the version is taken from the filename, not from ``Version``."""
    # Arrange
    wheel_filename = "pkg-1.0.0+Abc-py3-none-any.whl"
    # Act
    result = dist_info_name(wheel_filename)
    # Assert
    assert result == "pkg-1.0.0+Abc.dist-info"


def test_dist_info_name_with_build_tag() -> None:
    """Verify the build tag is not part of the dist-info directory name."""
    # Arrange
    wheel_filename = "MarkupSafe-3.0.2-1-py3-none-any.whl"
    # Act
    result = dist_info_name(wheel_filename)
    # Assert
    assert result == "MarkupSafe-3.0.2.dist-info"


@pytest.mark.parametrize(
    "wheel_filename",
    [
        "pkg-1.0.0.tar.gz",
        "pkg-1.0.0-py3-none-any.zip",
        "not-a-wheel.whl",
        "my-pkg-1.0-py3-none-any.whl",
    ],
)
def test_helpers_reject_invalid_wheel_filename(wheel_filename: str) -> None:
    """Verify malformed names and non-wheel extensions raise InvalidWheelFilename."""
    # Act / Assert
    with pytest.raises(InvalidWheelFilename):
        verbatim_dist_name(wheel_filename)
    with pytest.raises(InvalidWheelFilename):
        dist_info_name(wheel_filename)
