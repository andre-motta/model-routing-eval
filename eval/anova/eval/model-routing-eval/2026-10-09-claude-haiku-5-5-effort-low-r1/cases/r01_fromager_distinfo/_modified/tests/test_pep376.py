import pytest
from packaging.utils import InvalidWheelFilename

from fromager.pkgmetadata import dist_info_name, verbatim_dist_name


def test_verbatim_dist_name_keeps_case() -> None:
    # Arrange
    filename = "MarkupSafe-3.0.2-py3-none-any.whl"

    # Act
    name = verbatim_dist_name(filename)

    # Assert
    assert name == "MarkupSafe"


def test_dist_info_name_uses_verbatim_name_and_version() -> None:
    # Arrange
    filename = "MarkupSafe-3.0.2-py3-none-any.whl"

    # Act
    name = dist_info_name(filename)

    # Assert
    assert name == "MarkupSafe-3.0.2.dist-info"


def test_dist_info_name_keeps_version_unnormalized() -> None:
    # Arrange: "01.0" normalizes to "1.0", but the filename spelling is kept
    filename = "Foo_Bar-01.0-py3-none-any.whl"

    # Act
    name = dist_info_name(filename)

    # Assert
    assert name == "Foo_Bar-01.0.dist-info"


def test_dist_info_name_ignores_build_tag() -> None:
    # Arrange
    filename = "MarkupSafe-3.0.2-1-py3-none-any.whl"

    # Act
    name = dist_info_name(filename)

    # Assert
    assert name == "MarkupSafe-3.0.2.dist-info"


@pytest.mark.parametrize(
    "filename",
    [
        "MarkupSafe-3.0.2.tar.gz",
        "MarkupSafe-3.0.2-py3-none-any.zip",
        "not-a-wheel-name.whl",
    ],
)
def test_helpers_reject_invalid_wheel_filenames(filename: str) -> None:
    # Act / Assert
    with pytest.raises(InvalidWheelFilename):
        verbatim_dist_name(filename)
    with pytest.raises(InvalidWheelFilename):
        dist_info_name(filename)
