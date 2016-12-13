import os
from PyQt5 import QtWidgets, uic, QtGui, QtCore, QtSvg
import numpy
from .maze import analyze
from pprint import pprint
import copy
CELL_SIZE = 32


VALUE_ROLE = QtCore.Qt.UserRole
XYZ_ROLE = QtCore.Qt.DisplayRole

def get_path_line(filename):
    return QtSvg.QSvgRenderer(os.path.join(os.path.dirname(__file__), "pics", "lines", filename + ".svg"))

def get_path_arrow(arrow):
    filenames = {
        b"<": "left.svg",
        b">": "right.svg",
        b"v": "down.svg",
        b"^": "up.svg"
    }
    filename = filenames.get(arrow)
    if filename:
        return QtSvg.QSvgRenderer(os.path.join(os.path.dirname(__file__), "pics", "arrows", filename))
    else:
        return None

def get_tile(filename):
    return QtSvg.QSvgRenderer(os.path.join(os.path.dirname(__file__), "pics", filename))

def get_asset(*path):
    return QtSvg.QSvgRenderer(os.path.join(os.path.dirname(__file__), *path))

def pixels_to_logical(x, y):
    """return row, column"""
    return y//CELL_SIZE, x//CELL_SIZE


def logical_to_pixels(row, column):
    return column * CELL_SIZE, row * CELL_SIZE


class GridWidget(QtWidgets.QWidget):
    def __init__(self, array):
        super().__init__()
        self.array = array
        self.path_matrix = numpy.zeros(array.shape, dtype=numpy.int8)
        size = logical_to_pixels(*array.shape)
        self.setMinimumSize(*size)
        self.setMaximumSize(*size)
        self.resize(*size)
        self.dudes = []
        self.paths = []

    def paintEvent(self, event):
        rect = event.rect()  # získáme informace o překreslované oblasti
        print("paintevent ", rect)
        # zjistíme, jakou oblast naší matice to představuje
        # nesmíme se přitom dostat z matice ven
        row_min, col_min = pixels_to_logical(rect.left(), rect.top())
        row_min = max(row_min, 0)
        col_min = max(col_min, 0)
        row_max, col_max = pixels_to_logical(rect.right(), rect.bottom())
        row_max = min(row_max + 1, self.array.shape[0])
        col_max = min(col_max + 1, self.array.shape[1])

        painter = QtGui.QPainter(self)  # budeme kreslit

        TILES = {
            -1: get_tile("wall.svg"),
            0: get_tile("grass.svg"),
            1: get_tile("castle.svg"),
            2: get_tile("dude1.svg"),
            3: get_tile("dude2.svg"),
            4: get_tile("dude3.svg"),
            5: get_tile("dude4.svg"),
            6: get_tile("dude5.svg")
        }


        for row in range(row_min, row_max):
            for column in range(col_min, col_max):
                # získáme čtvereček, který budeme vybarvovat
                x, y = logical_to_pixels(row, column)
                rect = QtCore.QRectF(x, y, CELL_SIZE, CELL_SIZE)

                TILES[0].render(painter, rect)
                if self.path_matrix[row, column] > 0:
                    # render line
                    get_path_line(str(self.path_matrix[row, column])).render(painter, rect)

                    # render arrow
                    arrow_svg = get_path_arrow(self.solver_result.directions[row, column])
                    if arrow_svg:
                        arrow_svg.render(painter, rect)

                if self.array[row, column] < 0:
                    TILES[-1].render(painter, rect)
                elif self.array[row, column] > 1:
                    # dudes
                    TILES[int(self.array[row, column])].render(painter, rect)
                elif self.array[row, column] == 1:
                    # castle
                    TILES[int(self.array[row, column])].render(painter, rect)
                else:
                    # no need to paint grass again
                    pass

    def mousePressEvent(self, event):
        row, column = pixels_to_logical(event.x(), event.y())
        shape = self.array.shape
        if 0 <= row < shape[0] and 0 <= column < shape[1]:
            if event.button() == QtCore.Qt.LeftButton:
                if self.selected == 1:
                    # delete old castle before adding new one
                    castle_coords = numpy.where(self.array == 1)  # ([r1, r2], [c1, c2])
                    castle_coords = [indices.tolist() for indices in castle_coords]
                    if len(castle_coords[0]) > 0:
                        print("Deleting the old castle")
                        self.array[castle_coords[0][0], castle_coords[1][0]] = 0
                        self.update(*logical_to_pixels(castle_coords[0][0], castle_coords[1][0]), CELL_SIZE, CELL_SIZE)

                self.array[row, column] = self.selected

            else:
                self.array[row, column] = 0

            old_paths = copy.deepcopy(self.paths)
            self.find_paths()
            for path in self.paths + old_paths:
                for point in path:
                    self.update(*logical_to_pixels(point[0], point[1]), CELL_SIZE, CELL_SIZE)
        
            self.update(*logical_to_pixels(row, column), CELL_SIZE, CELL_SIZE)

    def load_maze(self, array):
        self.path_matrix = numpy.zeros(array.shape, dtype=numpy.int8)
        self.array = array
        self.find_paths()
        self.redraw()

    def find_paths(self):
        self.path_matrix = numpy.zeros(self.array.shape, dtype=numpy.int8)
        finish_coords = numpy.where(self.array == 1)  # ([r1, r2], [c1, c2])
        finish_coords = [indices.tolist() for indices in finish_coords]
        if len(finish_coords[0]) == 0:
            return False
        
        direction_map = {
            b"<": 2,
            b">": 8,
            b"v": 4,
            b"^": 1,
            b"X": 0,
            None: 0
        }

        direction_map_inv = {
            b">": 2,
            b"<": 8,
            b"^": 4,
            b"v": 1,
            b"X": 0,
            None: 0
        }

        self.solver_result = analyze(self.array)
        self.paths = []
        for row in range(self.array.shape[0]):
            for col in range(self.array.shape[1]):

                # dudes use 2-6
                if self.array[row, col] > 1:
                    dude_id = self.array[row, col]
                    try:
                        # find path
                        path = self.solver_result.path(row, col)
                    except Exception as e:
                        print(e)
                    else:
                        # path found
                        self.paths.append(path)
                        for i in range(len(path)):
                            point = path[i]
                            direction = self.solver_result.directions[path[i][0], path[i][1]]

                            prev_direction = self.solver_result.directions[path[i-1][0], path[i-1][1]] if i > 0 else None
                            next_direction = self.solver_result.directions[path[i+1][0], path[i+1][1]] if i < len(path)-1 else None

                            if direction == b"X":
                                self.path_matrix[point[0], point[1]] = self.path_matrix[point[0], point[1]] | direction_map_inv[prev_direction]
                            else:
                                self.path_matrix[point[0], point[1]] = self.path_matrix[point[0], point[1]] \
                                                        | direction_map[direction] \
                                                        | direction_map_inv[prev_direction]
        pprint(self.path_matrix)
        pprint(self.solver_result.directions)

    def redraw(self):
        size = logical_to_pixels(*self.array.shape)
        self.setMinimumSize(*size)
        self.setMaximumSize(*size)
        self.resize(*size)
        self.update()

    def wheelEvent(self, event):
        if (event.modifiers() & QtCore.Qt.ControlModifier):
            # print("wheelEvent() + ctrl captured")
            delta = event.pixelDelta()

            global CELL_SIZE
            new_size = CELL_SIZE + delta.y()
            if new_size > 1 and new_size < 128:
                CELL_SIZE = new_size
                self.redraw()
            event.accept()


class Maze():
    def __init__(self):
        self.app = QtWidgets.QApplication([])
        self.window = QtWidgets.QMainWindow()

        with open(os.path.join(os.path.dirname(__file__), "ui", "mainwindow.ui")) as f:
            uic.loadUi(f, self.window)

        array = numpy.zeros((15, 20))
        array[:, 5] = -1
        scroll_area = self.window.findChild(QtWidgets.QScrollArea, "scrollArea")

        self.grid = GridWidget(array)
        scroll_area.setWidget(self.grid)

        self.palette = self.window.findChild(QtWidgets.QListWidget, "palette")

        self.add_item_to_pallete("Grass", "grass.svg", 0)
        self.add_item_to_pallete("Wall", "wall.svg", -1)
        self.add_item_to_pallete("Castle", "castle.svg", 1)
        self.add_item_to_pallete("Dude Brow", "dude1.svg", 2)
        self.add_item_to_pallete("Dude Yellow", "dude2.svg", 3)
        self.add_item_to_pallete("Dude Pink", "dude3.svg", 4)
        self.add_item_to_pallete("Dude Blue", "dude4.svg", 5)
        self.add_item_to_pallete("Dude Green", "dude5.svg", 6)

        self.palette.itemSelectionChanged.connect(self.item_activated)
        self.palette.setCurrentRow(1)

        action = self.window.findChild(QtWidgets.QAction, "actionAbout")
        action.triggered.connect(self.about)

        action = self.window.findChild(QtWidgets.QAction, "actionNew")
        action.triggered.connect(self.new_dialog)

        action = self.window.findChild(QtWidgets.QAction, "actionQuit")
        action.triggered.connect(self.app.exit)

        # Open file dialog
        action = self.window.findChild(QtWidgets.QAction, "actionOpen")
        action.triggered.connect(self.open_dialog)

        # Save file dialog
        action = self.window.findChild(QtWidgets.QAction, "actionSave")
        action.triggered.connect(self.save_dialog)

    def new_dialog(self):
        dialog = QtWidgets.QDialog(self.window)
        with open(os.path.join(os.path.dirname(__file__), "ui", "newmaze.ui")) as f:
            uic.loadUi(f, dialog)
        result = dialog.exec()

        if result == QtWidgets.QDialog.Rejected:
            return

        cols = dialog.findChild(QtWidgets.QSpinBox, "widthBox").value()
        rows = dialog.findChild(QtWidgets.QSpinBox, "heightBox").value()

        self.grid.load_maze(numpy.zeros((rows, cols), dtype=numpy.int8))

        # self.grid.redraw()

    def save_dialog(self):
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self.window, 'Save File')
        if filename:
            try:
                print("Saving to " + filename)
                numpy.savetxt(filename, self.grid.array)
            except Exception as e:
                self.show_msg_box("Open file", "File could not be saved")
                print(e)

    def open_dialog(self):
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(self.window, "Open file")
        if filename:
            try:
                array = numpy.loadtxt(filename, dtype=numpy.int8)
                self.grid.load_maze(array)
            except Exception as e:
                print(e)
                self.show_msg_box("Open file", "Can't open file.")

    def show_msg_box(self, title, text, icon="critical",
                     additional_info=None, detailed_text=None):
        icons = {
            "critical": QtWidgets.QMessageBox.Critical,
            "information": QtWidgets.QMessageBox.Information,
        }
        icon = icons[icon]
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(title)
        msg.setIcon(icon)
        msg.setText(text)

        if additional_info:
            msg.setInformativeText(additional_info)
        if detailed_text:
            msg.setDetailedText(detailed_text)

        msg.exec()

    def about(self):
        dialog = QtWidgets.QDialog(self.window)
        with open(os.path.dirname(__file__), os.path.join("ui", "about.ui")) as f:
            uic.loadUi(f, dialog)
        result = dialog.exec()

    def add_item_to_pallete(self, name, icon, role):
        item = QtWidgets.QListWidgetItem(name)
        icon = QtGui.QIcon(os.path.join(os.path.dirname(__file__), "pics", icon))
        item.setData(QtCore.Qt.UserRole, role)
        item.setIcon(icon)
        self.palette.addItem(item)


    def item_activated(self):
        for item in self.palette.selectedItems():
            # row_num = palette.indexFromItem(item).row()
            self.grid.selected = item.data(VALUE_ROLE)
            print(self.grid.selected)


    def run(self):
        # Spuštění
        self.window.show()
        self.app.exec()


def main():
    maze = Maze()
    maze.run()

if __name__ == '__main__':
    main()
