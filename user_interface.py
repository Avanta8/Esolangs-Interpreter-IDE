
from PyQt5.QtCore import (Qt,
                          QEvent,
                          )
from PyQt5.QtWidgets import (QApplication,
                             QMainWindow,
                             QPlainTextEdit,
                             QToolBar,
                             QWidget,
                             QSplitter,
                             QTabWidget,
                             QVBoxLayout,
                             QFileDialog,
                             QMdiArea,
                             QAction,
                             )

from editor import EditorArea, TextEditor


class IDE(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_widgets()
        self._file_dialog_filter = 'All Files (*);;Text Files (*.txt);;Brainfuck (*.b)'

    def init_widgets(self):

        self.setGeometry(300, 200, 1280, 720)

        menubar = self.menuBar()
        file_actions = [
            [('New', self), ('Ctrl+N',), ('New file',), (self.file_new,)],
            [('New Window', self), ('Ctrl+Shift+N',), ('New window',), (self.file_new_window,)],
            [('Open', self), ('Ctrl+O',), ('Open file',), (self.file_open,)],
            [('Save', self), ('Ctrl+S',), ('Save file',), (self.file_save,)],
            [('Save As', self), ('Ctrl+Shift+S',), ('Save as',), (self.file_saveas,)],
        ]
        run_actions = [
            [('Run code', self), ('Ctrl+B',), ('Run code',), (self.run_code,)],
            [('Open visualiser', self), ('Ctrl+Shift+B',), ('Visualise run code',), (self.open_visualier,)]
        ]
        menus = ['&File', '&Run']
        all_actions = [file_actions, run_actions]

        for name, actions in zip(menus, all_actions):
            menu = menubar.addMenu(name)
            for action, shortcut, statustip, connect in actions:
                action = QAction(*action)
                action.setShortcut(*shortcut)
                action.setStatusTip(*statustip)
                action.triggered.connect(*connect)
                menu.addAction(action)

        # self.toolbar = QToolBar('Toolbar', self)
        # self.addToolBar(Qt.LeftToolBarArea, self.toolbar)

        self.editor_area = EditorArea(self)
        self.setCentralWidget(self.editor_area)

        self.statusBar()

        # self.file_dialog = QFileDialog()
        # self.file_dialog.setFileMode(QFileDialog.AnyFile)
        # self.file_dialog.setNameFilters([
        #     'Brainfuck (*.b)',
        #     'Any files (*)',
        # ])

        self.show()

    def file_new(self):
        """Create new file."""
        print('file_new')
        self.editor_area.new_editor()

    def file_new_window(self):
        """Create new window."""
        print('file_new_window')
        self.editor_area.new_window(new_editor=True)

    def file_open(self):
        """Opens file into new tab on current window."""
        print('file_open')
        filename, extension = QFileDialog.getOpenFileName(self, filter=self._file_dialog_filter)
        if not filename:
            return
        print(filename, extension)

        self.editor_area.store_open_file(filename, self._read_file(filename))

    def file_save(self):
        """Save current file."""
        print('file_save')
        save_info = self.editor_area.get_current_save_info()
        print(f'save_info: {save_info}')
        if save_info is None:
            return

        filepath, text = save_info
        if filepath is None:
            self.file_saveas()
            return

        self._write_file(filepath, text)

    def file_saveas(self):
        """Save as current file."""
        print('file_saveas')
        if self.editor_area.current_window is None:
            return

        filename, extension = QFileDialog.getSaveFileName(self, filter=self._file_dialog_filter)
        if not filename:
            return

        self.editor_area.store_current_filepath(filename)
        self.file_save()

    def _read_file(self, filepath):
        """Read `filepath` and return the contents."""
        with open(filepath, 'r') as file:
            read = file.read()
        return read

    def _write_file(self, filepath, text):
        """Write `text` to `filepath`."""
        with open(filepath, 'w') as file:
            file.write(text)

    def run_code(self):
        print('Run code')
        self.editor_area.run_code()

    def open_visualier(self):
        print('Run visualise')
        self.editor_area.open_visualier()


def main():
    app = QApplication([])
    _ = IDE()
    app.exec_()


if __name__ == "__main__":
    main()


# TODO: Use QSettings to create settings page
