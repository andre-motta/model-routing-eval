import io
import zipfile
from unittest import mock

import pytest

from fromager import candidate

METADATA = b"Metadata-Version: 2.1\nName: MarkupSafe\nVersion: 3.0.2\n"
URL = "https://pkg.test/files/MarkupSafe-3.0.2-py3-none-any.whl"


def _wheel(members: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in members.items():
            z.writestr(name, data)
    return buf.getvalue()


def test_wheel_metadata_path_ignores_query_and_fragment() -> None:
    path = candidate._wheel_metadata_path(URL + "?x=1#sha256=abc")
    assert path == "MarkupSafe-3.0.2.dist-info/METADATA"


def test_get_metadata_ignores_vendored_dist_info() -> None:
    data = _wheel(
        {
            "vendored-1.0.dist-info/METADATA": b"Metadata-Version: 2.1\nName: vendored\nVersion: 1.0\n",
            "MarkupSafe-3.0.2.dist-info/METADATA": METADATA,
        }
    )
    with mock.patch.object(candidate, "session") as session:
        session.get.return_value.content = data
        md = candidate.get_metadata_for_wheel(URL)
    assert md.name == "MarkupSafe"


def test_get_metadata_missing_member() -> None:
    data = _wheel({"vendored-1.0.dist-info/METADATA": METADATA})
    with mock.patch.object(candidate, "session") as session:
        session.get.return_value.content = data
        with pytest.raises(ValueError, match="Could not find METADATA"):
            candidate.get_metadata_for_wheel(URL)
