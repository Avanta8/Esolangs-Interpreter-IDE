
import itertools

from PyQt5.QtCore import (Qt,
                          QSize,
                          QThread,
                          pyqtSignal,
                          )
from PyQt5.QtGui import (QTextCursor,
                         QBrush,
                         )
from PyQt5.QtWidgets import (QPlainTextEdit,
                             QWidget,
                             QVBoxLayout,
                             QStatusBar,
                             QTableWidget,
                             QHBoxLayout,
                             QPushButton,
                             QGridLayout,
                             QTableWidgetItem,
                             QHeaderView,
                             QSplitter,
                             QFrame,
                             QSizePolicy,
                             )


class WorkerThread(QThread):

    error = pyqtSignal(Exception)
    result = pyqtSignal(object)
    progress = pyqtSignal(str)

    def __init__(self, func=lambda *a, **kw: None, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
        except Exception as error:
            self.error.emit(error)
        else:
            self.result.emit(result)


class ResizingTable(QTableWidget):

    # NOTE:
    # This is a bit buggy. For some reason, when resizing, it doesn't seem to remove
    # all the items in the table before placing them again.
    # "QTableWidget: cannot insert an item that is already owned by another QTableWidget"

    def __init__(self, parent=None, minsize=50, column_counts=()):
        super().__init__(parent)

        self.minsize = minsize
        self._column_counts = sorted(column_counts, reverse=True)

        self.reset_cells()

    def resizeEvent(self, event):
        super().resizeEvent(event)

        width = event.size().width()
        self.reformat(width)

    def reformat(self, width):
        columns = self._get_columns(width)
        if columns == self._last_columns:
            return

        rows = len(self._all_items) // columns + (1 if len(self._all_items) % columns else 0)

        for row in range(self.rowCount()):
            for column in range(self.columnCount()):
                self.takeItem(row, column)

        self.setRowCount(rows)
        self.setColumnCount(columns)
        for item, (column, row) in zip(self._all_items, ((x, y) for y in range(rows) for x in range(columns))):
            self.setItem(row, column, item)

        self._last_columns = columns

    def _get_columns(self, width):
        for column_count in self._column_counts:
            if width / column_count >= self.minsize:
                return column_count

        # Return this if there is not a specified number of columns
        # or if the table was too small to fit the smallest valid number of columns
        # but we must have at least one column
        return width // self.minsize or 1

    def add_item(self, item):
        if len(self._all_items) % self.columnCount() == 0:
            self.setRowCount(self.rowCount() + 1)

        self._all_items.append(item)

        row, column = divmod(len(self._all_items) - 1, self.columnCount())
        self.setItem(row, column, item)

    def reset_cells(self):
        for row in range(self.rowCount()):
            for column in range(self.columnCount()):
                self.takeItem(row, column)

        self.setRowCount(1)
        self.setColumnCount(1)
        self._all_items = []
        self._last_columns = -1
