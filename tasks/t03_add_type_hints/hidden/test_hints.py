import inspect
import typing

from geo import shapes
from geo.shapes import Polygon, distance, perimeter, centroid


def _check(fn, nparams):
    sig = inspect.signature(fn)
    hints = typing.get_type_hints(fn)
    params = [p for p in sig.parameters if p != "self"]
    assert len(params) == nparams
    for p in params:
        assert p in hints, f"{fn.__qualname__}: parameter {p} has no annotation"
    assert "return" in hints, f"{fn.__qualname__}: no return annotation"
    return hints


def test_functions_annotated():
    _check(distance, 2)
    _check(perimeter, 1)
    h = _check(centroid, 1)
    assert type(None) in typing.get_args(h["return"]) or h["return"] is type(None)


def test_methods_annotated():
    h = _check(Polygon.__init__, 2)
    assert type(None) in typing.get_args(h["name"]), "name should be Optional"
    _check(Polygon.area, 0)
    h = _check(Polygon.scaled, 1)
    assert h["return"] in (Polygon, "Polygon") or getattr(h["return"], "__forward_arg__", None) == "Polygon"
    _check(Polygon.describe, 0)


def test_behaviour_unchanged():
    sq = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)], "sq")
    assert sq.describe() == {"name": "sq", "sides": 4, "area": 4}
    assert shapes.perimeter([]) == 0.0
