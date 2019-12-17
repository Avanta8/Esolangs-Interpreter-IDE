
from PyQt5.QtGui import (QPainter,
                         QSyntaxHighlighter,
                         QColor,
                         QTextCharFormat,
                         QTextCursor,
                         )
from PyQt5.QtCore import (Qt,
                          QSize,
                          QRect,
                          QRegExp,
                          )
from PyQt5.QtWidgets import (QPlainTextEdit,
                             QWidget,
                             QApplication,
                             )


class DefaultHighlighter(QSyntaxHighlighter):

    def highlightBlock(self, text):
        pass


class BrainfuckHighlighter(QSyntaxHighlighter):

    def __init__(self, document):
        super().__init__(document)

        # Default rules
        rules = [
            (r'[\[\]]+', 'loop'),
            (r'[<>]+', 'pointer'),
            (r'[+-]+', 'cell'),
            (r'[.,]+', 'io'),
            (r'[^<>\-+,.\[\]]+', 'comment')
        ]
        self.rules = [(QRegExp(reg), rule) for reg, rule in rules]

        self.set_default_rule_formats()
        self.set_formats()

    def set_default_rule_formats(self):
        """Set the default formatting for all the rules."""
        self.rule_formats = {
            'loop': QTextCharFormat(),
            'pointer': QTextCharFormat(),
            'cell': QTextCharFormat(),
            'io': QTextCharFormat(),
            'comment': QTextCharFormat()
        }
        self.rule_formats['loop'].setForeground(QColor('red'))
        self.rule_formats['pointer'].setForeground(QColor('purple'))
        self.rule_formats['cell'].setForeground(QColor('green'))
        self.rule_formats['io'].setForeground(QColor('blue'))
        self.rule_formats['comment'].setForeground(QColor('grey'))

    def set_formats(self):
        """Set the format for each regexp and rehighlight the document.
        This method should be called whenever the default formatting changes,
        otherwise, the text won't be updated."""
        self.formats = [(reg, self.rule_formats[rule]) for reg, rule in self.rules]
        self.rehighlight()

    def highlightBlock(self, text):
        """Signal called by default when text is changed. `text` is the text on the
        current line."""
        for regexp, format_ in self.formats:
            index = regexp.indexIn(text)
            while index >= 0:
                length = regexp.matchedLength()
                self.setFormat(index, length, format_)
                index = regexp.indexIn(text, index + length)


class LineNumberArea(QWidget):
    def __init__(self, text):
        super().__init__(text)
        self.text = text

    def sizeHint(self):
        return QSize(self.text.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.text.line_number_paint(event)


class LineNumberText(QPlainTextEdit):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_widgets()

    def init_widgets(self):

        self.setLineWrapMode(self.NoWrap)

        self.line_number_area = LineNumberArea(self)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)

    def line_number_area_width(self, line=None):
        """Calculates the spacing required for `line`. If `line` is None,
        it defaults to the last line in the text."""
        if line is None:
            line = self.blockCount()

        # Minimum spacing of 3 chars
        digits = max(3, len(str(line)))

        space = 3 + self.fontMetrics().averageCharWidth() * digits

        return space

    def update_line_number_area_width(self, lines=None):
        """Called when the number of lines (blocks) change. `lines` if the total
        number of lines if called by the signal; otherwise, `lines` may be None."""
        self.setViewportMargins(self.line_number_area_width(lines), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """Update the current line numbers."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

    def resizeEvent(self, event):
        """Event called when widget is resized (eg. user dragged the screen).
        Resize the line numbers spacing."""
        super().resizeEvent(event)

        contents_rect = self.contentsRect()  # Whole area of whole widget
        line_number_rect = QRect(contents_rect.left(), contents_rect.top(), self.line_number_area_width(), contents_rect.height())
        self.line_number_area.setGeometry(line_number_rect)
        self.update_line_number_area_width()

    def line_number_paint(self, event):
        """Paint the line numbers on the lines currently in view of the screen."""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()

        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                line_number = str(block_number + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.line_number_area.width() - 3, self.fontMetrics().height(), Qt.AlignRight, line_number)

            block = block.next()
            top = bottom
            bottom += self.blockBoundingRect(block).height()
            block_number += 1

    def setFont(self, font):
        """Set the default font. Resize the line numbers spacing."""
        super().setFont(font)

        self.update_line_number_area_width()


class CodeText(LineNumberText):

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = QApplication.keyboardModifiers()

        if key == Qt.Key_Tab:
            # Indent tab
            self.add_tab()
        elif key == Qt.Key_Backtab:
            # Unindent tab
            self.remove_tab()
        elif key == Qt.Key_Return:
            # Insert required spaces
            pass
        elif key == Qt.Key_Backspace:
            # Delete requred spaces
            pass
        else:
            super().keyPressEvent(event)

    def add_tab(self):
        selection_start, selection_end = self.get_selection_index()
        if selection_start == selection_end:
            self.insertPlainText('    ')
            return

        start_block = self.document().findBlock(selection_start)
        end_block = self.document().findBlock(selection_end)
        start, end = start_block.blockNumber(), end_block.blockNumber()
        cursor = self.textCursor()

        cursor.beginEditBlock()
        cursor.setPosition(start_block.position())
        for line in range(start, end + 1):
            cursor.insertText('    ')
            cursor.movePosition(QTextCursor.NextBlock)
        cursor.endEditBlock()

    def remove_tab(self):
        selection_start, selection_end = self.get_selection_index()
        start_block = self.document().findBlock(selection_start)
        end_block = self.document().findBlock(selection_end)
        end = end_block.blockNumber()
        cursor = self.textCursor()

        cursor.beginEditBlock()
        block = start_block
        while 0 <= block.blockNumber() <= end:
            text = block.text()
            spaces = len(text) - len(text.lstrip(' '))
            if spaces > 0:
                to_delete = spaces % 4 or 4
                cursor.setPosition(block.position())
                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, to_delete)
                cursor.removeSelectedText()
            block = block.next()
        cursor.endEditBlock()

    def get_selection_index(self):
        cursor = self.textCursor()
        return cursor.selectionStart(), cursor.selectionEnd()

    def block_num_at_index(self, index):
        return self.document().findBlock(index).blockNumber()
