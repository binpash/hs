from __future__ import annotations

from enum import Enum


class OFlag(Enum):
    """
    represents open flags present in the OpenFlag class
    """

    O_RDONLY = 0
    O_WRONLY = 1 << 0
    O_RDWR = 1 << 1
    O_APPEND = 1 << 3
    O_CREAT = 1 << 9
    O_TRUNC = 1 << 10

    def __eq__(self, other):
        """
        :param other: the other OFlag
        :return: True if the other OFlag is equal to this OFlag
        """
        if isinstance(other, OFlag):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        else:
            return False

    def _to_json(self) -> str:
        """
        :return: the string representation of the open flag
        """
        if self == OFlag.O_RDONLY:
            return "read_only"
        elif self == OFlag.O_WRONLY:
            return "write_only"
        elif self == OFlag.O_RDWR:
            return "read_write"
        elif self == OFlag.O_APPEND:
            return "append"
        elif self == OFlag.O_CREAT:
            return "create"
        elif self == OFlag.O_TRUNC:
            return "truncate"
        else:
            raise Exception("invalid open flag")


def oflag_list_from_int(oflag_int: int) -> list[OFlag]:
    """
    :param oflag_int: the integer value of the open flag
    :return: a list of open flags
    """
    flag_list = []
    for flag in OFlag:
        if oflag_int & flag.value:
            flag_list.append(flag)
    return flag_list


def int_from_oflag_list(flag_list: list[OFlag]) -> int:
    """
    :param flag_list: the list of open flags
    :return: the integer value of the open flag
    """
    flag_int = 0
    for flag in flag_list:
        flag_int |= flag.value
    return flag_int


class WordDescFlag(Enum):
    """
    represents word description flags present in the WordDesc class
    """

    W_HASDOLLAR = 1 << 0  # dollar sign present
    W_QUOTED = 1 << 1  # some form of quote character is present
    W_ASSIGNMENT = 1 << 2  # this word is a variable assignment
    W_SPLITSPACE = 1 << 3  # split this word on " " regardless of IFS
    # do not perform word splitting on this word because IFS is empty string
    W_NOSPLIT = 1 << 4
    W_NOGLOB = 1 << 5  # do not perform globbing on this word
    # don't split word except for $@ expansion (using spaces) because context does not allow it
    W_NOSPLIT2 = 1 << 6
    W_TILDEEXP = 1 << 7  # tilde expand this assignment word
    W_DOLLARAT = 1 << 8  # UNUSED - $@ and its special handling
    W_ARRAYREF = 1 << 9  # word is a valid array reference
    W_NOCOMSUB = 1 << 10  # don't perform command substitution on this word
    W_ASSIGNRHS = 1 << 11  # word is rhs of an assignment statement
    W_NOTILDE = 1 << 12  # don't perform tilde expansion on this word
    W_NOASSNTILDE = 1 << 13  # don't do tilde expansion like an assignment statement
    W_EXPANDRHS = 1 << 14  # expanding word in ${paramOPword}
    W_COMPASSIGN = 1 << 15  # compound assignment
    W_ASSNBLTIN = 1 << 16  # word is a builtin command that takes assignments
    W_ASSIGNARG = 1 << 17  # word is assignment argument to command
    W_HASQUOTEDNULL = 1 << 18  # word contains a quoted null character
    W_DQUOTE = 1 << 19  # UNUSED - word should be treated as if double-quoted
    W_NOPROCSUB = 1 << 20  # don't perform process substitution
    W_SAWQUOTEDNULL = 1 << 21  # word contained a quoted null that was removed
    W_ASSIGNASSOC = 1 << 22  # word looks like associative array assignment
    W_ASSIGNARRAY = 1 << 23  # word looks like a compound indexed array assignment
    W_ARRAYIND = 1 << 24  # word is an array index being expanded
    # word is a global assignment to declare (declare/typeset -g)
    W_ASSNGLOBAL = 1 << 25
    W_NOBRACE = 1 << 26  # don't perform brace expansion
    W_COMPLETE = 1 << 27  # word is being expanded for completion
    W_CHKLOCAL = 1 << 28  # check for local vars on assignment
    # force assignments to be to local variables, non-fatal on assignment errors
    W_FORCELOCAL = 1 << 29

    def __eq__(self, other):
        """
        :param other: the other WordDescFlag
        :return: True if the other WordDescFlag is equal to this WordDescFlag
        """
        if isinstance(other, WordDescFlag):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        else:
            return False

    def _to_json(self) -> str:
        """
        :return: the string representation of the word description flag
        """
        if self == WordDescFlag.W_HASDOLLAR:
            return "has_dollar"
        elif self == WordDescFlag.W_QUOTED:
            return "quoted"
        elif self == WordDescFlag.W_ASSIGNMENT:
            return "assignment"
        elif self == WordDescFlag.W_SPLITSPACE:
            return "split_space"
        elif self == WordDescFlag.W_NOSPLIT:
            return "no_split"
        elif self == WordDescFlag.W_NOGLOB:
            return "no_glob"
        elif self == WordDescFlag.W_NOSPLIT2:
            return "no_split2"
        elif self == WordDescFlag.W_TILDEEXP:
            return "tilde_exp"
        elif self == WordDescFlag.W_DOLLARAT:
            return "dollar_at"
        elif self == WordDescFlag.W_ARRAYREF:
            return "array_ref"
        elif self == WordDescFlag.W_NOCOMSUB:
            return "no_comsub"
        elif self == WordDescFlag.W_ASSIGNRHS:
            return "assign_rhs"
        elif self == WordDescFlag.W_NOTILDE:
            return "no_tilde"
        elif self == WordDescFlag.W_NOASSNTILDE:
            return "no_assign_tilde"
        elif self == WordDescFlag.W_EXPANDRHS:
            return "expand_rhs"
        elif self == WordDescFlag.W_COMPASSIGN:
            return "comp_assign"
        elif self == WordDescFlag.W_ASSNBLTIN:
            return "assign_builtin"
        elif self == WordDescFlag.W_ASSIGNARG:
            return "assign_arg"
        elif self == WordDescFlag.W_HASQUOTEDNULL:
            return "has_quoted_null"
        elif self == WordDescFlag.W_DQUOTE:
            return "dquote"
        elif self == WordDescFlag.W_NOPROCSUB:
            return "no_procsub"
        elif self == WordDescFlag.W_SAWQUOTEDNULL:
            return "saw_quoted_null"
        elif self == WordDescFlag.W_ASSIGNASSOC:
            return "assign_assoc"
        elif self == WordDescFlag.W_ASSIGNARRAY:
            return "assign_array"
        elif self == WordDescFlag.W_ARRAYIND:
            return "array_index"
        elif self == WordDescFlag.W_ASSNGLOBAL:
            return "assign_global"
        elif self == WordDescFlag.W_NOBRACE:
            return "no_brace"
        elif self == WordDescFlag.W_COMPLETE:
            return "complete"
        elif self == WordDescFlag.W_CHKLOCAL:
            return "check_local"
        elif self == WordDescFlag.W_FORCELOCAL:
            return "force_local"
        else:
            raise Exception("invalid word description flag")


def word_desc_flag_list_from_int(flag_int: int) -> list[WordDescFlag]:
    """
    :param flag_int: the integer value of the word description flag
    :return: a list of word description flags
    """
    flag_list = []
    for flag in WordDescFlag:
        if flag_int & flag.value:
            flag_list.append(flag)
    return flag_list


def int_from_word_desc_flag_list(flag_list: list[WordDescFlag]) -> int:
    """
    :param flag_list: the list of word description flags
    :return: the integer value of the word description flag
    """
    flag_int = 0
    for flag in flag_list:
        flag_int |= flag.value
    return flag_int


class CommandFlag(Enum):
    """
    represents command flags present in several command types
    """

    CMD_WANT_SUBSHELL = 1 << 0  # user wants subshell
    CMD_FORCE_SUBSHELL = 1 << 1  # shell needs to force subshell
    CMD_INVERT_RETURN = 1 << 2  # invert the exit value
    CMD_IGNORE_RETURN = 1 << 3  # ignore the exit value
    CMD_NO_FUNCTIONS = 1 << 4  # ignore functions during command lookup
    CMD_INHIBIT_EXPANSION = 1 << 5  # do not expand command words
    CMD_NO_FORK = 1 << 6  # do not fork, just call execv
    CMD_TIME_PIPELINE = 1 << 7  # time the pipeline
    CMD_TIME_POSIX = 1 << 8  # time -p was specified
    CMD_AMPERSAND = 1 << 9  # command &
    CMD_STDIN_REDIRECTED = 1 << 10  # async command needs implicit </dev/null
    CMD_COMMAND_BUILTIN = 1 << 11  # command executed by 'command' builtin
    CMD_COPROC_SHELL = 1 << 12  # coprocess shell
    CMD_LASTPIPE = 1 << 13  # last command in pipeline
    CMD_STD_PATH = 1 << 14  # use default PATH for command lookup
    CMD_TRY_OPTIMIZING = 1 << 15  # try to optimize simple command

    def __eq__(self, other):
        """
        :param other: the other CommandFlag
        :return: True if the other CommandFlag is equal to this CommandFlag
        """
        if isinstance(other, CommandFlag):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        else:
            return False

    def _to_json(self) -> str:
        """
        :return: the string representation of the command flag
        """
        if self == CommandFlag.CMD_WANT_SUBSHELL:
            return "want_subshell"
        elif self == CommandFlag.CMD_FORCE_SUBSHELL:
            return "force_subshell"
        elif self == CommandFlag.CMD_INVERT_RETURN:
            return "invert_return"
        elif self == CommandFlag.CMD_IGNORE_RETURN:
            return "ignore_return"
        elif self == CommandFlag.CMD_NO_FUNCTIONS:
            return "no_functions"
        elif self == CommandFlag.CMD_INHIBIT_EXPANSION:
            return "inhibit_expansion"
        elif self == CommandFlag.CMD_NO_FORK:
            return "no_fork"
        elif self == CommandFlag.CMD_TIME_PIPELINE:
            return "time_pipeline"
        elif self == CommandFlag.CMD_TIME_POSIX:
            return "time_posix"
        elif self == CommandFlag.CMD_AMPERSAND:
            return "ampersand"
        elif self == CommandFlag.CMD_STDIN_REDIRECTED:
            return "stdin_redirected"
        elif self == CommandFlag.CMD_COMMAND_BUILTIN:
            return "command_builtin"
        elif self == CommandFlag.CMD_COPROC_SHELL:
            return "coproc_shell"
        elif self == CommandFlag.CMD_LASTPIPE:
            return "last_pipe"
        elif self == CommandFlag.CMD_STD_PATH:
            return "std_path"
        elif self == CommandFlag.CMD_TRY_OPTIMIZING:
            return "try_optimizing"
        else:
            raise Exception("invalid command flag")


def command_flag_list_from_int(flag_int: int) -> list[CommandFlag]:
    """
    :param flag_int: the integer value of the command flag
    :return: a list of command flags
    """
    flag_list = []
    for flag in CommandFlag:
        if flag_int & flag.value:
            flag_list.append(flag)
    return flag_list


def int_from_command_flag_list(flag_list: list[CommandFlag]) -> int:
    """
    :param flag_list: the list of command flags
    :return: the integer value of the command flag
    """
    flag_int = 0
    for flag in flag_list:
        flag_int |= flag.value
    return flag_int


class CommandType(Enum):
    """
    a command type enum
    """

    CM_FOR = 0  # for loop
    CM_CASE = 1  # switch case
    CM_WHILE = 2  # while loop
    CM_IF = 3  # if statement
    CM_SIMPLE = 4  # simple command
    CM_SELECT = 5  # select statement
    CM_CONNECTION = 6  # probably connectors like &,||, &&, ;
    CM_FUNCTION_DEF = 7  # function definition
    CM_UNTIL = 8  # until loop
    CM_GROUP = 9  # probably a command grouping via { } or ( )
    CM_ARITH = 10  # arithmetic expression, probably using $(( ))
    CM_COND = 11  # conditional expression, probably using [[ ]]
    CM_ARITH_FOR = 12  # probably for loop using (( ))
    CM_SUBSHELL = 13  # subshell via ( )
    CM_COPROC = 14  # coprocess

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other CommandType
        :return: True if the other CommandType is equal to this CommandType
        """
        if isinstance(other, CommandType):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        else:
            return False

    def _to_json(self) -> str:
        """
        :return: the string representation of the command type
        """
        if self == CommandType.CM_FOR:
            return "for"
        elif self == CommandType.CM_CASE:
            return "case"
        elif self == CommandType.CM_WHILE:
            return "while"
        elif self == CommandType.CM_IF:
            return "if"
        elif self == CommandType.CM_SELECT:
            return "select"
        elif self == CommandType.CM_SIMPLE:
            return "simple"
        elif self == CommandType.CM_CONNECTION:
            return "connection"
        elif self == CommandType.CM_FUNCTION_DEF:
            return "function_def"
        elif self == CommandType.CM_UNTIL:
            return "until"
        elif self == CommandType.CM_GROUP:
            return "group"
        elif self == CommandType.CM_ARITH:
            return "arithmetic"
        elif self == CommandType.CM_COND:
            return "conditional"
        elif self == CommandType.CM_ARITH_FOR:
            return "arithmetic_for"
        elif self == CommandType.CM_SUBSHELL:
            return "subshell"
        elif self == CommandType.CM_COPROC:
            return "coproc"
        else:
            raise Exception("invalid command type")


class RInstruction(Enum):
    """
    a redirection instruction enum
    """

    R_OUTPUT_DIRECTION = 0  # >foo
    R_INPUT_DIRECTION = 1  # <foo
    R_INPUTA_DIRECTION = 2  # foo & makes this -- might not be used
    R_APPENDING_TO = 3  # >>foo
    R_READING_UNTIL = 4  # << foo
    R_READING_STRING = 5  # <<< foo
    R_DUPLICATING_INPUT = 6  # 1<&2
    R_DUPLICATING_OUTPUT = 7  # 1>&2
    R_DEBLANK_READING_UNTIL = 8  # <<-foo
    R_CLOSE_THIS = 9  # <&-
    R_ERR_AND_OUT = 10  # command &>filename
    R_INPUT_OUTPUT = 11  # <>foo
    R_OUTPUT_FORCE = 12  # >| foo
    R_DUPLICATING_INPUT_WORD = 13  # 1<&$foo
    R_DUPLICATING_OUTPUT_WORD = 14  # 1>&$foo
    R_MOVE_INPUT = 15  # 1<&2-
    R_MOVE_OUTPUT = 16  # 1>&2-
    R_MOVE_INPUT_WORD = 17  # 1<&$foo-
    R_MOVE_OUTPUT_WORD = 18  # 1>&$foo-
    R_APPEND_ERR_AND_OUT = 19  # &>> filename

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other RInstruction
        :return: True if the other RInstruction is equal to this RInstruction
        """
        if isinstance(other, RInstruction):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        else:
            return False

    def _to_json(self) -> str:
        """
        :return: the string representation of the redirection type
        """
        if self == RInstruction.R_OUTPUT_DIRECTION:
            return ">"
        elif self == RInstruction.R_INPUT_DIRECTION:
            return "<"
        elif self == RInstruction.R_INPUTA_DIRECTION:
            return "&"  # ?
        elif self == RInstruction.R_APPENDING_TO:
            return ">>"
        elif self == RInstruction.R_READING_UNTIL:
            return "<<"
        elif self == RInstruction.R_READING_STRING:
            return "<<<"
        elif self == RInstruction.R_DUPLICATING_INPUT:
            return "<&"
        elif self == RInstruction.R_DUPLICATING_OUTPUT:
            return ">&"
        elif self == RInstruction.R_DEBLANK_READING_UNTIL:
            return "<<-"
        elif self == RInstruction.R_CLOSE_THIS:
            return "<&-"
        elif self == RInstruction.R_ERR_AND_OUT:
            return "&>"
        elif self == RInstruction.R_INPUT_OUTPUT:
            return "<>"
        elif self == RInstruction.R_OUTPUT_FORCE:
            return ">|"
        elif self == RInstruction.R_DUPLICATING_INPUT_WORD:
            return "<&$"  # todo figure out if $ is needed
        elif self == RInstruction.R_DUPLICATING_OUTPUT_WORD:
            return ">&$"  # todo figure out if $ is needed
        elif self == RInstruction.R_MOVE_INPUT:
            return "<&-"
        elif self == RInstruction.R_MOVE_OUTPUT:
            return ">&-"
        elif self == RInstruction.R_MOVE_INPUT_WORD:
            return "<&$-"  # todo figure out if $ is needed
        elif self == RInstruction.R_MOVE_OUTPUT_WORD:
            return ">&$-"  # todo figure out if $ is needed
        elif self == RInstruction.R_APPEND_ERR_AND_OUT:
            return "&>>"
        else:
            raise Exception("invalid redirect instruction")


class CondTypeEnum(Enum):
    """
    a conditional expression type enum
    """

    COND_AND = 1
    COND_OR = 2
    COND_UNARY = 3
    COND_BINARY = 4
    COND_TERM = 5
    COND_EXPR = 6

    def __eq__(self, other: object) -> bool:
        if isinstance(other, CondTypeEnum):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        else:
            return False

    def _to_json(self) -> str:
        """
        :return: the string representation of the conditional expression type
        """
        if self == CondTypeEnum.COND_AND:
            return "and"
        elif self == CondTypeEnum.COND_OR:
            return "or"
        elif self == CondTypeEnum.COND_UNARY:
            return "unary"
        elif self == CondTypeEnum.COND_BINARY:
            return "binary"
        elif self == CondTypeEnum.COND_TERM:
            return "term"
        elif self == CondTypeEnum.COND_EXPR:
            return "expression"
        else:
            raise Exception("invalid conditional expression type")


class ConnectionType(Enum):
    """
    a connection type enum - refer to execute_connection in execute_cmd.c
    in the bash source code for more information, pretty funny approach
    to this
    """

    AMPERSAND = 38
    SEMICOLON = 59
    NEWLINE = 10
    PIPE = 124
    AND_AND = 288
    OR_OR = 289

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other ConnectionType
        :return: True if the other ConnectionType is equal to this ConnectionType
        """
        if isinstance(other, ConnectionType):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        else:
            return False

    def _to_json(self) -> str:
        """
        :return: the string representation of the connection type
        """
        if self == ConnectionType.AMPERSAND:
            return "&"
        elif self == ConnectionType.SEMICOLON:
            return ";"
        elif self == ConnectionType.NEWLINE:
            return "\n"
        elif self == ConnectionType.PIPE:
            return "|"
        elif self == ConnectionType.AND_AND:
            return "&&"
        elif self == ConnectionType.OR_OR:
            return "||"
        else:
            raise Exception("invalid connection type")


class RedirectFlag(Enum):
    """
    a redirect flag enum
    """

    REDIR_VARASSIGN = 1 << 0

    def __eq__(self, other: object) -> bool:
        if isinstance(other, RedirectFlag):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        else:
            return False

    def _to_json(self) -> str:
        """
        :return: the string representation of the redirect flag
        """
        if self == RedirectFlag.REDIR_VARASSIGN:
            return "var_assign"
        else:
            raise Exception("invalid redirect flag")


def redirect_flag_list_from_rflags(rflags: int) -> list[RedirectFlag]:
    """
    :param rflags: the integer value of the redirect flag
    """
    flag_list = []
    for flag in RedirectFlag:
        if rflags & flag.value:
            flag_list.append(flag)
    return flag_list


def int_from_redirect_flag_list(flag_list: list[RedirectFlag]) -> int:
    """
    :param flag_list: the list of redirect flags
    :return: the integer value of the redirect flag
    """
    flag_int = 0
    for flag in flag_list:
        flag_int |= flag.value
    return flag_int


class PatternFlag(Enum):
    """
    a pattern flag enum, present in the CasePattern class
    """

    CASEPAT_FALLTHROUGH = 1 << 0  # fall through to next pattern
    CASEPAT_TESTNEXT = 1 << 1  # test next pattern

    def __eq__(self, other: object) -> bool:
        """
        :param other: the other PatternFlag
        """
        if isinstance(other, PatternFlag):
            return self.value == other.value
        elif isinstance(other, int):
            return self.value == other
        else:
            return False

    def _to_json(self) -> str:
        """
        :return: the string representation of the pattern flag
        """
        if self == PatternFlag.CASEPAT_FALLTHROUGH:
            return "fallthrough"
        elif self == PatternFlag.CASEPAT_TESTNEXT:
            return "test_next"
        else:
            raise Exception("invalid pattern flag")


def pattern_flag_list_from_int(flag_int: int) -> list[PatternFlag]:
    """
    :param flag_int: the integer value of the pattern flag
    :return: a list of pattern flags
    """
    flag_list = []
    for flag in PatternFlag:
        if flag_int & flag.value:
            flag_list.append(flag)
    return flag_list


def int_from_pattern_flag_list(flag_list: list[PatternFlag]) -> int:
    """
    :param flag_list: the list of pattern flags
    :return: the integer value of the pattern flag
    """
    flag_int = 0
    for flag in flag_list:
        flag_int |= flag.value
    return flag_int
