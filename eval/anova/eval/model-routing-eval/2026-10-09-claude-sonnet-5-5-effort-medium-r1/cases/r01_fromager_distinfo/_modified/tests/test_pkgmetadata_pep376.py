import pytest
from packaging.utils import InvalidWheelFilename

from fromager.pkgmetadata import dist_info_name, verbatim_dist_name


def test_verbatim_dist_name_keeps_case() -> None:
    assert verbatim_dist_name("MarkupSafe-3.0.2-cp312-cp312-linux_x86_64.whl") == (
        "MarkupSafe"
    )


def test_dist_info_name_verbatim_version() -> None:
    assert dist_info_name("MarkupSafe-3.0.2-1-py3-none-any.whl") == (
        "MarkupSafe-3.0.2.dist-info"
    )
    assert dist_info_name("pkg-1.0+local-py3-none-any.whl") == "pkg-1.0+local.dist-info"


@pytest.mark.parametrize("func", [verbatim_dist_name, dist_info_name])
@pytest.mark.parametrize("filename", ["pkg-1.0.tar.gz", "pkg-1.0.whl", "pkg.whl"])
def test_invalid_wheel_filename(func, filename: str) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(InvalidWheelFilename):
        func(filename)
