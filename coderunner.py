
import collections

from PyQt5.QtCore import (Qt,
                          QSize,
                          QThread,
                          QTimer,
                          QObject,
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
                             )

from interpreter import FastBrainfuckInterpreter, BFInterpreter, ErrorTypes, ProgramError, ProgramRuntimeError, ProgramSyntaxError, InterpreterError
from utility_widgets import WorkerThread
from input_text import InputTextEdit


class IOObject(QObject):
    input_ = pyqtSignal()
    output = pyqtSignal(str)


class CodeRunner(QWidget):

    INTERPRETER_TYPES = {
        '.b': FastBrainfuckInterpreter,
    }

    new_input_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.interpreter_type = None

        self.init_widgets()

    def init_widgets(self):

        # FIXME:
        #   Text changes back to the original font when
        #   the CodeRunner (self) if dragged out of the docking area.

        self.new_input_signal.connect(self.ask_new_input)

        self.buffer_timer = QTimer(self)
        self.buffer_timer.timeout.connect(self.add_from_buffer)
        self.buffer_timer.setInterval(10)

        self.output_text = QPlainTextEdit(self)
        self.output_text.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.output_text.setMaximumBlockCount(1000)
        self.output_text.setReadOnly(True)

        self.input_text = InputTextEdit(self)
        self.input_text.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.input_text.setMaximumBlockCount(1000)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.output_text)
        splitter.addWidget(self.input_text)

        self.statusbar = QStatusBar(self)

        layout = QVBoxLayout()
        layout.addWidget(splitter)
        layout.addWidget(self.statusbar)
        self.setLayout(layout)

        self.thread = WorkerThread()
        # self.thread.progress.connect(self.add_output)
        # self.thread.progress.connect(self.buffer_output)
        self.thread.error.connect(self.program_error)
        # self.thread.finished.connect(self.run_finished)

        self.statusbar.showMessage('Ready')

    def set_extension(self, extension):
        self.interpreter_type = self.INTERPRETER_TYPES.get(extension)
        self.input_text.set_extension(extension)

    def run_code(self, code):
        if self.thread.isRunning():
            self.waiting_for_input = False
            return

        if self.interpreter_type is None:
            self.add_output('Invalid file extension')
            return

        self.cleanup()
        self.output_text.clear()
        self.input_text.restart()
        self.statusbar.showMessage('Running')
        try:
            interpreter = self.interpreter_type(code, input_func=self.next_input,
                                                output_func=lambda char: self.output_buffer.append(char))
            # output_func=self.buffer_output)
            # interpreter = self.interpreter_type(code, input_func=self.io_object.input_.emit,
            #                                     output_func=self.io_object.output.emit)
        except ProgramError as error:
            self.program_error(error)
            # self.run_finished()
        else:
            # New output added to the right (append to right, pop from left)
            self.output_buffer = collections.deque()

            self.thread.func = interpreter.run
            self.buffer_timer.start()
            self.thread.start()
            # self.thread.start(priority=QThread.IdlePriority)

    def add_output(self, text):
        self.output_text.moveCursor(QTextCursor.End)
        self.output_text.insertPlainText(text)
        self.output_text.ensureCursorVisible()

    def run_finished(self):
        """Should only be called when execution has been ended and there is nothing left in the output buffer."""
        self.add_output('\nFinished.')
        self.statusbar.showMessage('Ready')
        self.buffer_timer.stop()

    def program_error(self, error):
        if not isinstance(error, InterpreterError):
            raise error

        error_type = error.error
        message = error.message
        if message is None:
            if error_type is ErrorTypes.UNMATCHED_OPEN_PAREN:
                message = 'Unmatched opening parentheses'
            elif error_type is ErrorTypes.UNMATCHED_CLOSE_PAREN:
                message = 'Unmatched closing parentheses'
            elif error_type is ErrorTypes.INVALID_TAPE_CELL:
                message = 'Tape pointer out of bounds'
            else:
                raise error

        error_text = f'\nError: {message}{f" at {error.location}" if error.location is not None else ""}'
        # self.add_output(error_text)
        self.buffer_output(error_text)

    def cleanup(self):
        print('closeEvent')
        print(self.thread.isFinished())
        # self.thread.quit()
        self.thread.terminate()
        print(self.thread.isFinished())

    def buffer_output(self, chars):
        self.output_buffer.append(chars)

    def add_from_buffer(self):
        if self.output_buffer:
            length = min(100, len(self.output_buffer))
            text = ''.join(self.output_buffer.popleft() for _ in range(length))
            self.add_output(text)
        else:
            if self.thread.isFinished():
                self.run_finished()

    def next_input(self):
        input_ = self.input_text.next_()
        print('in next_input:', repr(input_))

        if input_ is None:
            while self.output_buffer:
                pass
            self.new_input_signal.emit()
            self.waiting_for_input = True
            while self.waiting_for_input:
                pass
            return self.next_input()

        return input_

    def ask_new_input(self):
        self.statusbar.showMessage('Waiting for input. Press Ctrl+B.')
