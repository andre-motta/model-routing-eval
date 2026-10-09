import io
import zipfile
from unittest.mock import Mock, patch

import pytest
from packaging.utils import InvalidWheelFilename

from fromager.candidate import _wheel_metadata_path, get_metadata_for_wheel
from fromager.pkgmetadata import dist_info_name, verbatim_dist_name

METADATA = b"Metadata-Version: 2.1\nName: MarkupSafe\nVersion: 3.0.2\n"
VENDORED = b"Metadata-Version: 2.1\nName: vendored\nVersion: 9.9\n"


def make_wheel(members: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, content in members.items():
            z.writestr(name, content)
    return buf.getvalue()


def test_verbatim_dist_name_keeps_case() -> None:
    assert verbatim_dist_name("MarkupSafe-3.0.2-py3-none-any.whl") == "MarkupSafe"


@pytest.mark.parametrize("func", [verbatim_dist_name, dist_info_name])
@pytest.mark.parametrize("filename", ["pkg-1.0.tar.gz", "pkg.whl", "pkg-1.0-py3.whl"])
def test_helpers_reject_invalid_filenames(func, filename: str) -> None:
    with pytest.raises(InvalidWheelFilename):
        func(filename)


def test_dist_info_name_is_verbatim() -> None:
    assert (
        dist_info_name("MarkupSafe-3.0.2.RC1-1-py3-none-any.whl")
        == "MarkupSafe-3.0.2.RC1.dist-info"
    )


def test_wheel_metadata_path_ignores_query_and_fragment() -> None:
    url = "https://pkg.test/files/MarkupSafe-3.0.2-py3-none-any.whl?x=1#sha256=ab"
    assert _wheel_metadata_path(url) == "MarkupSafe-3.0.2.dist-info/METADATA"


def test_get_metadata_ignores_vendored_dist_info() -> None:
    wheel = make_wheel(
        {
            "MarkupSafe/_vendor/vendored-9.9.dist-info/METADATA": VENDORED,
            "MarkupSafe-3.0.2.dist-info/METADATA": METADATA,
        }
    )
    with patch("fromager.candidate.session") as session:
        session.get.return_value = Mock(content=wheel)
        md = get_metadata_for_wheel(
            "https://pkg.test/MarkupSafe-3.0.2-py3-none-any.whl"
        )
    assert md.name == "MarkupSafe"


def test_get_metadata_missing_member_raises() -> None:
    wheel = make_wheel({"other-1.0.dist-info/METADATA": VENDORED})
    with patch("fromager.candidate.session") as session:
        session.get.return_value = Mock(content=wheel)
        with pytest.raises(ValueError, match="Could not find METADATA"):
            get_metadata_for_wheel(
                "https://pkg.test/MarkupSafe-3.0.2-py3-none-any.whl"
            )
