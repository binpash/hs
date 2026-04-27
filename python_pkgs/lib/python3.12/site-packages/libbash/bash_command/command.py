from __future__ import annotations

from typing import Union, Optional
from .. import ctypes_bash_command as c_bash
import ctypes
from .flags import *
from .util import *


class WordDesc:
    """
    describes a word
    """

    word: bytes  # the word
    flags: list[WordDescFlag]

    def __init__(self, word: c_bash.word_desc):
        """
        :param word: the word description
        """
        self.word = word.word
        self.flags = word_desc_flag_list_from_int(word.flags)

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other word description
        :return: whether the two word descriptions are equal, the
        flags lists need not be in the same order
        """
        if not isinstance(other, WordDesc):
            return False
        if self.word != other.word:
            return False
        if not list_same_elements(self.flags, other.flags):
            return False
        return True

    def _to_json(self) -> dict[str, Union[int, str]]:
        """
        :return: a dictionary representation of the word description
        """
        return {
            "word": self.word.decode("utf-8", errors="replace"),
            "flags": [x._to_json() for x in self.flags],
        }

    def _to_ctypes(self) -> c_bash.word_desc:
        """
        :return: the c word_desc struct representation of this word description
        """
        c_word_desc = c_bash.word_desc()
        c_word_desc.word = self.word
        c_word_desc.flags = int_from_word_desc_flag_list(self.flags)
        return c_word_desc


def word_desc_list_from_word_list(
    word_list: ctypes._Pointer[c_bash.word_list],
) -> list[WordDesc]:
    """
    :param word_list: the word list
    :return: a list of word descriptions
    """
    word_desc_list = []
    while word_list:
        word_desc_list.append(WordDesc(word_list.contents.word.contents))
        word_list = word_list.contents.next
    return word_desc_list


def c_word_list_from_word_desc_list(
    word_desc_list: list[WordDesc],
) -> ctypes._Pointer[c_bash.word_list]:
    """
    :param word_desc_list: the list of word descriptions
    :return: a pointer to the first word description in the list
    """
    if len(word_desc_list) == 0:
        return ctypes.POINTER(c_bash.word_list)()
    c_word_list = c_bash.word_list()
    c_word_list.word = ctypes.POINTER(c_bash.word_desc)(word_desc_list[0]._to_ctypes())
    c_word_list.next = c_word_list_from_word_desc_list(word_desc_list[1:])
    return ctypes.POINTER(c_bash.word_list)(c_word_list)


class RedirecteeUnion:
    """
    a redirectee, either a file descriptor or a file name
    """

    # use only if R_DUPLICATING_INPUT or R_DUPLICATING_OUTPUT
    dest: Optional[int]
    # use otherwise
    filename: Optional[WordDesc]

    def __init__(self, dest: Optional[int], filename: Optional[c_bash.word_desc]):
        """
        :param dest: the destination file descriptor or None
        :param filename: the word description or None
        """
        self.dest = dest if dest is not None else None
        self.filename = WordDesc(filename) if filename else None

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other redirectee union
        :return: whether the two redirectee unions are equal
        """
        if not isinstance(other, RedirecteeUnion):
            return False
        if self.dest != other.dest:
            return False
        if self.filename != other.filename:
            return False
        return True

    def _to_json(self) -> dict[str, Union[int, str, dict, list]]:
        """
        :return: a dictionary representation of the redirectee union
        """
        if self.dest is not None:
            return {"dest": self.dest}
        elif self.filename is not None:
            return {"filename": self.filename._to_json()}
        else:
            raise Exception("invalid redirectee")

    def _to_ctypes(self) -> c_bash.REDIRECTEE:
        """
        :return: the c redirectee union struct representation of this redirectee union
        """
        c_redirectee = c_bash.REDIRECTEE()
        if self.dest is not None:
            c_redirectee.dest = self.dest
        elif self.filename is not None:
            c_redirectee.filename = self.filename._to_ctypes()
        else:
            raise Exception("invalid redirectee")
        return c_redirectee


class Redirect:
    """
    describes a redirection such as >, >>, <, <<
    """

    redirector: RedirecteeUnion  # the thing being redirected
    rflags: list[RedirectFlag]  # flags for redirection
    flags: list[OFlag]
    instruction: RInstruction  # the type of redirection
    redirectee: RedirecteeUnion  # the thing being redirected to
    here_doc_eof: Optional[str]  # the word that appeared in the << operator?

    def __init__(self, redirect: c_bash.redirect):
        """
        :param redirect: the redirect struct
        """
        self.rflags = redirect_flag_list_from_rflags(redirect.rflags)
        self.flags = oflag_list_from_int(redirect.flags)
        self.instruction = RInstruction(redirect.instruction)
        self.here_doc_eof = (
            redirect.here_doc_eof.decode("utf-8")
            if redirect.here_doc_eof is not None
            else None
        )
        if RedirectFlag.REDIR_VARASSIGN in self.rflags:
            self.redirector = RedirecteeUnion(
                None, redirect.redirector.filename.contents
            )
        else:
            self.redirector = RedirecteeUnion(redirect.redirector.dest, None)
        if (
            self.instruction == RInstruction.R_DUPLICATING_INPUT
            or self.instruction == RInstruction.R_DUPLICATING_OUTPUT
            or self.instruction == RInstruction.R_CLOSE_THIS
            or self.instruction == RInstruction.R_MOVE_INPUT
            or self.instruction == RInstruction.R_MOVE_OUTPUT
        ):
            self.redirectee = RedirecteeUnion(redirect.redirectee.dest, None)
        else:
            self.redirectee = RedirecteeUnion(
                None, redirect.redirectee.filename.contents
            )

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other redirect struct
        :return: whether the two redirect structs are equal,
        the flags lists need not be in the same order
        """
        if not isinstance(other, Redirect):
            return False
        if not list_same_elements(self.rflags, other.rflags):
            return False
        if not list_same_elements(self.flags, other.flags):
            return False
        if self.instruction != other.instruction:
            return False
        if self.here_doc_eof != other.here_doc_eof:
            return False
        if self.redirector != other.redirector:
            return False
        if self.redirectee != other.redirectee:
            return False
        return True

    def _to_json(self) -> dict[str, Union[int, str, dict, list, None]]:
        """
        :return: a dictionary representation of the redirect struct
        """
        return {
            "redirector": self.redirector._to_json(),
            "rflags": [x._to_json() for x in self.rflags],
            "flags": [x._to_json() for x in self.flags],
            "instruction": self.instruction._to_json(),
            "redirectee": self.redirectee._to_json(),
            "here_doc_eof": self.here_doc_eof,
        }

    def _to_ctypes(self) -> c_bash.redirect:
        """
        :return: the c redirect struct representation of this redirect
        """
        c_redirect = c_bash.redirect()
        c_redirect.redirector = c_bash.REDIRECTEE()
        if self.redirector.dest is not None:
            c_redirect.redirector.dest = self.redirector.dest
        elif self.redirector.filename is not None:
            c_redirect.redirector.filename = ctypes.POINTER(c_bash.word_desc)(
                self.redirector.filename._to_ctypes()
            )
        else:
            raise Exception("invalid redirector")
        c_redirect.rflags = int_from_redirect_flag_list(self.rflags)
        c_redirect.flags = int_from_oflag_list(self.flags)
        c_redirect.instruction = self.instruction.value
        c_redirect.redirectee = c_bash.REDIRECTEE()
        if self.redirectee.dest is not None:
            c_redirect.redirectee.dest = self.redirectee.dest
        elif self.redirectee.filename is not None:
            c_redirect.redirectee.filename = ctypes.POINTER(c_bash.word_desc)(
                self.redirectee.filename._to_ctypes()
            )
        else:
            raise Exception("invalid redirectee")
        c_redirect.here_doc_eof = (
            self.here_doc_eof.encode("utf-8") if self.here_doc_eof is not None else None
        )
        return c_redirect


def redirect_list_from_redirect(
    redirect: ctypes._Pointer[c_bash.redirect],
) -> list[Redirect]:
    """
    :param redirect: the redirect list
    :return: a list of redirects
    """
    redirect_list = []
    while redirect:
        redirect_list.append(Redirect(redirect.contents))
        redirect = redirect.contents.next
    return redirect_list


def c_redirect_list_from_redirect_list(
    redirect_list: list[Redirect],
) -> ctypes._Pointer[c_bash.redirect]:
    """
    :param redirect_list: the list of redirects
    :return: a pointer to the first redirect in the list
    """
    if len(redirect_list) == 0:
        return ctypes.POINTER(c_bash.redirect)()
    c_redirect = redirect_list[0]._to_ctypes()
    c_redirect.next = c_redirect_list_from_redirect_list(redirect_list[1:])
    return ctypes.POINTER(c_bash.redirect)(c_redirect)


def c_redirect_from_redirect_list(
    redirect_list: list[Redirect],
) -> ctypes._Pointer[c_bash.redirect]:
    """
    :param redirect_list: the list of redirects
    :return: a pointer to the first redirect in the list
    """
    if len(redirect_list) == 0:
        return ctypes.POINTER(c_bash.redirect)()
    c_redirect = redirect_list[0]._to_ctypes()
    c_redirect.next = c_redirect_from_redirect_list(redirect_list[1:])
    return ctypes.POINTER(c_bash.redirect)(c_redirect)


class ForCom:
    """
    a for command class
    """

    flags: list[CommandFlag]
    line: int  # line number the command is on?
    name: WordDesc  # the variable name to get mapped over?
    map_list: list[WordDesc]  # the list of words to map over
    action: "Command"  # the action to take for each word in the map list

    def __init__(self, for_c: c_bash.for_com):
        """
        :param for_c: the for command struct

        """
        self.flags = command_flag_list_from_int(for_c.flags)
        self.line = for_c.line
        self.name = WordDesc(for_c.name.contents)
        self.map_list = word_desc_list_from_word_list(for_c.map_list)
        self.action = Command(for_c.action.contents)

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other for command
        :return: whether the two for commands are equal, the
        flags lists need not be in the same order
        """
        if not isinstance(other, ForCom):
            return False
        if not list_same_elements(self.flags, other.flags):
            return False
        if self.name != other.name:
            return False
        if not list_same_elements(self.map_list, other.map_list):
            return False
        if self.action != other.action:
            return False
        return True

    def _to_json(self) -> dict[str, Union[int, str, dict, list]]:
        """
        :return: a dictionary representation of the for command
        """
        return {
            "flags": self.flags,
            "line": self.line,
            "name": self.name._to_json(),
            "map_list": [x._to_json() for x in self.map_list],
            "action": self.action._to_json(),
        }

    def _to_ctypes(self) -> c_bash.for_com:
        """
        :return: the c for_com struct representation of this for command
        """
        c_for = c_bash.for_com()
        c_for.flags = int_from_command_flag_list(self.flags)
        c_for.line = self.line
        c_for.name = ctypes.POINTER(c_bash.word_desc)(self.name._to_ctypes())
        c_for.map_list = c_word_list_from_word_desc_list(self.map_list)
        c_for.action = ctypes.POINTER(c_bash.command)(self.action._to_ctypes())
        return c_for


class Pattern:
    """
    represents a pattern in a case command
    """

    patterns: list[WordDesc]  # the list of patterns to match against
    action: Optional["Command"]  # the action to take if the pattern matches
    flags: list[PatternFlag]

    def __init__(self, pattern: c_bash.pattern_list):
        """
        :param pattern: the pattern struct
        """
        self.patterns = word_desc_list_from_word_list(pattern.patterns)
        self.action = Command(pattern.action.contents) if pattern.action else None
        self.flags = pattern_flag_list_from_int(pattern.flags)

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other pattern
        :return: whether the two patterns are equal, the
        flags lists need not be in the same order
        """
        if not isinstance(other, Pattern):
            return False
        if not list_same_elements(self.patterns, other.patterns):
            return False
        if self.action != other.action:
            return False
        if not list_same_elements(self.flags, other.flags):
            return False
        return True

    def _to_json(self) -> dict[str, Union[int, dict, list, None]]:
        """
        :return: a dictionary representation of the pattern
        """
        return {
            "patterns": [x._to_json() for x in self.patterns],
            "action": self.action._to_json() if self.action is not None else None,
            "flags": self.flags,
        }

    def _to_ctypes(self) -> c_bash.pattern_list:
        """
        :return: the c pattern_list struct representation of this pattern
        """
        c_pattern = c_bash.pattern_list()
        c_pattern.patterns = c_word_list_from_word_desc_list(self.patterns)
        c_pattern.action = (
            ctypes.POINTER(c_bash.command)(self.action._to_ctypes())
            if self.action is not None
            else None
        )
        c_pattern.flags = int_from_pattern_flag_list(self.flags)
        return c_pattern


def pattern_list_from_pattern_list(
    pattern: ctypes._Pointer[c_bash.pattern_list],
) -> list[Pattern]:
    """
    :param pattern: the pattern list, as they are represented in c
    :return: a list of patterns as they are represented in python
    """
    pattern_list = []
    while pattern:
        pattern_list.append(Pattern(pattern.contents))
        pattern = pattern.contents.next
    return pattern_list


def c_pattern_list_from_pattern_list(
    pattern_list: list[Pattern],
) -> ctypes._Pointer[c_bash.pattern_list]:
    """
    :param pattern_list: the list of patterns, as they are represented in python
    :return: a pointer to the first pattern in the list, as they are represented in c
    """
    if len(pattern_list) == 0:
        return ctypes.POINTER(c_bash.pattern_list)()
    c_pattern = pattern_list[0]._to_ctypes()
    c_pattern.next = c_pattern_list_from_pattern_list(pattern_list[1:])
    return ctypes.POINTER(c_bash.pattern_list)(c_pattern)


class CaseCom:
    """
    a case command class
    """

    flags: list[CommandFlag]
    line: int  # line number the command is on?
    word: WordDesc  # the thing to match against
    clauses: list[Pattern]  # the list of patterns to match against

    def __init__(self, case_c: c_bash.case_com):
        """
        :param case_c: the case command struct
        """
        self.flags = command_flag_list_from_int(case_c.flags)
        self.line = case_c.line
        self.word = WordDesc(case_c.word.contents)
        self.clauses = pattern_list_from_pattern_list(case_c.clauses)

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other case command
        :return: whether the two case commands are equal, the
        flags lists need not be in the same order
        """
        if not isinstance(other, CaseCom):
            return False
        if not list_same_elements(self.flags, other.flags):
            return False
        if self.word != other.word:
            return False
        if not list_same_elements(self.clauses, other.clauses):
            return False
        return True

    def _to_json(self) -> dict[str, Union[int, str, dict, list]]:
        """
        :return: a dictionary representation of the case command
        """
        return {
            "flags": self.flags,
            "line": self.line,
            "word": self.word._to_json(),
            "clauses": [x._to_json() for x in self.clauses],
        }

    def _to_ctypes(self) -> c_bash.case_com:
        """
        :return: the c case_com struct representation of this case command
        """
        c_case = c_bash.case_com()
        c_case.flags = int_from_command_flag_list(self.flags)
        c_case.line = self.line
        c_case.word = ctypes.POINTER(c_bash.word_desc)(self.word._to_ctypes())
        c_case.clauses = c_pattern_list_from_pattern_list(self.clauses)
        return c_case


class WhileCom:
    """
    a while command class
    """

    flags: list[CommandFlag]
    test: "Command"  # the thing to test
    action: "Command"  # the action to take while the test is true

    def __init__(self, while_c: c_bash.while_com):
        """
        :param while_c: the while command struct
        """
        self.flags = command_flag_list_from_int(while_c.flags)
        self.test = Command(while_c.test.contents)
        self.action = Command(while_c.action.contents)

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other while command
        :return: whether the two while commands are equal, the
        flags lists need not be in the same order
        """
        if not isinstance(other, WhileCom):
            return False
        if not list_same_elements(self.flags, other.flags):
            return False
        if self.test != other.test:
            return False
        if self.action != other.action:
            return False
        return True

    def _to_json(self) -> dict[str, Union[int, str, dict, list]]:
        """
        :return: a dictionary representation of the while command
        """
        return {
            "flags": self.flags,
            "test": self.test._to_json(),
            "action": self.action._to_json(),
        }

    def _to_ctypes(self) -> c_bash.while_com:
        """
        :return: the c while_com struct representation of this while command
        """
        c_while = c_bash.while_com()
        c_while.flags = int_from_command_flag_list(self.flags)
        c_while.test = ctypes.POINTER(c_bash.command)(self.test._to_ctypes())
        c_while.action = ctypes.POINTER(c_bash.command)(self.action._to_ctypes())
        return c_while


class IfCom:
    """
    an if command class
    """

    flags: list[CommandFlag]
    test: "Command"  # the thing to test
    true_case: "Command"  # the action to take if the test is true
    false_case: Optional["Command"]  # the action to take if the test is false

    def __init__(self, if_c: c_bash.if_com):
        """
        :param if_c: the if command struct
        """
        self.flags = command_flag_list_from_int(if_c.flags)
        self.test = Command(if_c.test.contents)
        self.true_case = Command(if_c.true_case.contents)
        self.false_case = Command(if_c.false_case.contents) if if_c.false_case else None

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other if command
        """
        if not isinstance(other, IfCom):
            return False
        if not list_same_elements(self.flags, other.flags):
            return False
        if self.test != other.test:
            return False
        if self.true_case != other.true_case:
            return False
        if self.false_case != other.false_case:
            return False
        return True

    def _to_json(self) -> dict[str, Union[int, str, dict, list, None]]:
        """
        :return: a dictionary representation of the if command
        """
        return {
            "flags": self.flags,
            "test": self.test._to_json(),
            "true_case": self.true_case._to_json(),
            "false_case": (
                self.false_case._to_json() if self.false_case is not None else None
            ),
        }

    def _to_ctypes(self) -> c_bash.if_com:
        """
        :return: the c if_com struct representation of this if command
        """
        c_if = c_bash.if_com()
        c_if.flags = int_from_command_flag_list(self.flags)
        c_if.test = ctypes.POINTER(c_bash.command)(self.test._to_ctypes())
        c_if.true_case = ctypes.POINTER(c_bash.command)(self.true_case._to_ctypes())
        c_if.false_case = (
            ctypes.POINTER(c_bash.command)(self.false_case._to_ctypes())
            if self.false_case is not None
            else None
        )
        return c_if


class Connection:
    """
    represents connections
    """

    flags: list[CommandFlag]
    first: "Command"  # the first command to run
    second: Optional["Command"]  # the second command to run
    connector: ConnectionType  # the type of connection

    def __init__(self, connection: c_bash.connection):
        """
        :param connection: the connection struct
        """
        self.flags = command_flag_list_from_int(connection.ignore)
        self.first = Command(connection.first.contents)
        self.second = Command(connection.second.contents) if connection.second else None
        self.connector = ConnectionType(connection.connector)

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other connection
        :return: whether the two connections are equal
        """
        if not isinstance(other, Connection):
            return False
        if not list_same_elements(self.flags, other.flags):
            return False
        if self.first != other.first:
            return False
        if self.second != other.second:
            return False
        if self.connector != other.connector:
            return False
        return True

    def _to_json(self) -> dict[str, Union[int, str, dict, list, None]]:
        """
        :return: a dictionary representation of the connection
        """
        return {
            "flags": [x._to_json() for x in self.flags],
            "first": self.first._to_json(),
            "second": self.second._to_json() if self.second is not None else None,
            "connector": self.connector._to_json(),  # todo: figure out what this int means
        }

    def _to_ctypes(self) -> c_bash.connection:
        """
        :return: the c connection struct representation of this connection
        """
        c_connection = c_bash.connection()
        c_connection.ignore = int_from_command_flag_list(self.flags)
        c_connection.first = ctypes.POINTER(c_bash.command)(self.first._to_ctypes())
        c_connection.second = (
            ctypes.POINTER(c_bash.command)(self.second._to_ctypes())
            if self.second is not None
            else None
        )
        c_connection.connector = self.connector.value
        return c_connection


class SimpleCom:
    """
    a simple command class
    """

    flags: list[CommandFlag]
    line: int  # line number the command is on
    words: list[WordDesc]  # program name, arguments, variable assignments, etc
    redirects: list[Redirect]  # redirections

    def __init__(self, simple: c_bash.simple_com):
        """
        :param simple: the simple command struct
        """
        self.flags = command_flag_list_from_int(simple.flags)
        self.line = simple.line
        self.words = word_desc_list_from_word_list(simple.words)
        self.redirects = redirect_list_from_redirect(simple.redirects)

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other simple command
        :return: whether the two simple commands are equal, the
        """
        if not isinstance(other, SimpleCom):
            return False
        if not list_same_elements(self.flags, other.flags):
            return False
        if not list_same_elements(self.words, other.words):
            return False
        if not list_same_elements(self.redirects, other.redirects):
            return False
        return True

    def _to_json(self) -> dict[str, Union[int, str, dict, list]]:
        """
        :return: a dictionary representation of the simple command
        """
        return {
            "flags": [x._to_json() for x in self.flags],
            "line": self.line,
            "words": [x._to_json() for x in self.words],
            "redirects": [x._to_json() for x in self.redirects],
        }

    def _to_ctypes(self) -> c_bash.simple_com:
        """
        :return: the c simple_com struct representation of this simple command
        """
        c_simple = c_bash.simple_com()
        c_simple.flags = int_from_command_flag_list(self.flags)
        c_simple.line = self.line
        c_simple.words = c_word_list_from_word_desc_list(self.words)
        c_simple.redirects = c_redirect_list_from_redirect_list(self.redirects)
        return c_simple


class FunctionDef:
    """
    for function definitions
    """

    flags: list[CommandFlag]
    line: int  # line number the command is on
    name: WordDesc  # the name of the function
    command: "Command"  # the execution tree for the function
    source_file: Optional[str]  # the file the function was defined in, if any

    def __init__(self, function: c_bash.function_def):
        """
        :param function: the function_def struct
        """
        self.flags = command_flag_list_from_int(function.flags)
        self.line = function.line
        self.name = WordDesc(function.name.contents)
        self.command = Command(function.command.contents)
        self.source_file = (
            function.source_file.decode("utf-8") if function.source_file else None
        )

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other function definition
        :return: whether the two function definitions are equal, the
        flags lists need not be in the same order
        """
        if not isinstance(other, FunctionDef):
            return False
        if not list_same_elements(self.flags, other.flags):
            return False
        if self.name != other.name:
            return False
        if self.command != other.command:
            return False
        # if the asts are coming from different files, they should still be considered equal
        # if self.source_file != other.source_file:
        #     return False
        return True

    def _to_json(self) -> dict[str, Union[int, str, dict, list, None]]:
        """
        :return: a dictionary representation of the function definition
        """
        return {
            "flags": [x._to_json() for x in self.flags],
            "line": self.line,
            "name": self.name._to_json(),
            "command": self.command._to_json(),
            "source_file": self.source_file if self.source_file is not None else None,
        }

    def _to_ctypes(self) -> c_bash.function_def:
        """
        :return: the c function_def struct representation of this function definition
        """
        c_function = c_bash.function_def()
        c_function.flags = int_from_command_flag_list(self.flags)
        c_function.line = self.line
        c_function.name = ctypes.POINTER(c_bash.word_desc)(self.name._to_ctypes())
        c_function.command = ctypes.POINTER(c_bash.command)(self.command._to_ctypes())
        c_function.source_file = (
            self.source_file.encode("utf-8") if self.source_file is not None else None
        )
        return c_function


class GroupCom:
    """
    group commands allow pipes and redirections to be applied to a group of commands
    """

    flags: list[CommandFlag]
    command: "Command"  # the command to run

    def __init__(self, group: c_bash.group_com):
        """
        :param group: the group command struct
        """
        self.flags = command_flag_list_from_int(group.ignore)
        self.command = Command(group.command.contents)

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other group command
        :return: whether the two group commands are equal
        """
        if not isinstance(other, GroupCom):
            return False
        if not list_same_elements(self.flags, other.flags):
            return False
        if self.command != other.command:
            return False
        return True

    def _to_json(self) -> dict[str, Union[int, str, dict, list]]:
        """
        :return: a dictionary representation of the group command
        """
        return {
            "line": [x._to_json() for x in self.flags],
            "command": self.command._to_json(),
        }

    def _to_ctypes(self) -> c_bash.group_com:
        """
        :return: the c group_com struct representation of this group command
        """
        c_group = c_bash.group_com()
        c_group.ignore = int_from_command_flag_list(self.flags)
        c_group.command = ctypes.POINTER(c_bash.command)(self.command._to_ctypes())
        return c_group


class SelectCom:
    """
    the select command is like a for loop but with a menu
    """

    flags: list[CommandFlag]
    line: int  # line number the command is on
    name: WordDesc  # the name of the variable?
    map_list: list[WordDesc]  # the list of words to map over
    action: "Command"  # the action to take for each word in the map list, during execution name is bound to member of map_list

    def __init__(self, select: c_bash.select_com):
        """
        :param select: the select command struct
        """
        self.flags = command_flag_list_from_int(select.flags)
        self.line = select.line
        self.name = WordDesc(select.name.contents)
        self.map_list = word_desc_list_from_word_list(select.map_list)
        self.action = Command(select.action.contents)

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other select command
        :return: whether the two select commands are equal, the
        lists need not be in the same order
        """
        if not isinstance(other, SelectCom):
            return False
        if not list_same_elements(self.flags, other.flags):
            return False
        if self.name != other.name:
            return False
        if not list_same_elements(self.map_list, other.map_list):
            return False
        if self.action != other.action:
            return False
        return True

    def _to_json(self) -> dict[str, Union[int, str, dict, list]]:
        """
        :return: a dictionary representation of the select command
        """
        return {
            "flags": [x._to_json() for x in self.flags],
            "line": self.line,
            "name": self.name._to_json(),
            "map_list": [x._to_json() for x in self.map_list],
            "action": self.action._to_json(),
        }

    def _to_ctypes(self) -> c_bash.select_com:
        """
        :return: the c select_com struct representation of this select command
        """
        c_select = c_bash.select_com()
        c_select.flags = int_from_command_flag_list(self.flags)
        c_select.line = self.line
        c_select.name = ctypes.POINTER(c_bash.word_desc)(self.name._to_ctypes())
        c_select.map_list = c_word_list_from_word_desc_list(self.map_list)
        c_select.action = ctypes.POINTER(c_bash.command)(self.action._to_ctypes())
        return c_select


class ArithCom:
    """
    arithmetic expression ((...))
    """

    flags: list[CommandFlag]
    line: int  # line number the command is on
    exp: list[WordDesc]  # the expression to evaluate

    def __init__(self, arith: c_bash.arith_com):
        """
        :param arith: the arith command struct
        """
        self.flags = command_flag_list_from_int(arith.flags)
        self.line = arith.line
        self.exp = word_desc_list_from_word_list(arith.exp)

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other arith command
        :return: whether the two arith commands are equal, the
        flags lists need not be in the same order
        """
        if not isinstance(other, ArithCom):
            return False
        if not list_same_elements(self.flags, other.flags):
            return False
        if not list_same_elements(self.exp, other.exp):
            return False
        return True

    def _to_json(self) -> dict[str, Union[int, str, dict, list]]:
        """
        :return: a dictionary representation of the arith command
        """
        return {
            "flags": [x._to_json() for x in self.flags],
            "line": self.line,
            "exp": [x._to_json() for x in self.exp],
        }

    def _to_ctypes(self) -> c_bash.arith_com:
        """
        :return: the c arith_com struct representation of this arith command
        """
        c_arith = c_bash.arith_com()
        c_arith.flags = int_from_command_flag_list(self.flags)
        c_arith.line = self.line
        c_arith.exp = c_word_list_from_word_desc_list(self.exp)
        return c_arith


class CondCom:
    """
    conditional expression [[...]]
    """

    flags: list[CommandFlag]
    line: int  # line number the command is on
    type: CondTypeEnum  # the type of conditional expression
    op: Optional[WordDesc]  # binary tree vibe?
    left: Optional["CondCom"]  # the left side of the expression
    right: Optional["CondCom"]  # the right side of the expression

    def __init__(self, cond: c_bash.cond_com):
        """
        :param cond: the cond command struct
        """
        self.flags = command_flag_list_from_int(cond.flags)
        self.line = cond.line
        self.type = CondTypeEnum(cond.type)
        self.op = WordDesc(cond.op.contents) if cond.op else None
        self.left = CondCom(cond.left.contents) if cond.left else None
        self.right = CondCom(cond.right.contents) if cond.right else None

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other cond command
        :return: whether the two cond commands are equal, the
        flags lists need not be in the same order
        """
        if not isinstance(other, CondCom):
            return False
        if not list_same_elements(self.flags, other.flags):
            return False
        if self.type != other.type:
            return False
        if self.op != other.op:
            return False
        if self.left != other.left:
            return False
        if self.right != other.right:
            return False
        return True

    def _to_json(self) -> dict[str, Union[int, str, dict, list, None]]:
        """
        :return: a dictionary representation of the cond command
        """
        return {
            "flags": [x._to_json() for x in self.flags],
            "line": self.line,
            "cond_type": self.type._to_json(),
            "op": self.op._to_json() if self.op is not None else None,
            "left": self.left._to_json() if self.left is not None else None,
            "right": self.right._to_json() if self.right is not None else None,
        }

    def _to_ctypes(self) -> c_bash.cond_com:
        """
        :return: the c cond_com struct representation of this cond command
        """
        c_cond = c_bash.cond_com()
        c_cond.flags = int_from_command_flag_list(self.flags)
        c_cond.line = self.line
        c_cond.type = self.type.value
        c_cond.op = (
            ctypes.POINTER(c_bash.word_desc)(self.op._to_ctypes())
            if self.op is not None
            else None
        )
        c_cond.left = (
            ctypes.POINTER(c_bash.cond_com)(self.left._to_ctypes())
            if self.left is not None
            else None
        )
        c_cond.right = (
            ctypes.POINTER(c_bash.cond_com)(self.right._to_ctypes())
            if self.right is not None
            else None
        )
        return c_cond


class ArithForCom:
    """
    a c-style for loop ((init; test; step)) action
    """

    flags: list[CommandFlag]
    line: int  # line number the command is on
    init: list[WordDesc]  # the initial values of the variables
    test: list[WordDesc]  # the test to perform
    step: list[WordDesc]  # the step to take
    action: "Command"  # the action to take for each iteration

    def __init__(self, arith_for: c_bash.arith_for_com):
        """
        :param arith_for: the arith_for command struct
        """
        self.flags = command_flag_list_from_int(arith_for.flags)
        self.line = arith_for.line
        self.init = word_desc_list_from_word_list(arith_for.init)
        self.test = word_desc_list_from_word_list(arith_for.test)
        self.step = word_desc_list_from_word_list(arith_for.step)
        self.action = Command(arith_for.action.contents)

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other arith_for command
        :return: whether the two arith_for commands are equal, the
        flags lists need not be in the same order
        """
        if not isinstance(other, ArithForCom):
            return False
        if not list_same_elements(self.flags, other.flags):
            return False
        if self.init != other.init:
            return False
        if self.test != other.test:
            return False
        if self.step != other.step:
            return False
        if self.action != other.action:
            return False
        return True

    def _to_json(self) -> dict[str, Union[int, str, dict, list]]:
        """
        :return: a dictionary representation of the arith_for command
        """
        return {
            "flags": [x._to_json() for x in self.flags],
            "line": self.line,
            "init": [x._to_json() for x in self.init],
            "test": [x._to_json() for x in self.test],
            "step": [x._to_json() for x in self.step],
            "action": self.action._to_json(),
        }

    def _to_ctypes(self) -> c_bash.arith_for_com:
        """
        :return: the c arith_for_com struct representation of this arith_for command
        """
        c_arith_for = c_bash.arith_for_com()
        c_arith_for.flags = int_from_command_flag_list(self.flags)
        c_arith_for.line = self.line
        c_arith_for.init = c_word_list_from_word_desc_list(self.init)
        c_arith_for.test = c_word_list_from_word_desc_list(self.test)
        c_arith_for.step = c_word_list_from_word_desc_list(self.step)
        c_arith_for.action = ctypes.POINTER(c_bash.command)(self.action._to_ctypes())
        return c_arith_for


class SubshellCom:
    """
    a subshell command
    """

    flags: list[CommandFlag]  # unclear flag type
    line: int  # line number the command is on
    command: "Command"  # the command to run in the subshell

    def __init__(self, subshell: c_bash.subshell_com):
        """
        :param subshell: the subshell command struct
        """
        self.flags = command_flag_list_from_int(subshell.flags)
        self.line = subshell.line
        self.command = Command(subshell.command.contents)

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other subshell command
        :return: whether the two subshell commands are equal, the
        """
        if not isinstance(other, SubshellCom):
            return False
        if not list_same_elements(self.flags, other.flags):
            return False
        if self.command != other.command:
            return False
        return True

    def _to_json(self) -> dict[str, Union[int, str, dict, list]]:
        """
        :return: a dictionary representation of the subshell command
        """
        return {
            "flags": [x._to_json() for x in self.flags],
            "line": self.line,
            "command": self.command._to_json(),
        }

    def _to_ctypes(self) -> c_bash.subshell_com:
        """
        :return: the c subshell_com struct representation of this subshell command
        """
        c_subshell = c_bash.subshell_com()
        c_subshell.flags = int_from_command_flag_list(self.flags)
        c_subshell.line = self.line
        c_subshell.command = ctypes.POINTER(c_bash.command)(self.command._to_ctypes())
        return c_subshell


class CoprocCom:
    """
    a coprocess command
    """

    flags: list[CommandFlag]  # unclear flag type
    name: str  # the name of the coprocess
    command: "Command"  # the command to run in the coprocess

    def __init__(self, coproc: c_bash.coproc_com):
        """
        :param coproc: the coproc command struct
        """
        self.flags = command_flag_list_from_int(coproc.flags)
        # c_char_p is a bytes object so we need to decode it
        self.name = coproc.name.decode("utf-8")
        self.command = Command(coproc.command.contents)

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other coproc command
        :return: whether the two coproc commands are equal, the
        flags lists need not be in the same order
        """
        if not isinstance(other, CoprocCom):
            return False
        if not list_same_elements(self.flags, other.flags):
            return False
        if self.name != other.name:
            return False
        if self.command != other.command:
            return False
        return True

    def _to_json(self) -> dict[str, Union[int, str, dict, list]]:
        """
        :return: a dictionary representation of the coproc command
        """
        return {
            "flags": [x._to_json() for x in self.flags],
            "name": self.name,
            "command": self.command._to_json(),
        }

    def _to_ctypes(self) -> c_bash.coproc_com:
        """
        :return: the c coproc_com struct representation of this coproc command
        """
        c_coproc = c_bash.coproc_com()
        c_coproc.flags = int_from_command_flag_list(self.flags)
        c_coproc.name = self.name.encode("utf-8")
        c_coproc.command = ctypes.POINTER(c_bash.command)(self.command._to_ctypes())
        return c_coproc


class ValueUnion:
    """
    a union of all the possible command types
    exactly one of these will be non-null
    """

    for_com: Optional[ForCom]
    case_com: Optional[CaseCom]
    while_com: Optional[WhileCom]
    if_com: Optional[IfCom]
    connection: Optional[Connection]
    simple_com: Optional[SimpleCom]
    function_def: Optional[FunctionDef]
    group_com: Optional[GroupCom]
    select_com: Optional[SelectCom]
    arith_com: Optional[ArithCom]
    cond_com: Optional[CondCom]
    arith_for_com: Optional[ArithForCom]
    subshell_com: Optional[SubshellCom]
    coproc_com: Optional[CoprocCom]

    def __init__(self, command_type: CommandType, value: c_bash.value):
        """
        :param command_type: the type of command
        :param value: the value union struct
        """
        self.for_com = None
        self.case_com = None
        self.while_com = None
        self.if_com = None
        self.connection = None
        self.simple_com = None
        self.function_def = None
        self.group_com = None
        self.select_com = None
        self.arith_com = None
        self.cond_com = None
        self.arith_for_com = None
        self.subshell_com = None
        self.coproc_com = None

        if command_type == CommandType.CM_FOR:
            self.for_com = ForCom(value.For.contents)
        elif command_type == CommandType.CM_CASE:
            self.case_com = CaseCom(value.Case.contents)
        elif command_type == CommandType.CM_WHILE:
            self.while_com = WhileCom(value.While.contents)
        elif command_type == CommandType.CM_IF:
            self.if_com = IfCom(value.If.contents)
        elif command_type == CommandType.CM_CONNECTION:
            self.connection = Connection(value.Connection.contents)
        elif command_type == CommandType.CM_SIMPLE:
            self.simple_com = SimpleCom(value.Simple.contents)
        elif command_type == CommandType.CM_FUNCTION_DEF:
            self.function_def = FunctionDef(value.Function_def.contents)
        elif command_type == CommandType.CM_UNTIL:
            self.while_com = WhileCom(value.While.contents)
        elif command_type == CommandType.CM_GROUP:
            self.group_com = GroupCom(value.Group.contents)
        elif command_type == CommandType.CM_SELECT:
            self.select_com = SelectCom(value.Select.contents)
        elif command_type == CommandType.CM_ARITH:
            self.arith_com = ArithCom(value.Arith.contents)
        elif command_type == CommandType.CM_COND:
            self.cond_com = CondCom(value.Cond.contents)
        elif command_type == CommandType.CM_ARITH_FOR:
            self.arith_for_com = ArithForCom(value.ArithFor.contents)
        elif command_type == CommandType.CM_SUBSHELL:
            self.subshell_com = SubshellCom(value.Subshell.contents)
        elif command_type == CommandType.CM_COPROC:
            self.coproc_com = CoprocCom(value.Coproc.contents)
        else:
            raise Exception("Unknown command type provided.")

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other value union
        :return: whether the two value unions are equal
        """
        if not isinstance(other, ValueUnion):
            return False
        if self.for_com != other.for_com:
            return False
        if self.case_com != other.case_com:
            return False
        if self.while_com != other.while_com:
            return False
        if self.if_com != other.if_com:
            return False
        if self.connection != other.connection:
            return False
        if self.simple_com != other.simple_com:
            return False
        if self.function_def != other.function_def:
            return False
        if self.group_com != other.group_com:
            return False
        if self.select_com != other.select_com:
            return False
        if self.arith_com != other.arith_com:
            return False
        if self.cond_com != other.cond_com:
            return False
        if self.arith_for_com != other.arith_for_com:
            return False
        if self.subshell_com != other.subshell_com:
            return False
        if self.coproc_com != other.coproc_com:
            return False
        return True

    def _to_json(self) -> dict:
        """
        :return: a dictionary representation of the value union
        """
        if self.for_com is not None:
            return self.for_com._to_json()
        elif self.case_com is not None:
            return self.case_com._to_json()
        elif self.while_com is not None:
            return self.while_com._to_json()
        elif self.if_com is not None:
            return self.if_com._to_json()
        elif self.connection is not None:
            return self.connection._to_json()
        elif self.simple_com is not None:
            return self.simple_com._to_json()
        elif self.function_def is not None:
            return self.function_def._to_json()
        elif self.group_com is not None:
            return self.group_com._to_json()
        elif self.select_com is not None:
            return self.select_com._to_json()
        elif self.arith_com is not None:
            return self.arith_com._to_json()
        elif self.cond_com is not None:
            return self.cond_com._to_json()
        elif self.arith_for_com is not None:
            return self.arith_for_com._to_json()
        elif self.subshell_com is not None:
            return self.subshell_com._to_json()
        elif self.coproc_com is not None:
            return self.coproc_com._to_json()
        else:
            raise Exception("invalid value union")

    def _to_ctypes(self) -> c_bash.value:
        """
        :return: the c value union struct representation of this value union
        """
        c_value = c_bash.value()
        if self.for_com is not None:
            c_value.For = ctypes.POINTER(c_bash.for_com)(self.for_com._to_ctypes())
        elif self.case_com is not None:
            c_value.Case = ctypes.POINTER(c_bash.case_com)(self.case_com._to_ctypes())
        elif self.while_com is not None:
            c_value.While = ctypes.POINTER(c_bash.while_com)(
                self.while_com._to_ctypes()
            )
        elif self.if_com is not None:
            c_value.If = ctypes.POINTER(c_bash.if_com)(self.if_com._to_ctypes())
        elif self.connection is not None:
            c_value.Connection = ctypes.POINTER(c_bash.connection)(
                self.connection._to_ctypes()
            )
        elif self.simple_com is not None:
            c_value.Simple = ctypes.POINTER(c_bash.simple_com)(
                self.simple_com._to_ctypes()
            )
        elif self.function_def is not None:
            c_value.Function_def = ctypes.POINTER(c_bash.function_def)(
                self.function_def._to_ctypes()
            )
        elif self.group_com is not None:
            c_value.Group = ctypes.POINTER(c_bash.group_com)(
                self.group_com._to_ctypes()
            )
        elif self.select_com is not None:
            c_value.Select = ctypes.POINTER(c_bash.select_com)(
                self.select_com._to_ctypes()
            )
        elif self.arith_com is not None:
            c_value.Arith = ctypes.POINTER(c_bash.arith_com)(
                self.arith_com._to_ctypes()
            )
        elif self.cond_com is not None:
            c_value.Cond = ctypes.POINTER(c_bash.cond_com)(self.cond_com._to_ctypes())
        elif self.arith_for_com is not None:
            c_value.ArithFor = ctypes.POINTER(c_bash.arith_for_com)(
                self.arith_for_com._to_ctypes()
            )
        elif self.subshell_com is not None:
            c_value.Subshell = ctypes.POINTER(c_bash.subshell_com)(
                self.subshell_com._to_ctypes()
            )
        elif self.coproc_com is not None:
            c_value.Coproc = ctypes.POINTER(c_bash.coproc_com)(
                self.coproc_com._to_ctypes()
            )
        else:
            raise Exception("invalid value union")
        return c_value


class Command:
    """
    a mirror of the bash command struct defined here:
    https://git.savannah.gnu.org/cgit/bash.git/tree/command.h
    """

    type: CommandType  # command type
    flags: list[CommandFlag]  # command flags
    # line: int  # line number the command is on - seems to be unused
    redirects: list[Redirect]
    value: ValueUnion

    def __init__(self, bash_command: c_bash.command):
        """
        :param bash_command: the command struct
        """
        self.type = CommandType(bash_command.type)
        self.flags = command_flag_list_from_int(bash_command.flags)
        # self.line = bash_command.line
        self.redirects = redirect_list_from_redirect(bash_command.redirects)
        self.value = ValueUnion(self.type, bash_command.value)

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other command
        :return: whether the two commands are equal, the
        flags lists need not be in the same order
        """
        if not isinstance(other, Command):
            return False
        if self.type != other.type:
            return False
        if not list_same_elements(self.flags, other.flags):
            return False
        if not list_same_elements(self.redirects, other.redirects):
            return False
        if self.value != other.value:
            return False
        return True

    def _to_json(self) -> dict[str, Union[int, str, dict, list]]:
        """
        :return: a dictionary representation of the command
        """
        return {
            "type": self.type._to_json(),
            "flags": self.flags,
            # 'line': self.line,
            "redirects": [x._to_json() for x in self.redirects],
            "value": self.value._to_json(),
        }

    def _to_ctypes(self) -> c_bash.command:
        """
        :return: the c command struct representation of this command
        """
        c_command = c_bash.command()
        c_command.type = self.type.value
        c_command.flags = int_from_command_flag_list(self.flags)
        c_command.line = 0
        c_command.redirects = c_redirect_from_redirect_list(self.redirects)
        c_command.value = self.value._to_ctypes()
        return c_command
