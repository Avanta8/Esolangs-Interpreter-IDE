import enum
from collections import deque


class ErrorTypes(enum.Enum):
    UNMATCHED_CLOSE_PAREN = enum.auto()
    UNMATCHED_OPEN_PAREN = enum.auto()
    INVALID_TAPE_CELL = enum.auto()


class BFInterpreter:
    """Brainfuck interpreter."""

    def __init__(self, code, input_func=input, output_func=None, undo_input_func=None, maxlen=1_000_000):
        self.code = code
        self.input_func = input_func
        self.output_func = output_func
        self.undo_input_func = undo_input_func
        self.brackets = self.match_brackets(code)
        self.tape = [0]
        self.tape_pointer = 0
        self.code_pointer = -1
        self.output = ''
        self.instruction_count = 0
        self.past = deque(maxlen=maxlen)
        self.commands = {
            '[': self.open_loop,
            ']': self.close_loop,
            '>': self.increment_pointer,
            '<': self.decrement_pointer,
            '+': self.increment_cell,
            '-': self.decrement_cell,
            ',': self.accept_input,
            '.': self.add_output
        }

    def step(self):
        if self.code_pointer + 1 >= len(self.code):
            raise ExecutionEndedError

        self.past.append((self.code_pointer, self.tape_pointer,
                          self.tape[self.tape_pointer], len(self.output)))

        self.code_pointer += 1
        try:
            while self.current_instruction not in self.commands:
                self.code_pointer += 1
        except IndexError:
            self.code_pointer -= 1
            self.past.pop()
            raise ExecutionEndedError

        code_pointer = self.code_pointer
        self.instruction_count += 1

        self.commands[self.current_instruction]()

        return code_pointer

    def run(self):
        while True:
            try:
                self.step()
            except ExecutionEndedError:
                break
        return self.output

    def open_loop(self):
        if self.current_cell == 0:
            self.code_pointer = self.brackets[self.code_pointer]

    def close_loop(self):
        if self.current_cell != 0:
            self.code_pointer = self.brackets[self.code_pointer]

    def increment_pointer(self):
        self.tape_pointer += 1
        if self.tape_pointer >= len(self.tape):
            self.tape.append(0)

    def decrement_pointer(self):
        self.tape_pointer -= 1
        if self.tape_pointer < 0:
            error_location = self.code_pointer
            self.back()  # Reset back to was it was before
            raise ProgramRuntimeError(
                ErrorTypes.INVALID_TAPE_CELL, error_location)

    def increment_cell(self):
        self.tape[self.tape_pointer] = (self.tape[self.tape_pointer] + 1) % 256

    def decrement_cell(self):
        self.tape[self.tape_pointer] = (self.tape[self.tape_pointer] - 1) % 256

    def accept_input(self):
        input_ = self.input_func()
        if input_:
            self.tape[self.tape_pointer] = ord(input_) % 256
        else:
            self.back()  # Reset back to was it was before
            raise NoInputError

    def add_output(self):
        self.output += chr(self.current_cell)
        if self.output_func:
            self.output_func(self.output)

    def back(self):
        # undo_input = self.current_instruction == ','
        try:
            # self.code_pointer, self.tape_pointer, tape_val, output_len = self.past.pop()
            prev_info = self.past.pop()
        except IndexError:
            raise NoPreviousExecutionError

        undo_input = self.current_instruction == ','
        if undo_input and self.undo_input_func is not None:
            self.undo_input_func()

        self.code_pointer, self.tape_pointer, tape_val, output_len = prev_info

        if output_len != len(self.output):
            self.output = self.output[:-1]
            self.output_func(self.output)
        self.tape[self.tape_pointer] = tape_val
        self.instruction_count -= 1
        return self.code_pointer

    @property
    def current_cell(self):
        return self.tape[self.tape_pointer]

    @property
    def current_instruction(self):
        return self.code[self.code_pointer]

    @staticmethod
    def match_brackets(code):
        stack = deque()  # deque is faster than list
        brackets = {}
        for i, char in enumerate(code):
            if char == '[':
                stack.append(i)
            elif char == ']':
                try:
                    match = stack.pop()
                except IndexError:
                    raise ProgramSyntaxError(
                        ErrorTypes.UNMATCHED_CLOSE_PAREN, i)
                brackets[match] = i
                brackets[i] = match
        if stack:
            raise ProgramSyntaxError(
                ErrorTypes.UNMATCHED_OPEN_PAREN, stack[-1])
        return brackets


class FastBrainfuckInterpreter:
    def __init__(self, code, input_func=input, output_func=None):
        self.commands, self.brackets = self._compile(code)
        self.input_func = input_func
        self.output_func = output_func
        self.tape = [0] * 40000
        self.command_pointer = 0
        self.tape_pointer = 0
        self.output = []

    def run(self):
        self.running = True
        while self.running:
            command, arg = self.commands[self.command_pointer]
            command(arg)
            self.command_pointer += 1
        return ''.join(self.output)

    def open_loop(self, arg):
        if self.current_cell == 0:
            self.command_pointer = self.brackets[self.command_pointer]

    def close_loop(self, arg):
        if self.current_cell != 0:
            self.command_pointer = self.brackets[self.command_pointer]

    def pointer_op(self, times):
        self.tape_pointer += times
        if self.tape_pointer < 0:
            raise ProgramRuntimeError(ErrorTypes.INVALID_TAPE_CELL)

    def cell_op(self, times):
        self.tape[self.tape_pointer] = (
            self.tape[self.tape_pointer] + times) % 256

    def accept_input(self, arg):
        self.tape[self.tape_pointer] = ord(self.input_func()) % 256

    def add_output(self, arg):
        self.output.append(chr(self.current_cell))
        if self.output_func:
            self.output_func(chr(self.current_cell))

    def stop(self, arg):
        self.running = False

    @property
    def current_cell(self):
        return self.tape[self.tape_pointer]

    def _compile(self, code):
        command_funcs = {
            '[': self.open_loop,
            ']': self.close_loop,
            '>': self.pointer_op,
            '<': self.pointer_op,
            '+': self.cell_op,
            '-': self.cell_op,
            ',': self.accept_input,
            '.': self.add_output
        }

        pointer_ops = set('<>')
        cell_ops = set('+-')

        bracket_stack = []
        brackets = {}
        final_commands = []
        code_len = len(code)
        i = 0

        while i < code_len:
            char = code[i]
            arg = None

            if char == '[':
                bracket_stack.append(len(final_commands))
            elif char == ']':
                try:
                    match = bracket_stack.pop()
                except IndexError:
                    raise ProgramSyntaxError(
                        ErrorTypes.UNMATCHED_CLOSE_PAREN, i)
                current = len(final_commands)
                brackets[match] = current
                brackets[current] = match

            if char in pointer_ops:
                arg = 0
                while i < code_len and code[i] in pointer_ops:
                    arg += 1 if code[i] == '>' else -1
                    i += 1
            elif char in cell_ops:
                arg = 0
                while i < code_len and code[i] in cell_ops:
                    arg += 1 if code[i] == '+' else -1
                    i += 1
            else:
                i += 1

            if char in command_funcs:
                final_commands.append((command_funcs[char], arg))

        final_commands.append((self.stop, None))

        if bracket_stack:
            raise ProgramSyntaxError(
                ErrorTypes.UNMATCHED_OPEN_PAREN)
        return final_commands, brackets


class InterpreterError(Exception):
    """Base class for exceptions to do with an interpreter."""


class ExecutionEndedError(InterpreterError):
    """Error raised when program has ended but `Interpreter.step` is still called"""


class NoPreviousExecutionError(InterpreterError):
    """Error raised when `Interpreter.back` is called but it is the first instruction being processed"""


class NoInputError(InterpreterError):
    """Error raised when no input returned from `Interpreter.input_func`"""


class ProgramError(InterpreterError):
    """Error raised when there is something wrong with a program.

    Attributes:
        error -- Source of error (default to None).
        location -- Location of error (default to None).
        message -- Optional mesage (default to None)."""

    def __init__(self, error=None, location=None, message=None):
        self.error = error
        self.location = location
        self.message = message


class ProgramSyntaxError(ProgramError):
    """Error raised when there is a syntax error with the source code of a program."""


class ProgramRuntimeError(ProgramError):
    """Error raised when there is a error while the program is running. (Does not include missing input.)"""


if __name__ == '__main__':
    print(issubclass(ProgramSyntaxError, InterpreterError))
