import pytest
from packaging.utils import InvalidWheelFilename

from fromager.pkgmetadata import dist_info_name, verbatim_dist_name


def test_verbatim_dist_name() -> None:
    assert verbatim_dist_name("MarkupSafe-3.0.2-py3-none-any.whl") == "MarkupSafe"


def test_dist_info_name_verbatim_version() -> None:
    wheel = "MarkupSafe-3.0.2-1-cp312-cp312-linux_x86_64.whl"
    assert dist_info_name(wheel) == "MarkupSafe-3.0.2.dist-info"


@pytest.mark.parametrize("filename", ["pkg-1.0.tar.gz", "pkg.whl", "pkg-1.0-py3.whl"])
def test_invalid_filename(filename: str) -> None:
    with pytest.raises(InvalidWheelFilename):
        verbatim_dist_name(filename)
    with pytest.raises(InvalidWheelFilename):
        dist_info_name(filename)
