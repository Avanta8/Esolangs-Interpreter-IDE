
import codecs
import re

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import (QTextCursor,
                         QBrush,
                         QTextCharFormat,
                         QColor,
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


class BrainfuckDecoder:
    REGEX = re.compile(r'\\(?:n|r|t|\\|\d{1,3})|.', flags=re.DOTALL)

    @classmethod
    def decode_next(cls, text):
        match_obj = re.match(cls.REGEX, text)
        if match_obj is None:
            return None, 0

        # Matched string
        match = match_obj[0]

        # A match of length 1 means that the match was just a standard chararacter.
        # A match of more than length 1 means that the match was an escape sequence
        if len(match) > 1:
            if match[1].isdecimal():
                # Ascii code
                match = chr(int(match[1:]))
            else:
                # Escape character (\n, \r, \t)
                match = codecs.decode(match, 'unicode_escape')
        return match, match_obj.end()


class InputTextEdit(QPlainTextEdit):

    DECODERS = {
        '.b': BrainfuckDecoder,
    }

    def __init__(self, parent=None):
        super().__init__(parent)

        self.psudo_cursor = self.textCursor()

        self.default_char_format = QTextCharFormat()
        self.default_char_format.setBackground(QColor(Qt.white))

        self.highlight_char_format = QTextCharFormat()
        self.highlight_char_format.setBackground(QColor(Qt.gray))

        self._reset()

    def restart(self):
        self.remove_prev_highlight()
        self._reset()

    def _reset(self):
        self.prev_input_indexes = [0, 0]

    def next_(self):
        text = self.toPlainText()
        last_input = self.prev_input_indexes[-1]

        char, length = self.decoder.decode_next(text[last_input:])
        if char is None:
            return

        self.remove_prev_highlight()
        self.prev_input_indexes.append(last_input + length)
        self.highlight_current()

        return char

    def prev(self):
        self.remove_prev_highlight()
        self.prev_input_indexes.pop()
        self.highlight_current()

    def highlight_current(self):
        start = self.prev_input_indexes[-2]
        end = self.prev_input_indexes[-1]

        self.format_range(start, end, self.highlight_char_format)

    def remove_prev_highlight(self):
        start = self.prev_input_indexes[-2]
        end = self.prev_input_indexes[-1]

        self.format_range(start, end, self.default_char_format)

    def format_range(self, start, end, format_):
        self.psudo_cursor.setPosition(start)
        self.psudo_cursor.setPosition(end, QTextCursor.KeepAnchor)
        self.psudo_cursor.setCharFormat(format_)

    def set_extension(self, extension):
        self.decoder = self.DECODERS[extension]


if __name__ == "__main__":
    print(repr(BrainfuckDecoder.decode_next(r'\t')))
