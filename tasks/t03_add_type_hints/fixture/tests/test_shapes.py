from geo.shapes import Polygon, distance, perimeter, centroid


def test_square():
    sq = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)], "sq")
    assert sq.area() == 4
    assert perimeter(sq.points) == 8
    assert centroid(sq.points) == (1, 1)
    assert distance((0, 0), (3, 4)) == 5
    assert sq.scaled(2).area() == 16
    assert centroid([]) is None
