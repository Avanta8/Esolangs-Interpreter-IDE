
from collections import OrderedDict

from PyQt5.QtCore import (Qt,
                          QSize,
                          QTimer,
                          )
from PyQt5.QtGui import (QTextCursor,
                         QBrush,
                         QTextCharFormat,
                         QColor,
                         )
from PyQt5.QtWidgets import (QPlainTextEdit,
                             QWidget,
                             QVBoxLayout,
                             QBoxLayout,
                             QLayout,
                             QStatusBar,
                             QTableWidget,
                             QHBoxLayout,
                             QPushButton,
                             QGridLayout,
                             QTableWidgetItem,
                             QHeaderView,
                             QSplitter,
                             QFrame,
                             QLineEdit,
                             QSlider,
                             QLabel,
                             QCheckBox,
                             QScrollBar,
                             )

from interpreter import (FastBrainfuckInterpreter,
                         BFInterpreter,
                         ErrorTypes,
                         InterpreterError,
                         ProgramError,
                         NoInputError,
                         NoPreviousExecutionError,
                         ProgramRuntimeError,
                         ProgramSyntaxError,
                         ExecutionEndedError,)
from utility_widgets import ResizingTable
from input_text import InputTextEdit


class VisualiserLayoutManager(QHBoxLayout):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_widgets()

    def init_widgets(self):

        commands_frame = self._create_commands_frame()
        texts_frame = self._create_text_frame()

        # Creating the splitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(commands_frame)
        self.splitter.addWidget(texts_frame)

        self.addWidget(self.splitter)

    def _create_commands_frame(self):
        buttons_frame = self._create_buttons_frame()
        speed_frame = self._create_speed_frame()
        jump_frame = self._create_jump_frame()

        commands_layout = QVBoxLayout()
        commands_layout.addWidget(buttons_frame)
        commands_layout.addWidget(speed_frame)
        commands_layout.addWidget(jump_frame)

        commands_frame = QFrame()
        commands_frame.setLayout(commands_layout)
        commands_frame.setFrameShape(QFrame.StyledPanel)
        return commands_frame

    def _create_text_frame(self):
        self.input_text = InputTextEdit()
        self.output_text = QPlainTextEdit()
        self.input_text.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.output_text.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.output_text.setReadOnly(True)
        self.error_output = QLineEdit()

        texts_layout = QVBoxLayout()
        texts_layout.addWidget(QLabel('Input:'))
        texts_layout.addWidget(self.input_text)
        texts_layout.addWidget(QLabel('Output:'))
        texts_layout.addWidget(self.output_text)
        texts_layout.addWidget(self.error_output)

        texts_frame = QFrame()
        texts_frame.setLayout(texts_layout)
        texts_frame.setFrameShape(QFrame.StyledPanel)
        return texts_frame

    def _create_speed_frame(self):
        speed_label = QLabel('Runspeed:')
        # QSlider defaults to a range of 0 - 99 inclusive
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_checkbox = QCheckBox('Faster')

        speed_layout = QVBoxLayout()
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_checkbox)

        speed_frame = QFrame()
        speed_frame.setLayout(speed_layout)
        speed_frame.setFrameShape(QFrame.StyledPanel)
        return speed_frame

    def _create_buttons_frame(self):
        self.run_button = QPushButton('Run')
        self.continue_button = QPushButton('Continue')
        self.step_button = QPushButton('Step')
        self.pause_button = QPushButton('Pause')
        self.back_button = QPushButton('Back')
        self.stop_button = QPushButton('Stop')
        self.buttons = [self.run_button, self.step_button,
                        self.pause_button, self.back_button,
                        self.stop_button, self.continue_button]

        self.button_layout = QGridLayout()
        self.button_layout.setColumnStretch(0, 1)
        self.button_layout.setColumnStretch(1, 1)

        buttons_frame = QFrame()
        buttons_frame.setLayout(self.button_layout)
        buttons_frame.setFrameShape(QFrame.StyledPanel)
        return buttons_frame

    def _create_jump_frame(self):
        jump_label = QLabel('Jump:')
        self.jump_input = QLineEdit()
        self.jump_forwards_button = QPushButton('Forward')
        self.jump_backwards_button = QPushButton('Backwards')

        top_layout = QHBoxLayout()
        top_layout.addWidget(jump_label)
        top_layout.addWidget(self.jump_input)

        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.jump_backwards_button)
        bottom_layout.addWidget(self.jump_forwards_button)

        jump_layout = QVBoxLayout()
        jump_layout.addLayout(top_layout)
        jump_layout.addLayout(bottom_layout)

        jump_frame = QFrame()
        jump_frame.setLayout(jump_layout)
        jump_frame.setFrameShape(QFrame.StyledPanel)
        return jump_frame

    def set_visualiser(self, visualiser):
        """Display `visualiser` in `self.splitter`."""
        visualiser_layout = QVBoxLayout()
        visualiser_layout.addWidget(visualiser)
        visualiser_frame = QFrame()
        visualiser_frame.setLayout(visualiser_layout)
        visualiser_frame.setFrameShape(QFrame.StyledPanel)
        self.splitter.insertWidget(0, visualiser_frame)

    def display_running(self):
        """Display the buttons that should appear while running:
        - stop - pause
        """
        self.add_buttons(
            self.stop_button,
            self.pause_button
        )

    def display_stopped(self):
        """Display the buttons that should appear when stopped:
        - run - step
        """
        self.add_buttons(
            self.run_button,
            self.step_button
        )

    def display_paused(self):
        """Display the buttons that should appear when paused:
        - stop - step
        - back - continue
        """
        self.add_buttons(
            self.stop_button,
            self.step_button,
            self.back_button,
            self.continue_button
        )

    def add_buttons(self, a, b, c=None, d=None):
        """Clear all buttons then display the buttons a,b,c,d.
        Also hide the error text.

        TODO:
            Display the buttons on the same row. Eg. when only displaying
            two buttons, display them on the top row, not the middle.
        """
        self.clear_buttons()
        self.hide_error_text()
        self.button_layout.addWidget(a, 0, 0)
        a.show()
        self.button_layout.addWidget(b, 0, 1)
        b.show()
        if c is not None:
            self.button_layout.addWidget(c, 1, 0)
            c.show()
        if d is not None:
            self.button_layout.addWidget(d, 1, 1)
            d.show()

    def clear_buttons(self):
        """Remove all buttons."""
        for button in self.buttons:
            if button.isVisible():
                self.button_layout.removeWidget(button)
                button.hide()

    def display_error_text(self, text):
        self.error_output.show()
        self.error_output.setText(text)

    def hide_error_text(self):
        self.error_output.hide()


class BrainfuckVisualiser(QWidget):
    """Visualise Brainfuck programs"""

    # FIXME:
    # Doesn't quite scroll to item correctly, especially in set_visuals

    def __init__(self, parent):
        super().__init__(parent)
        self.commander = parent

        self.selected_format = QBrush(Qt.red)
        self.unselected_format = QBrush(Qt.white)
        self.foreground_format = QBrush(Qt.black)

        self.init_widgets()
        self.reset_tape()

    def init_widgets(self):
        self.table = ResizingTable(self, minsize=30, column_counts=(5, 10, 20))
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout = QVBoxLayout()
        layout.addWidget(self.table)
        self.setLayout(layout)

    def reset_tape(self):
        """"Reset the table to the default size of 20 cells."""
        self.table.reset_cells()
        for _ in range(20):
            self._add_table_cell()

        self.last_cell = QTableWidgetItem()

        self.visuals_to_add = OrderedDict()

    def add_visual(self, interpreter):
        self.visuals_to_add[interpreter.tape_pointer] = interpreter.current_cell
        self.visuals_to_add.move_to_end(interpreter.tape_pointer)

    def set_visuals(self):
        if not self.visuals_to_add:
            return

        for index, value in self.visuals_to_add.items():
            table_cell = self._get_table_cell_from_index(index)
            while table_cell is None:
                self._add_table_cell()
                table_cell = self._get_table_cell_from_index(index)
            table_cell.setText(str(value))

        self._highlight_cell(table_cell)
        self.table.scrollToItem(table_cell)

        self.visuals_to_add = OrderedDict()

    def configure_visual(self, interpreter):
        """"Configure the value of the current cell.
        `interpreter` is the current interpreter object.
        Then also highlight the cell."""
        table_cell = self._get_current_table_cell(interpreter)
        if table_cell is None:
            table_cell = self._add_table_cell()
        table_cell.setText(str(interpreter.current_cell))

        self._highlight_cell(table_cell)
        self.table.scrollToItem(table_cell)

    def _highlight_cell(self, table_cell):
        """Highlight `table_cell` and remove highlighting from the last highlighted cell."""
        if self.last_cell == table_cell:
            return

        self.last_cell.setBackground(self.unselected_format)
        table_cell.setBackground(self.selected_format)
        self.last_cell = table_cell

    def _get_current_table_cell(self, interpreter):
        """Return the current cell that `interpreter.tape_pointer` points to."""
        return self._get_table_cell_from_index(interpreter.tape_pointer)

    def _get_table_cell_from_index(self, index):
        cell_row, cell_column = divmod(index, self.table.columnCount())
        return self.table.item(cell_row, cell_column)

    def _add_table_cell(self):
        """Add a new cell to `self.table`."""
        table_cell = QTableWidgetItem('0')
        table_cell.setForeground(self.foreground_format)
        table_cell.setFlags(Qt.NoItemFlags)
        self.table.add_item(table_cell)
        return table_cell


class VisualiserController:
    """Class that handles the logic behind the visualising commands."""

    INTERPRETER_TYPES = {
        '.b': (BFInterpreter, BrainfuckVisualiser),
    }

    def __init__(self, master):
        self.visualiser_master = master

        self.interpreter_type = None
        self.visualiser = None

        self.interpreter = None

    def set_extension(self, extension):
        """Set the `self.interpreter_type` and `self.visualiser` to the correct ones defined by
        `extension`. If new `extension` is different, then delete `self.visualiser` and set it to None.
        If there is no suitable visualiser / interpreter for `extension`, set them to None."""
        interpreter_type, visualiser_type = self.INTERPRETER_TYPES.get(extension, (None, None))
        # if isinstance(self.visualiser, visualiser_type):
        if type(self.visualiser) is visualiser_type:
            # The new extension is the same as the old one
            return

        # Delete the current visualiser
        if self.visualiser is not None:
            self.visualiser.deleteLater()
            self.visualiser = None
            # self.visualiser_master.delete_visualiser()

        if visualiser_type is None:
            # There is no suitable visualiser / interpreter for the extension
            self.interpreter_type = None
            self.visualiser = None
        else:
            self.interpreter_type = interpreter_type
            self.visualiser = visualiser_type(self.visualiser_master)

            self.visualiser_master.set_visualiser(self.visualiser)
            self.visualiser_master.layout_manager.input_text.set_extension(extension)

    def step(self, display=True):
        """Step one instruction. If `display` is True, then also do special display stuff
        like highlighting the current command being executed. If `self.interpreter` is None,
        then initialise it. Return True if stepping was successful else False."""
        if self.interpreter is None:
            if not self.restart_interpreter():
                return False

        try:
            code_pointer = self.interpreter.step()
        except InterpreterError as error:
            self.handle_error(error)
            return False

        self.visualiser.configure_visual(self.interpreter)
        self.visualiser_master.set_current_code_pointer(code_pointer)
        if display:
            self.visualiser_master.highlight_current_code_pointer()

        return True

    def back(self, display=True):

        try:
            code_pointer = self.interpreter.back()
        except NoPreviousExecutionError as error:
            self.handle_error(error)
            return False

        self.visualiser.configure_visual(self.interpreter)
        self.visualiser_master.set_current_code_pointer(code_pointer)
        if display:
            self.visualiser_master.highlight_current_code_pointer()

        return True

    def jump_forwards(self, steps):
        self.jump(1, steps)

    def jump_backwards(self, steps):
        self.jump(-1, steps)

    def jump(self, direction, steps):

        if self.interpreter is None:
            if not self.restart_interpreter():
                return

        command = self.interpreter.step if direction == 1 else self.interpreter.back

        error = None
        changed = False
        for i in range(steps):
            try:
                code_pointer = command()
            except InterpreterError as e:
                error = e
                break
            changed = True
            self.visualiser.add_visual(self.interpreter)

        if changed:
            self.visualiser_master.set_current_code_pointer(code_pointer)
            self.visualiser_master.highlight_current_code_pointer()
            self.visualiser.set_visuals()

        if error is not None:
            self.handle_error(error)

    def stop(self):
        """Stop the interpreter. self `self.interpreter` to None"""
        self.interpreter = None

    def restart_interpreter(self):
        """Initaliser `self.interpreter`. Reset `self.visualiser` and `self.visualiser_master`.
        Return True if creating an interpreter was successful else False."""
        self.visualiser.reset_tape()
        self.visualiser_master.restart()

        try:
            self.interpreter = self.interpreter_type(self.visualiser_master.get_code_text(),
                                                     input_func=self.visualiser_master.next_input,
                                                     undo_input_func=self.visualiser_master.undo_input,
                                                     output_func=self.visualiser_master.set_output)
        except ProgramSyntaxError as error:
            self.handle_error(error)
            return False
        return True

    def handle_error(self, error):
        """Handle any `InterpreterError` raised by `self.interpreter`"""
        if isinstance(error, ExecutionEndedError):
            message = 'Execution finished'
        elif isinstance(error, NoPreviousExecutionError):
            message = 'No previous execution'
        elif isinstance(error, NoInputError):
            message = 'Enter input'
        elif isinstance(error, ProgramError):
            error_type = error.error
            if error_type is ErrorTypes.UNMATCHED_OPEN_PAREN:
                message = 'Unmatched opening parentheses'
            elif error_type is ErrorTypes.UNMATCHED_CLOSE_PAREN:
                message = 'Unmatched closing parentheses'
            elif error_type is ErrorTypes.INVALID_TAPE_CELL:
                message = 'Tape pointer out of bounds'
            else:
                raise error
        else:
            raise error

        self.visualiser_master.pause_command()
        self.visualiser_master.display_error_text(message)
        self.visualiser_master.highlight_current_code_pointer()


class VisualiserMaster(QWidget):

    def __init__(self, text_editor, code_text):
        super().__init__(text_editor)

        self.text_editor = text_editor
        self.code_text = code_text
        self.text_cursor = code_text.textCursor()

        self.visualiser_controller = VisualiserController(self)

        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(QColor(Qt.gray))

        self.prev_formats = {}

        self.init_widgets()
        self.stop_command()

        self.set_runspeed()

    def init_widgets(self):

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.run_signal)
        self.timer.setInterval(10)

        layout = VisualiserLayoutManager()
        self.setLayout(layout)
        self.layout_manager = layout

        layout.run_button.clicked.connect(self.run_command)
        layout.continue_button.clicked.connect(self.run_command)
        layout.step_button.clicked.connect(self.step_command)
        layout.pause_button.clicked.connect(self.pause_command)
        layout.back_button.clicked.connect(self.back_command)
        layout.stop_button.clicked.connect(self.stop_command)

        layout.jump_forwards_button.clicked.connect(lambda: self.jump_command(1))
        layout.jump_backwards_button.clicked.connect(lambda: self.jump_command(-1))

        layout.speed_slider.valueChanged.connect(self.set_runspeed)
        layout.speed_checkbox.stateChanged.connect(self.set_runspeed)

    def set_visualiser(self, visualiser):
        self.layout_manager.set_visualiser(visualiser)

    def restart(self):
        """Restart the visualising. <- Not a great description.
        Disables the code text."""
        self.set_current_code_pointer(0, length=0)
        self.layout_manager.input_text.restart()
        self.code_text.setReadOnly(True)

    def set_extension(self, extension):
        """Set the current file extension."""
        self.visualiser_controller.set_extension(extension)

    def visualise(self):
        """Assert that the current file is valid for visualising."""
        if self.visualiser_controller.interpreter_type is None:
            raise Exception('Invalid extension. No visualiser.')

    def get_code_text(self):
        """Return the current text in `self.code_text`"""
        return self.code_text.toPlainText()

    def run_command(self):
        """Called when `self.run_button` pressed.
        Start the running timer."""
        self.layout_manager.display_running()
        self.timer.start()
        self.run_signal()

    def step_command(self):
        """Called when `self.step_button` pressed.
        Step forwards once."""
        self.layout_manager.display_paused()
        self.visualiser_controller.step()

    def pause_command(self):
        """Called when `self.pause_button` pressed.
        Pause the running timer."""
        self.layout_manager.display_paused()
        self.timer.stop()

    def back_command(self):
        """Called when `self.back_button` pressed.
        Step backwards once."""
        self.layout_manager.display_paused()
        self.visualiser_controller.back()

    def stop_command(self):
        """Called when `self.stop_button` pressed.
        Stop execution."""
        self.layout_manager.display_stopped()
        self.timer.stop()
        self.visualiser_controller.stop()

        self.layout_manager.input_text.restart()
        self.code_text.setReadOnly(False)
        self.remove_command_highlights()

    def jump_command(self, direction):
        self.pause_command()
        try:
            steps = int(self.layout_manager.jump_input.text())
        except ValueError:
            self.display_error_text('Invalid jump steps')
        else:
            if direction == 1:
                self.visualiser_controller.jump_forwards(steps)
            else:
                self.visualiser_controller.jump_backwards(steps)

    def set_runspeed(self, *args):
        """Set the interval of the running timer. Also set the amount of steps the skip
        displaying if fast_mode is checked."""
        if self.layout_manager.speed_checkbox.isChecked():
            runspeed = 10
            self.steps_skip = self.layout_manager.speed_slider.value() // 5
        else:
            value = self.layout_manager.speed_slider.value() + 1
            runspeed = int(1000 / (value * value * .0098 + 1))
            self.steps_skip = 0
        self.timer.setInterval(runspeed)

    def run_signal(self):
        """Signal emmitted by timer. Step `self.steps_skip` without displaying, then
        step normally."""
        self.visualiser_controller.jump_forwards(self.steps_skip + 1)

    def remove_command_highlights(self):
        """Remove the command highlighting and set each character back to its
        original format."""
        for pos, format_ in self.prev_formats.items():
            self.text_cursor.setPosition(pos)
            self.text_cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
            self.text_cursor.setCharFormat(format_)
        self.prev_formats = {}

    def set_current_code_pointer(self, code_pointer, length=1):
        """Sets start index and length of the current code pointer."""
        self.current_code_pointer = (code_pointer, length)

    def highlight_current_code_pointer(self):
        """Remove the previous command highlighting and then add the new highlighting."""

        self.remove_command_highlights()

        code_pointer, length = self.current_code_pointer
        end = code_pointer + length

        # Can't have a negative index. Should only ever be a negative index if it
        # is the 0th instruction. If it is negative, set it to 0, but don't change
        # the end location
        if code_pointer < 0:
            code_pointer = 0

        self.text_cursor.setPosition(code_pointer)
        for pos in range(code_pointer, end):
            # Release the anchor
            self.text_cursor.movePosition(QTextCursor.NoMove, QTextCursor.MoveAnchor)
            # Move along one char
            self.text_cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
            # Store format of previous char
            char_format = self.text_cursor.charFormat()
            self.prev_formats[pos] = char_format
            # Merge new format
            self.text_cursor.mergeCharFormat(self.highlight_format)
        self.text_cursor.movePosition(QTextCursor.NoMove, QTextCursor.MoveAnchor)

    def set_output(self, text):
        """Set the current output to `text`"""
        self.layout_manager.output_text.setPlainText(text)
        self.layout_manager.output_text.verticalScrollBar().triggerAction(QScrollBar.SliderToMaximum)

    def next_input(self):
        """Return the next input from `self.input_text`"""
        return self.layout_manager.input_text.next_()

    def undo_input(self):
        """Undo the last input from `self.input_text`."""
        self.layout_manager.input_text.prev()

    def display_error_text(self, text):
        self.layout_manager.display_error_text(text)

    def hide_error_text(self):
        self.layout_manager.hide_error_text()
