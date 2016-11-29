from maze import analyze
import pytest
import numpy

def test_simple_maze():
    test_array = numpy.array([
        [-1, 0, -1, -1],
        [-1, 0, 0, -1],
        [-1, -1, 0, -1],
        [1, 0, 0, -1],
        [-1, -1, -1, -1]
    ])
    r = analyze(test_array)
    assert r.is_reachable == True
    assert r.path(0,1) == [(0, 1), (1, 1), (1, 2), (2, 2), (3, 2), (3, 1), (3, 0)]
    assert r.distances[0, 1] == 6


def test_simple_maze2():
    test_array = numpy.array([
        [-1, 0, -1, -1],
        [-1, 0, 0, -1],
        [-1, -1, 0, -1],
        [0, 1, 0, -1],
        [-1, -1, 0, -1]
    ])
    r = analyze(test_array)
    assert r.is_reachable == True
    assert r.path(0,1) == [(0, 1), (1, 1), (1, 2), (2, 2), (3, 2), (3, 1)]
    assert r.distances[0, 1] == 5


def test_simple_maze_cycle():
    test_array = numpy.array([
        [-1, 0, -1, -1, -1],
        [-1, 0, 0, 0, 0],
        [-1, -1, 0, -1, 0],
        [0, 1, 0, 0, 0],
        [-1, -1, -1, -1, -1]
    ])
    r = analyze(test_array)
    assert r.is_reachable == True
    assert r.path(0,1) == [(0, 1), (1, 1), (1, 2), (2, 2), (3, 2), (3, 1)]
    assert r.distances[0, 1] == 5
    # wall
    with pytest.raises(Exception):
        r.path(0,4)


def test_simple_maze_unreachable():
    test_array = numpy.array([
        [-1, 0, -1, -1, -1],
        [-1, 0, 0, -1, 0],
        [-1, -1, 0, -1, 0],
        [0, 1, 0, -1, 0],
        [-1, -1, -1, -1, -1]
    ])
    r = analyze(test_array)
    assert r.is_reachable == False
    assert r.path(1,1) == [(1, 1), (1, 2), (2, 2), (3, 2), (3, 1)]
    assert r.distances[1, 1] == 4
    # unreachable
    with pytest.raises(Exception):
        r.path(1,4)
    # wall
    with pytest.raises(Exception):
        r.path(0,4)