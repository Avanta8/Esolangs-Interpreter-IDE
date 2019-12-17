
import threading

from PyQt5.QtCore import QRunnable, QThreadPool, QObject, pyqtSignal, QThread
from PyQt5.QtGui import (QTextCursor,
                         )
from PyQt5.QtWidgets import (QPlainTextEdit,
                             QWidget,
                             QVBoxLayout,
                             )

from interpreter import FastBrainfuckInterpreter, ErrorTypes, ProgramError, ProgramRuntimeError, ProgramSyntaxError


_INTERPRETERS = {
    '.b': FastBrainfuckInterpreter,
}


class WorkerThread(QThread):

    # For some reason, threads slow down the GUI a lot :(

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
        # finished is given as a default signal


class CodeRunner(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.extension = None

        self.init_widgets()

    def init_widgets(self):

        # FIXME:
        #   Text changes back to the original font when
        #   the CodeRunner (self) if dragged out of the docking area.

        self.text = QPlainTextEdit(self)
        self.text.setLineWrapMode(QPlainTextEdit.NoWrap)

        layout = QVBoxLayout()
        layout.addWidget(self.text)
        self.setLayout(layout)

        self.thread = WorkerThread()
        self.thread.progress.connect(self.add_output)
        self.thread.error.connect(self.program_error)
        self.thread.finished.connect(self.run_finished)

    def set_extension(self, extension):
        self.extension = extension

    def run_code(self, code):
        # Reset the output text
        self.text.setPlainText('')

        try:
            interpreter_type = _INTERPRETERS[self.extension]
        except KeyError:
            self.set_error_text('Invalid file extension')
            return

        try:
            interpreter = interpreter_type(code, output_func=lambda char: self.thread.progress.emit(char))
        except ProgramError as error:
            # Syntax error will be caught here
            self.program_error(error)
            self.run_finished()
            return

        self.thread.func = interpreter.run
        self.thread.start(priority=QThread.IdlePriority)

    def add_output(self, chars):
        self.text.moveCursor(QTextCursor.End)
        self.text.insertPlainText(chars)

    def run_finished(self):
        self.add_output('\nFinished.')
        self.text.ensureCursorVisible()

    def program_error(self, error):
        error_type = error.error
        if error_type is ErrorTypes.UNMATCHED_OPEN_PAREN:
            message = 'Unmatched opening parentheses'
        elif error_type is ErrorTypes.UNMATCHED_CLOSE_PAREN:
            message = 'Unmatched closing parentheses'
        elif error_type is ErrorTypes.INVALID_TAPE_CELL:
            message = 'Tape pointer out of bounds'
        else:
            raise error

        error_text = f'\nError: {message}{f" at {error.location}" if error.location else ""}'
        self.add_output(error_text)

    def set_error_text(self, text):
        self.add_output(text)

    def cleanup(self):
        print('closeEvent')
        print(self.thread.isFinished())
        # self.thread.quit()
        self.thread.terminate()
        print(self.thread.isFinished())
