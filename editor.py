
import os

from PyQt5.QtGui import (QFont,
                         QColor,
                         )
from PyQt5.QtCore import (Qt,
                          QEvent,
                          QObject,
                          )
from PyQt5.QtWidgets import (QAction,
                             QPlainTextEdit,
                             QWidget,
                             QMainWindow,
                             QSplitter,
                             QTabWidget,
                             QVBoxLayout,
                             QSizePolicy,
                             QMdiArea,
                             QMdiSubWindow,
                             QDockWidget,
                             )

from text import CodeText, BrainfuckHighlighter, DefaultHighlighter
from coderunner import CodeRunner
from visualiser import VisualiserMaster


class TextEditor(QMainWindow):
    """Basic text editor widget containing a `CodeText` and maybe more."""

    highlighters = {
        '.b': BrainfuckHighlighter,
    }

    def __init__(self, editor_window):
        super().__init__()

        self.editor_window = editor_window
        self.filepath = None
        self.extension = None

        self.init_widgets()

    def init_widgets(self):

        self.code_text = CodeText(self)

        self.code_runner = CodeRunner(self)
        self.visualiser = VisualiserMaster(self, self.code_text)

        # Don't put self in dock widgets as it forces them to appear.
        self.code_runner_dock_widget = QDockWidget('Code Runner')
        self.code_runner_dock_widget.setMinimumSize(10, 10)
        self.code_runner_dock_widget.setWidget(self.code_runner)

        self.code_runner_dock_widget.closeEvent = lambda e: self.code_runner.cleanup()

        self.visualiser_dock_widget = QDockWidget('Visualiser')
        self.visualiser_dock_widget.setMinimumSize(10, 10)
        self.visualiser_dock_widget.setWidget(self.visualiser)

        self.setCentralWidget(self.code_text)
        # self.addDockWidget(Qt.BottomDockWidgetArea, self.code_runner_dock_widget)
        # self.addDockWidget(Qt.TopDockWidgetArea, self.visualiser_dock_widget)

    def current_save_info(self):
        """Return the current filepath and the current text."""
        return self.filepath, self.get_code_text()

    def store_filepath(self, filepath):
        """Set `self.filepath` to `filepath`. Set the current highlighter."""
        self.filepath = filepath
        self.extension = os.path.splitext(self.filepath)[1]

        self.code_runner.set_extension(self.extension)
        self.visualiser.set_extension(self.extension)
        self.set_highlighter()

    def store_open_file(self, filepath, text):
        """Store `filepath` and set current text to `text`."""
        self.store_filepath(filepath)
        self.code_text.setPlainText(text)

    def set_highlighter(self):
        """Sets the syntax highlighter for the text based on the current file extension."""
        highlighter = self.highlighters.get(self.extension, DefaultHighlighter)
        self.highlighter = highlighter(self.code_text.document())

    def dock_code_runner(self):
        """Docks the `code_runner_dock_widget` if it is not already visible"""
        if self.code_runner.isVisible():
            return
        self.addDockWidget(Qt.BottomDockWidgetArea, self.code_runner_dock_widget)
        self.code_runner_dock_widget.show()

    def dock_visualiser(self):
        """Docks the `visualiser_dock_widget` if it is not already visible"""
        if self.visualiser.isVisible():
            return
        self.addDockWidget(Qt.TopDockWidgetArea, self.visualiser_dock_widget)
        self.visualiser_dock_widget.show()

    def run_code(self):
        self.dock_code_runner()

        text = self.code_text.toPlainText()
        self.code_runner.run_code(text)

    def open_visualier(self):
        self.dock_visualiser()
        self.visualiser.visualise()

    def get_code_text(self):
        return self.code_text.toPlainText()


class EditorWindow(QTabWidget):
    """Editor containing one or more tabs of `TextEditor` pages."""

    def __init__(self, editor_area):
        super().__init__(editor_area)

        self.editor_area = editor_area

        self.init_widgets()

    def init_widgets(self):
        self.setMovable(True)  # Can drag tabs
        self.setTabsClosable(True)  # Tabs have crosses on

        self.tabCloseRequested.connect(self.close_tab)

        # For some reason, this doesn't call the focusInEvent
        self.setFocusPolicy(Qt.ClickFocus)

    def new_editor(self):
        """Create a new `TextEditor` page and add it to the tabs."""

        mdi = QMdiArea(self)
        self.addTab(mdi, 'Untitled')

        editor = TextEditor(self)
        mdi.editor = editor

        subwindow = mdi.addSubWindow(editor)
        subwindow.setWindowFlags(Qt.FramelessWindowHint)
        subwindow.showMaximized()

        self.setCurrentWidget(mdi)
        self.setFocus()
        self.editor_focus_in()

    def close_tab(self, tab_ind):
        """Close the tab. And delete the page. If there are no pages
        left, then delete `self`."""
        widget = self.widget(tab_ind)
        widget.deleteLater()
        self.removeTab(tab_ind)

        if self.count() == 0:
            self.close_window()

    def close_window(self):
        """Set the current window to None and deletes `self`"""
        print('close window')
        self.editor_area.current_window = None
        self.deleteLater()

    def mousePressEvent(self, pos):
        """Give self focus if mouse is pressed over `self`.
        A better way would be to override `focusInEvent` but that
        never seems to be called."""
        super().mousePressEvent(pos)

        self.setFocus()
        self.editor_focus_in()

    def editor_focus_in(self):
        """Set the current window of the editor area to `self`."""
        print('focus in:', self)
        self.editor_area.current_window = self

    def rename_tab(self, index, filepath):
        """Rename tab at `index` based on `filepath`."""
        name = f'{os.path.basename(filepath)}'
        self.setTabText(self.currentIndex(), name)

    def store_filepath(self, filepath):
        """Store `filepath` for the current tab and rename the tab.
        Called after the user saved as a file."""
        self.currentWidget().editor.store_filepath(filepath)
        self.rename_tab(self.indexOf(self.currentWidget()), filepath)

    def store_open_file(self, filepath, text):
        """Store `filepath` and `text` for the current tab and rename the tab.
        Called when the user opened a file."""
        self.currentWidget().editor.store_open_file(filepath, text)
        self.rename_tab(self.indexOf(self.currentWidget()), filepath)

    def run_code(self):
        self.currentWidget().editor.run_code()

    def open_visualier(self):
        self.currentWidget().editor.open_visualier()


class EditorArea(QWidget):
    """Whole text editor area containing zero or more `EditorWindow` objects."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_widgets()

    def init_widgets(self):

        font = QFont()
        font.setPointSize(9)
        font.setFamily('Source Code Pro')
        self.setFont(font)

        layout = QVBoxLayout(self)
        self.splitter = QSplitter(Qt.Horizontal)
        self.setLayout(layout)
        layout.addWidget(self.splitter)

        self.current_window = None

    def new_editor(self, window=None):
        """Make a new `TextEditor` page for the current window. If there is
        no current window, then choose the first open window. If no windows are
        open, then create a new window. If `window` is given, then ignore the
        saftey checks and create a new editor for that `window`."""
        print('self.current_window:', self.current_window)
        if window is None:
            if self.splitter.count() == 0:
                self.new_window()
            window = self.current_window if self.current_window is not None else self.splitter.widget(0)

        window.new_editor()

    def new_window(self, new_editor=False):
        """Create and return a new `EditorWindow`. If `new_editor` is True, then
        also create a new page for that window."""
        window = EditorWindow(self)
        self.splitter.addWidget(window)
        self.current_window = window
        if new_editor:
            self.new_editor(window)

    def get_current_save_info(self):
        """Return current save info from the current active editor. If no
        window is active, return None."""
        if self.current_window is None:
            return None
        return self.current_window.currentWidget().editor.current_save_info()

    def store_current_filepath(self, filepath):
        """Store the filepath of current active editor to `filepath`. If no
        window is active, return None."""
        if self.current_window is None:
            return
        self.current_window.store_filepath(filepath)

    def store_open_file(self, filepath, text):
        """Create a new editor and store `filepath` and load `text`."""
        self.new_editor()
        self.current_window.store_open_file(filepath, text)

    def run_code(self):
        if self.current_window is None:
            return
        self.current_window.run_code()

    def open_visualier(self):
        if self.current_window is None:
            return
        self.current_window.open_visualier()
