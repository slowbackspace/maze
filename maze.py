import numpy
from collections import defaultdict
from collections import deque
from pprint import pprint

class Result(object):
    def __init__(self, distances, directions, is_reachable):
        self.distances = distances
        self.directions = directions
        self.is_reachable = is_reachable

    def path(self, row, column):
        if self.distances[row, column] < 0:
            raise Exception("Wall or a unreachable spot.")

        coords_list = []
        direction = self.directions[row, column]
        while(direction != b"X"):
            coords_list.append((row, column))
            if direction == b">":
                column += 1
            elif direction == b"<":
                column -=1
            elif direction == b"v":
                row +=1
            elif direction == b"^":
                row -=1
            else:
                raise Exception("woah should not happen")
            direction = self.directions[row, column]
        coords_list.append((row, column))
        return coords_list

def make_graph(array):
    rows = array.shape[0]
    cols = array.shape[1]

    graph = {(i, j): [] for j in range(cols) for i in range(rows) if array[i,j] >= 0}

    for row, col in graph.keys():
        if array[row][col] < 0:
            continue  # wall
        if row < rows - 1 and array[row + 1][col] >= 0:
            graph[(row, col)].append(("^", (row + 1, col)))
            graph[(row + 1, col)].append(("v", (row, col)))
        if col < cols - 1 and array[row][col + 1] >= 0:
            graph[(row, col)].append(("<", (row, col + 1)))
            graph[(row, col + 1)].append((">", (row, col)))
    # print(graph)
    return graph
    

def bfs_solver(maze, start):
    queue = deque([("", start, 0)])
    visited = set()
    distances = defaultdict(tuple)
    graph = make_graph(maze)

    while queue:
        path, coords, distance = queue.popleft()

        if coords in distances:
            if distances[coords][0] > distance:
                distances[coords] = (distance, path)
        else:
            distances[coords] = (distance, path)

        if coords in visited:
            continue

        visited.add(coords)

        for direction, neighbour in graph[coords]:
            queue.append((direction, neighbour, distance+1))

    # print(distances)

    distance_matrix = numpy.ndarray(maze.shape)
    distance_matrix.fill(-1)
    for point in distances:
        distance_matrix[point[0], point[1]] = distances[point][0]

    directionsMatrix = numpy.empty(maze.shape, dtype=("a", 1))
    # fill with "walls"
    directionsMatrix.fill("#")

    # fill with direction to the finish finish for each reachable point
    for point in distances:
        directionsMatrix[point[0], point[1]] = distances[point][1]

    # mark target
    directionsMatrix[start[0], start[1]] = "X"

    # mark unreachable points with space character
    is_reachable = True
    for point in graph:
        if point not in visited:
            directionsMatrix[point[0], point[1]] = " "
            is_reachable = False

    return distance_matrix, directionsMatrix, is_reachable


def analyze(array):
    finish_coords = numpy.where(array == 1)  # ([r1, r2], [c1, c2])
    finish_coords = [indices.tolist() for indices in finish_coords]

    start = (finish_coords[0][0], finish_coords[1][0])

    distanceMatrix, directionsMatrix, is_reachable = bfs_solver(array, start)
    result = Result(distanceMatrix, directionsMatrix, is_reachable)
    # print(distanceMatrix)
    # print(directionsMatrix)
    # print(result.path(0, 0))
    return result

if __name__ == '__main__':
    test_array = numpy.array([[ 1],
       [ 0],
       [-1],
       [-1],
       [ 0]], dtype=int)
    r = analyze(test_array)
    # print(r.is_reachable)