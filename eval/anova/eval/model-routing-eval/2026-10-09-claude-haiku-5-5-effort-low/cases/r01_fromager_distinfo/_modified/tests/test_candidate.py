import io
import typing
import zipfile
from unittest.mock import Mock, patch

import pytest
from packaging.utils import InvalidWheelFilename

from fromager.candidate import _wheel_metadata_path, get_metadata_for_wheel

WHEEL_URL = "https://pkg.test/files/MarkupSafe-3.0.2-py3-none-any.whl"


def make_metadata(name: str, version: str) -> bytes:
    return f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n".encode()


def make_wheel(members: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for member, data in members.items():
            zf.writestr(member, data)
    return buf.getvalue()


def test_wheel_metadata_path_uses_verbatim_name_and_version() -> None:
    # Arrange / Act
    path = _wheel_metadata_path(WHEEL_URL)

    # Assert
    assert path == "MarkupSafe-3.0.2.dist-info/METADATA"


def test_wheel_metadata_path_ignores_query_and_fragment() -> None:
    # Arrange
    url = f"{WHEEL_URL}?token=abc#sha256=def"

    # Act
    path = _wheel_metadata_path(url)

    # Assert
    assert path == "MarkupSafe-3.0.2.dist-info/METADATA"


def test_wheel_metadata_path_unquotes_filename() -> None:
    # Arrange
    url = "https://pkg.test/files/foo-1.0%2Blocal.abc-py3-none-any.whl"

    # Act
    path = _wheel_metadata_path(url)

    # Assert
    assert path == "foo-1.0+local.abc.dist-info/METADATA"


@pytest.mark.parametrize(
    "url",
    [
        "https://pkg.test/files/foo-1.0.tar.gz",
        "https://pkg.test/files/foo.whl",
    ],
)
def test_wheel_metadata_path_rejects_non_wheel(url: str) -> None:
    # Act & Assert
    with pytest.raises(InvalidWheelFilename):
        _wheel_metadata_path(url)


@patch("fromager.candidate.session")
def test_get_metadata_fallback_ignores_vendored_dist_info(
    mock_session: typing.Any,
) -> None:
    # Arrange: the vendored dist-info comes first in the zip
    wheel = make_wheel(
        {
            "markupsafe/_vendor/vendored-9.9.dist-info/METADATA": make_metadata(
                "vendored", "9.9"
            ),
            "MarkupSafe-3.0.2.dist-info/METADATA": make_metadata("MarkupSafe", "3.0.2"),
        }
    )
    mock_session.get.return_value = Mock(content=wheel)

    # Act
    metadata = get_metadata_for_wheel(WHEEL_URL)

    # Assert
    assert metadata.name == "MarkupSafe"
    assert str(metadata.version) == "3.0.2"
    mock_session.get.assert_called_once_with(WHEEL_URL)


@patch("fromager.candidate.session")
def test_get_metadata_fallback_missing_member_raises(
    mock_session: typing.Any,
) -> None:
    # Arrange: only a vendored dist-info, no METADATA for the wheel itself
    wheel = make_wheel(
        {
            "vendored-9.9.dist-info/METADATA": make_metadata("vendored", "9.9"),
        }
    )
    mock_session.get.return_value = Mock(content=wheel)

    # Act & Assert
    with pytest.raises(ValueError, match="Could not find METADATA file"):
        get_metadata_for_wheel(WHEEL_URL)
