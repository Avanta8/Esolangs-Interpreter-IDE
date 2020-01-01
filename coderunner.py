
import collections

from PyQt5.QtCore import Qt, QTimer
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

from interpreter import FastBrainfuckInterpreter, BFInterpreter, ErrorTypes, ProgramError, ProgramRuntimeError, ProgramSyntaxError
from utility_widgets import WorkerThread
from input_text import InputTextEdit


class CodeRunner(QWidget):

    INTERPRETERS = {
        '.b': FastBrainfuckInterpreter,
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        self.interpreter_type = None

        self.init_widgets()

    def init_widgets(self):

        # FIXME:
        #   Text changes back to the original font when
        #   the CodeRunner (self) if dragged out of the docking area.

        self.buffer_timer = QTimer(self)
        self.buffer_timer.timeout.connect(self.add_from_buffer)
        self.buffer_timer.setInterval(10)

        self.text = QPlainTextEdit(self)
        self.text.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.text.setMaximumBlockCount(1000)
        self.text.setReadOnly(True)

        self.input_ = InputTextEdit(self)
        self.input_.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.input_.setMaximumBlockCount(1000)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.text)
        splitter.addWidget(self.input_)

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
        self.interpreter_type = self.INTERPRETERS.get(extension)

    def run_code(self, code):
        # Reset the output text
        self.text.clear()
        self.cleanup()
        self.input_.restart()
        self.statusbar.showMessage('Running')

        if self.interpreter_type is None:
            self.set_error_text('Invalid file extension')
            self.run_finished()
            return

        try:
            interpreter = self.interpreter_type(code, input_func=self.next_input,
                                                output_func=lambda char: self.output_buffer.append(char))
        except ProgramError as error:
            print(error)
            # Syntax error will be caught here
            self.program_error(error)
            self.run_finished()
            return

        # New output added to the right (append to right, pop from left)
        self.output_buffer = collections.deque()

        self.thread.func = interpreter.run
        self.buffer_timer.start()
        self.thread.start()
        # self.thread.start(priority=QThread.IdlePriority)

    def add_output(self, text):
        self.text.moveCursor(QTextCursor.End)
        self.text.insertPlainText(text)
        self.text.ensureCursorVisible()

    def run_finished(self):
        self.add_output('\nFinished.')
        self.statusbar.showMessage('Ready')
        self.buffer_timer.stop()

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
        input_ = self.input_.next_()

        if input_ is None:
            self.output_buffer.append('\nPlease Enter input\n')
            while input_ is None:
                input_ = self.input_.next_()

        print(f'next input: {input_}')
        return input_

    # def get_input(self):
    #     input_text = self.input_.toPlainText()
    #     iter_input_text = iter(input_text)

    #     def input_func():
    #         try:
    #             input_ = next(iter_input_text)
    #         except StopIteration:
    #             input_text = self.get_instant_input()
    #         finally:
    #             return input_

    # def get_input(self):
    #     self.input_.setReadOnly(True)
    #     self.input_text = self.input_.toPlainText()
    #     self.input_index = 0

    # def input_func(self):
