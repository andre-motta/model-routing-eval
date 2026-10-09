import pytest
from packaging.utils import InvalidWheelFilename

from fromager.pkgmetadata import dist_info_name, verbatim_dist_name


def test_verbatim_dist_name() -> None:
    assert verbatim_dist_name("MarkupSafe-3.0.2-cp312-cp312-linux_x86_64.whl") == (
        "MarkupSafe"
    )


def test_dist_info_name() -> None:
    assert dist_info_name("MarkupSafe-3.0.2-1-cp312-cp312-linux_x86_64.whl") == (
        "MarkupSafe-3.0.2.dist-info"
    )
    assert dist_info_name("pkg_a-1.0.0.RC1-py3-none-any.whl") == (
        "pkg_a-1.0.0.RC1.dist-info"
    )


@pytest.mark.parametrize("func", [verbatim_dist_name, dist_info_name])
@pytest.mark.parametrize("filename", ["pkg-1.0.tar.gz", "pkg-1.0.whl", "pkg.whl"])
def test_invalid_wheel_filename(filename: str, func: type) -> None:
    with pytest.raises(InvalidWheelFilename):
        func(filename)  # type: ignore[operator]
