import io
import re
import typing
import zipfile
from unittest.mock import Mock, patch

import pytest

from fromager.candidate import _wheel_metadata_path, get_metadata_for_wheel


def make_wheel(members: dict[str, str]) -> bytes:
    """Build an in-memory wheel with the given member contents."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, content in members.items():
            z.writestr(name, content)
    return buf.getvalue()


def metadata_text(name: str) -> str:
    return f"Metadata-Version: 2.1\nName: {name}\nVersion: 1.0\n"


def test_wheel_metadata_path_uses_dist_info_of_filename() -> None:
    # Arrange
    url = "https://pkg.test/simple/MarkupSafe-3.0.2-py3-none-any.whl"

    # Act
    path = _wheel_metadata_path(url)

    # Assert
    assert path == "MarkupSafe-3.0.2.dist-info/METADATA"


def test_wheel_metadata_path_ignores_query_and_fragment() -> None:
    # Arrange
    url = "https://pkg.test/files/MarkupSafe-3.0.2-py3-none-any.whl?sha256=abc#metadata"

    # Act
    path = _wheel_metadata_path(url)

    # Assert
    assert path == "MarkupSafe-3.0.2.dist-info/METADATA"


def test_wheel_metadata_path_decodes_percent_encoded_plus() -> None:
    # Arrange: "+" in local versions is commonly percent-encoded in URLs
    url = "https://pkg.test/files/foo_bar-1.0%2Blocal-py3-none-any.whl"

    # Act
    path = _wheel_metadata_path(url)

    # Assert
    assert path == "foo_bar-1.0+local.dist-info/METADATA"


@patch("fromager.candidate.session")
def test_get_metadata_for_wheel_ignores_vendored_dist_info(
    mock_session: typing.Any,
) -> None:
    # Arrange: a vendored dist-info sorts before the wheel's own one
    wheel = make_wheel(
        {
            "markupsafe/_vendor/vendored-1.0.dist-info/METADATA": metadata_text(
                "vendored"
            ),
            "MarkupSafe-3.0.2.dist-info/METADATA": metadata_text("MarkupSafe"),
        }
    )
    mock_session.get.return_value = Mock(content=wheel)
    url = "https://pkg.test/files/MarkupSafe-3.0.2-py3-none-any.whl"

    # Act
    metadata = get_metadata_for_wheel(url)

    # Assert
    assert metadata.name == "MarkupSafe"


@patch("fromager.candidate.session")
def test_get_metadata_for_wheel_missing_metadata_raises(
    mock_session: typing.Any,
) -> None:
    # Arrange: the wheel only has a vendored dist-info, not its own
    wheel = make_wheel(
        {"vendored-1.0.dist-info/METADATA": metadata_text("vendored")},
    )
    mock_session.get.return_value = Mock(content=wheel)
    url = "https://pkg.test/files/MarkupSafe-3.0.2-py3-none-any.whl"

    # Act / Assert
    with pytest.raises(
        ValueError, match=re.escape("MarkupSafe-3.0.2.dist-info/METADATA")
    ):
        get_metadata_for_wheel(url)
