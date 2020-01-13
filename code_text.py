
from PyQt5.QtGui import (QPainter,
                         QSyntaxHighlighter,
                         QColor,
                         QTextCharFormat,
                         QTextBlockFormat,
                         QTextCursor,
                         QTextFormat,
                         QTextBlock,
                         )
from PyQt5.QtCore import (Qt,
                          QSize,
                          QRect,
                          QRegExp,
                          QPoint,
                          )
from PyQt5.QtWidgets import (QPlainTextEdit,
                             QTextEdit,
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

        # for format_ in self.rule_formats.values():
        #     format_.setBackground(QColor(Qt.white))

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

        self.can_undo = False

        self.init_widgets()

    def init_widgets(self):

        self.setLineWrapMode(self.NoWrap)

        self.line_number_area = LineNumberArea(self)

        self.current_line_colour = QColor(Qt.gray).lighter(150)
        # self.current_block_format = QTextBlockFormat()
        # self.current_block_format.setBackground(self.current_line_colour)
        # self.current_block_format.setProperty(QTextFormat.FullWidthSelection, True)

        self.last_block_infos = []

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

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

    def highlight_current_line(self):
        if self.isReadOnly():
            return

        extra_selections = []

        selection = QTextEdit.ExtraSelection()
        selection.cursor = self.textCursor()
        if selection.cursor.hasSelection():
            selection.cursor.clearSelection()
        else:
            selection.format.setBackground(self.current_line_colour)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

        # If I want to expand this to multicursor support, I can create a list of previous
        # block infos instead.

        # print(self.can_undo)

        # textcursor = self.textCursor()
        # textcursor.beginEditBlock()
        # for prev_block, prev_format in self.last_block_infos:
        #     textcursor.setPosition(prev_block.position())
        #     textcursor.setBlockFormat(prev_format)

        # self.last_block_infos = []
        # textcursor.setPosition(self.textCursor().position(), QTextCursor.MoveAnchor)
        # self.last_block_infos.append((textcursor.block(), textcursor.block().blockFormat()))
        # textcursor.setBlockFormat(self.current_block_format)

        # textcursor.endEditBlock()
        # self.textCursor().joinPreviousEditBlock()

    # def focusInEvent(self, event):
    #     print('LineNumberText.focusInEvent')
    #     super().focusInEvent(event)
    #     self.highlight_current_line()

    # def focusOutEvent(self, event):
    #     print('LineNumberText.focusOutEvent')
    #     super().focusOutEvent(event)
    #     self.setExtraSelections([])

    def setReadOnly(self, value):
        super().setReadOnly(value)
        if value:
            self.setExtraSelections([])
        else:
            self.highlight_current_line()


class CodeText(LineNumberText):

    #############

    # NOTE!:
    # QPlainTextEdit::setExtraSelections
    # It can be used to: mark text - for breakpoint!

    # Cursor.setCharFormat can be used set set the format
    # to simulate multicursor.

    # QPlainTextEdit.cursorForPosition(pos)
    # can be used to set breakpoint to mouse event
    # can be bound to QWidget.mousePressEvent(event)
    # where event is a QMouseEvent

    #############

    HIGHLIGHTER_TYPES = {
        '.b': BrainfuckHighlighter,
    }

    def __init__(self, texteditor):
        super().__init__(texteditor)
        self.texteditor = texteditor

        self.indentation = '    '
        self.breakpoints = {}
        self.breakpoint_background = QColor(Qt.yellow)

        self.highlighter = DefaultHighlighter(self.document())

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.texteditor.editor_window.editor_focus_in()

    # def mousePressEvent(self, event):
    #     super().mousePressEvent(event)
    #     if event.button() == Qt.RightButton:
    #         print('right button')
    #         print(self.document().characterAt(self.cursorForPosition(event.pos()).position()))

    def mousePressEvent(self, event):
        button = event.button()
        modifiers = QApplication.keyboardModifiers()

        if button == Qt.LeftButton and modifiers == Qt.ControlModifier:
            # print('Add multicursor', event.pos(), event.localPos(), (event.x(), event.y()), self.document().characterAt(self.cursorForPosition(QPoint(0, 0)).position()))
            self.add_multicursor(event.pos())
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        buttons = event.buttons()
        modifiers = QApplication.keyboardModifiers()

        if buttons == Qt.LeftButton and modifiers == Qt.ControlModifier:
            print('move multicursor')
            # self.add_
        else:
            super().mousePressEvent(event)

    def add_multicursor(self, pos):
        # print(self.contentOffset().x(), self.contentOffset().y())
        # text_cursor = self.cursorForPosition(pos)
        # text_cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
        # f = QTextCharFormat()
        # f.setBackground(QColor(Qt.green))
        # text_cursor.setCharFormat(f)

        # text_cursor = self.cursorForPosition(pos)
        # selection = QTextEdit.ExtraSelection()
        # selection.cursor = text_cursor

        # self.setExtraSelections([selection])
        pass

    def keyPressEvent(self, event):
        key = event.key()
        # modifiers = QApplication.keyboardModifiers()

        # if key == Qt.Key_Q and modifiers == Qt.ControlModifier:
        #     self.set_breakpoint()

        special_key = True
        if key == Qt.Key_Tab:
            # Indent tab
            self.add_tab()
        elif key == Qt.Key_Backtab:
            # Unindent tab
            self.remove_tab()
        elif key == Qt.Key_Return:
            # Insert required spaces
            self.return_key()
        elif key == Qt.Key_Backspace:
            # Delete requred spaces
            self.backspace()
        elif key == Qt.Key_Space:
            # Inserts an edit separator
            # This is a bit hacky though. Probably refactor this.
            cursor = self.textCursor()
            cursor.beginEditBlock()
            super().keyPressEvent(event)
            cursor.endEditBlock()
        else:
            special_key = False

        if special_key:
            self.ensureCursorVisible()
        else:
            super().keyPressEvent(event)

    def set_breakpoint(self):

        print('set breakpoint')

        selection_start, selection_end = self.get_selection_index()

        if selection_start == selection_end:
            selection_end += 1

        # bps = []
        # extra_selection = QTextEdit.ExtraSelection()
        # # print(type(extra_selection.cursor))
        # # print(type(extra_selection.format))
        # cursor = self.textCursor()
        # cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
        # # cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, 3)
        # extra_selection.format.setBackground(self.breakpoint_background)
        # extra_selection.format.setAnchor(True)
        # extra_selection.cursor = cursor
        # bps.append(extra_selection)

        # cursor = self.textCursor()
        # for pos in range(selection_start, selection_end):
        #     print(pos)
        #     cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
        #     if pos in self.breakpoints:
        #         self.breakpoints.pop(pos)
        #     else:
        #         extra_selection = QTextEdit.ExtraSelection()
        #         extra_selection.format.setBackground(self.breakpoint_background)
        #         extra_selection.cursor = cursor
        #         self.breakpoints[pos] = extra_selection
        #     cursor.clearSelection()

        # self.setExtraSelections(self.breakpoints.values())

        cursor = self.textCursor()
        if cursor.hasSelection():
            fmt = QTextCharFormat()
            fmt.setBackground(Qt.green)
            cursor.setCharFormat(fmt)

    def add_tab(self):
        selection_start, selection_end = self.get_selection_index()
        if selection_start == selection_end:
            self.insertPlainText(self.indentation)
            return

        start_block = self.document().findBlock(selection_start)
        end_block = self.document().findBlock(selection_end)
        start, end = start_block.blockNumber(), end_block.blockNumber()
        cursor = self.textCursor()

        cursor.beginEditBlock()
        cursor.setPosition(start_block.position())
        for line in range(start, end + 1):
            cursor.insertText(self.indentation)
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
            spaces = self.search_spaces(block)
            if spaces > 0:
                to_delete = spaces % 4 or 4
                cursor.setPosition(block.position())
                cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, to_delete)
                cursor.removeSelectedText()
            block = block.next()
        cursor.endEditBlock()

    def return_key(self):
        selection_start, selection_end = self.get_selection_index()
        cursor = self.textCursor()

        cursor.beginEditBlock()
        if selection_start != selection_end:
            cursor.removeSelectedText()

        curr_block = cursor.block()
        spaces = self.search_spaces(curr_block)
        cursor.insertText('\n' + ' ' * spaces)

        cursor.endEditBlock()

    def backspace(self):
        selection_start, selection_end = self.get_selection_index()
        cursor = self.textCursor()
        # If there is a selection, then just delete that selection.
        # If cursor is at the start of a line, then just delete that line.
        if selection_start != selection_end or cursor.atBlockStart():
            # QTextCursor.deletePreviousChar() deletes any selected text if there is any
            cursor.deletePreviousChar()
            return

        block = cursor.block()
        spaces = self.search_spaces(block)
        if spaces == cursor.positionInBlock():
            to_delete = spaces % 4 or 4
            cursor.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor, to_delete)
            cursor.removeSelectedText()
        else:
            cursor.deletePreviousChar()

    def search_spaces(self, block):
        """Returns the number of spaces at the start of `block`."""
        text = block.text()
        return len(text) - len(text.lstrip(' '))

    def get_selection_index(self):
        cursor = self.textCursor()
        return cursor.selectionStart(), cursor.selectionEnd()

    def set_extension(self, extension):
        highlighter_type = self.HIGHLIGHTER_TYPES.get(extension, DefaultHighlighter)
        if type(self.highlighter) is highlighter_type:
            return

        self.highlighter = highlighter_type(self.document())
