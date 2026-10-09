"""Tests for PEP 376 wheel .dist-info naming and METADATA lookup."""

import io
import pathlib
import typing
import zipfile
from unittest.mock import Mock, patch

import pytest
from packaging.utils import InvalidWheelFilename

from fromager import dependencies
from fromager.candidate import _wheel_metadata_path, get_metadata_for_wheel
from fromager.pkgmetadata import dist_info_name, verbatim_dist_name

INVALID_WHEEL_FILENAMES = [
    "MarkupSafe-3.0.2.tar.gz",
    "MarkupSafe-3.0.2-py3-none.whl",
    "markupsafe.whl",
]


def _make_wheel(members: dict[str, str]) -> bytes:
    """Build an in-memory wheel with the given members, in insertion order."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in members.items():
            zf.writestr(name, content)
    return buf.getvalue()


def test_verbatim_dist_name_keeps_case() -> None:
    # Arrange
    wheel_filename = "MarkupSafe-3.0.2-cp313-cp313-manylinux_2_17_x86_64.whl"

    # Act
    name = verbatim_dist_name(wheel_filename)

    # Assert
    assert name == "MarkupSafe"


def test_verbatim_dist_name_with_build_tag() -> None:
    # Arrange
    wheel_filename = "Foo_Bar-1.0-123-py3-none-any.whl"

    # Act
    name = verbatim_dist_name(wheel_filename)

    # Assert
    assert name == "Foo_Bar"


@pytest.mark.parametrize("wheel_filename", INVALID_WHEEL_FILENAMES)
def test_verbatim_dist_name_rejects_invalid_filename(wheel_filename: str) -> None:
    # Act & Assert
    with pytest.raises(InvalidWheelFilename):
        verbatim_dist_name(wheel_filename)


def test_dist_info_name_uses_verbatim_name() -> None:
    # Arrange
    wheel_filename = "MarkupSafe-3.0.2-cp313-cp313-linux_x86_64.whl"

    # Act
    name = dist_info_name(wheel_filename)

    # Assert
    assert name == "MarkupSafe-3.0.2.dist-info"


def test_dist_info_name_excludes_build_tag() -> None:
    # Arrange
    wheel_filename = "mypkg-1.0.0-123-py3-none-any.whl"

    # Act
    name = dist_info_name(wheel_filename)

    # Assert
    assert name == "mypkg-1.0.0.dist-info"


def test_dist_info_name_keeps_version_verbatim() -> None:
    # Arrange: packaging normalizes this version to "1.0.0rc1"
    wheel_filename = "Foo-1.0.RC1-py3-none-any.whl"

    # Act
    name = dist_info_name(wheel_filename)

    # Assert
    assert name == "Foo-1.0.RC1.dist-info"


@pytest.mark.parametrize("wheel_filename", INVALID_WHEEL_FILENAMES)
def test_dist_info_name_rejects_invalid_filename(wheel_filename: str) -> None:
    # Act & Assert
    with pytest.raises(InvalidWheelFilename):
        dist_info_name(wheel_filename)


def test_get_metadata_from_wheel_keeps_verbatim_version(tmp_path: pathlib.Path) -> None:
    # Arrange: the dist-info uses the version as spelled in the filename
    wheel_file = tmp_path / "Foo-1.0.RC1-py3-none-any.whl"
    wheel_file.write_bytes(
        _make_wheel(
            {
                "Foo-1.0.RC1.dist-info/METADATA": (
                    "Metadata-Version: 2.1\nName: Foo\nVersion: 1.0rc1\n"
                ),
            }
        )
    )

    # Act
    metadata = dependencies._get_metadata_from_wheel(wheel_file)

    # Assert
    assert metadata.name == "Foo"


def test_wheel_metadata_path_ignores_query_and_fragment() -> None:
    # Arrange
    url = (
        "https://pkg.test/files/MarkupSafe-3.0.2-cp313-cp313-linux_x86_64.whl"
        "?sha256=abc#fragment"
    )

    # Act
    path = _wheel_metadata_path(url)

    # Assert
    assert path == "MarkupSafe-3.0.2.dist-info/METADATA"


def test_wheel_metadata_path_unquotes_filename() -> None:
    # Arrange: %2B is "+" in a local version label
    url = "https://pkg.test/files/pkg-1.0%2Bcpu-py3-none-any.whl"

    # Act
    path = _wheel_metadata_path(url)

    # Assert
    assert path == "pkg-1.0+cpu.dist-info/METADATA"


@patch("fromager.candidate.session")
def test_get_metadata_fallback_ignores_vendored_dist_info(
    mock_session: typing.Any,
) -> None:
    # Arrange: the vendored dist-info comes first in the archive
    wheel_bytes = _make_wheel(
        {
            "vendored-2.0.dist-info/METADATA": (
                "Metadata-Version: 2.1\nName: vendored\nVersion: 2.0\n"
            ),
            "pkg-1.0.dist-info/METADATA": (
                "Metadata-Version: 2.1\nName: pkg\nVersion: 1.0\n"
            ),
        }
    )
    mock_session.get.return_value = Mock(content=wheel_bytes)
    url = "https://pkg.test/simple/pkg-1.0-py3-none-any.whl"

    # Act
    metadata = get_metadata_for_wheel(url)

    # Assert
    assert metadata.name == "pkg"
    assert str(metadata.version) == "1.0"
    mock_session.get.assert_called_once_with(url)


@patch("fromager.candidate.session")
def test_get_metadata_fallback_missing_metadata_raises(
    mock_session: typing.Any,
) -> None:
    # Arrange: only a vendored dist-info, no METADATA for the wheel itself
    wheel_bytes = _make_wheel(
        {
            "vendored-2.0.dist-info/METADATA": (
                "Metadata-Version: 2.1\nName: vendored\nVersion: 2.0\n"
            ),
        }
    )
    mock_session.get.return_value = Mock(content=wheel_bytes)
    url = "https://pkg.test/simple/pkg-1.0-py3-none-any.whl"

    # Act & Assert
    with pytest.raises(ValueError, match="Could not find METADATA file in wheel"):
        get_metadata_for_wheel(url)
