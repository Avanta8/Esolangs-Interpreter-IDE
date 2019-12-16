
import enum

from PyQt5.QtGui import (QTextCursor,
                         )
from PyQt5.QtWidgets import (QPlainTextEdit,
                             QWidget,
                             QVBoxLayout,
                             )

from interpreter import FastBrainfuckInterpreter


_INTERPRETERS = {
    '.b': FastBrainfuckInterpreter,
}


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

    def set_extension(self, extension):
        self.extension = extension

    def run_code(self, code):
        try:
            interpreter_type = _INTERPRETERS[self.extension]
        except KeyError:
            self.set_error_text('Invalid file extension')
            return

        # Reset the output text
        self.text.setPlainText('')

        interpreter = interpreter_type(code, output_func=self.add_output)
        interpreter.run()

        self.add_output('\nFinished.')
        self.text.ensureCursorVisible()

    def add_output(self, chars):
        # chars should only be 1 character long
        self.text.moveCursor(QTextCursor.End)
        self.text.insertPlainText(chars)

    def set_error_text(self, text):
        self.text.setPlainText(text)
