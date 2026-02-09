"""
Utility functions for the PaSh preprocessor.

Contains general utilities (logging, temp files), AST building helpers,
and variable name conventions for the pash runtime.
"""

from datetime import timedelta
import functools
import logging
import os
import tempfile

from shasta.ast_node import AstNode, ArgChar, CArgChar

# Configuration from environment variables (set by pa.sh or pash_runtime.sh)
PASH_TMP_PREFIX = os.environ.get("PASH_TMP_PREFIX", "/tmp/pash_tmp/")
OUTPUT_TIME = os.environ.get("pash_output_time_flag", "1") == "1"
LOGGING_PREFIX = "PaSh: "


# === Logging and general utilities ===


def unzip(lst):
    """Unzip a list of pairs into two separate lists."""
    res = [[i for i, j in lst], [j for i, j in lst]]
    return res


def print_time_delta(prefix, start_time, end_time):
    """Output timing information to the log."""
    time_difference = (end_time - start_time) / timedelta(milliseconds=1)
    if OUTPUT_TIME:
        log("{} time:".format(prefix), time_difference, " ms", level=0)
    else:
        log("{} time:".format(prefix), time_difference, " ms")


def logging_prefix(logging_prefix_str):
    """Decorator to add logging prefix to a function."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            global LOGGING_PREFIX
            old_prefix = LOGGING_PREFIX
            LOGGING_PREFIX = logging_prefix_str
            result = func(*args, **kwargs)
            LOGGING_PREFIX = old_prefix
            return result
        return wrapper
    return decorator


def log(*args, end="\n", level=2):
    """Wrapper for logging."""
    if level == 1:
        concatted_args = " ".join([str(a) for a in list(args)])
        logging.warning(f"{LOGGING_PREFIX} {concatted_args}")
    elif level >= 2:
        concatted_args = " ".join([str(a) for a in list(args)])
        logging.info(f"{LOGGING_PREFIX} {concatted_args}")


def ptempfile():
    """Create a temporary file in the PaSh temp directory."""
    fd, name = tempfile.mkstemp(dir=PASH_TMP_PREFIX)
    os.close(fd)
    return name


def make_kv(key, val):
    """Make a key-value pair in AST JSON format."""
    return [key, val]


# === Variable names used in the pash runtime ===


def loop_iters_var() -> str:
    return "pash_loop_iters"


def loop_iter_var(loop_id: int) -> str:
    return f"pash_loop_{loop_id}_iter"


# === Preprocessed AST classes ===


class PreprocessedAST:
    """Class used by the preprocessor in ast_to_ir."""

    def __init__(
        self, ast, replace_whole, non_maximal, something_replaced=True, last_ast=False
    ):
        assert isinstance(ast, AstNode)
        self.ast = ast
        self.replace_whole = replace_whole
        self.non_maximal = non_maximal
        self.something_replaced = something_replaced
        self.last_ast = last_ast

    def should_replace_whole_ast(self):
        return self.replace_whole

    def is_non_maximal(self):
        return self.non_maximal

    def will_anything_be_replaced(self):
        return self.something_replaced

    def is_last_ast(self):
        return self.last_ast


class UnparsedScript:
    """
    Represents text that was not modified at all by preprocessing,
    and therefore does not need to be unparsed.
    """

    def __init__(self, text):
        self.text = text


# === AST building helpers ===


def format_args(args):
    formatted_args = [format_arg_chars(arg_chars) for arg_chars in args]
    return formatted_args


def format_arg_chars(arg_chars):
    chars = [format_arg_char(arg_char) for arg_char in arg_chars]
    return "".join(chars)


def format_arg_char(arg_char: ArgChar) -> str:
    return arg_char.format()


def string_to_carg_char_list(string: str) -> "list[CArgChar]":
    ret = [CArgChar(ord(char)) for char in string]
    return ret


def string_to_arguments(string):
    return [string_to_argument(word) for word in string.split(" ")]


def string_to_argument(string):
    ret = [char_to_arg_char(char) for char in string]
    return ret


def concat_arguments(arg1, arg2):
    """Arguments are simply `arg_char list` and therefore can just be concatenated."""
    return arg1 + arg2


def char_to_arg_char(char):
    return ["C", ord(char)]


def escaped_char(char):
    return ["E", ord(char)]


def standard_var_ast(string):
    return make_kv("V", ["Normal", False, string, []])


def make_arith(arg):
    return make_kv("A", arg)


def make_quoted_variable(string):
    return make_kv("Q", [standard_var_ast(string)])


def quote_arg(arg):
    return make_kv("Q", arg)


def redir_append_stderr_to_string_file(string):
    return make_kv("File", ["Append", 2, string_to_argument(string)])


def redir_stdout_to_file(arg):
    return make_kv("File", ["To", 1, arg])


def redir_file_to_stdin(arg):
    return make_kv("File", ["From", 0, arg])


def make_background(body, redirections=None):
    redirections = [] if redirections is None else redirections
    lineno = 0
    node = make_kv("Background", [lineno, body, redirections])
    return node


def make_backquote(node):
    node = make_kv("B", node)
    return node


def make_subshell(body, redirections=None):
    redirections = [] if redirections is None else redirections
    lineno = 0
    node = make_kv("Subshell", [lineno, body, redirections])
    return node


def make_command(arguments, redirections=None, assignments=None):
    redirections = [] if redirections is None else redirections
    assignments = [] if assignments is None else assignments
    lineno = 0
    node = make_kv("Command", [lineno, assignments, arguments, redirections])
    return node


def make_nop():
    return make_command([string_to_argument(":")])


def make_assignment(var, value):
    lineno = 0
    assignment = (var, value)
    assignments = [assignment]
    node = make_kv("Command", [lineno, assignments, [], []])
    return node


def make_semi_sequence(asts):
    if len(asts) == 0:
        return make_nop()

    if len(asts) == 1:
        return asts[0]
    else:
        acc = asts[-1]
        iter_asts = asts[:-1]
        for ast in iter_asts[::-1]:
            acc = make_kv("Semi", [ast, acc])
        return acc


def make_defun(name, body):
    lineno = 0
    node = make_kv("Defun", [lineno, name, body])
    return node


def make_export_var_constant_string(var_name: str, value: str):
    node = make_export_var(var_name, string_to_argument(value))
    return node


def make_export_var(var_name: str, arg_char_list):
    """An argument is an arg_char_list."""
    arg1 = string_to_argument(f"{var_name}=")
    arguments = [string_to_argument("export"), concat_arguments(arg1, arg_char_list)]
    node = make_command(arguments)
    return node


def export_pash_loop_iters_for_current_context(all_loop_ids: "list[int]"):
    if len(all_loop_ids) > 0:
        iter_var_names = [loop_iter_var(loop_id) for loop_id in all_loop_ids]
        iter_vars = [
            standard_var_ast(iter_var_name) for iter_var_name in iter_var_names
        ]
        concatted_vars = [iter_vars[0]]
        for iter_var in iter_vars[1:]:
            concatted_vars.append(char_to_arg_char("-"))
            concatted_vars.append(iter_var)
        quoted_vars = [quote_arg(concatted_vars)]
    else:
        quoted_vars = []

    # export pash_loop_iters="$pash_loop_XXX_iter $pash_loop_YYY_iter ..."
    save_loop_iters_node = make_export_var(loop_iters_var(), quoted_vars)

    return save_loop_iters_node


def make_unset_var(var_name: str):
    arguments = [string_to_argument("unset"), string_to_argument(var_name)]
    node = make_command(arguments)
    return node


def make_loop_list_assignment(loop_list_args):
    """Create HS_LOOP_LIST=<list> assignment from for-loop arguments.

    Matches the implementation from fae47999 commit of spec_future branch.
    """
    from shasta.ast_node import CArgChar, QArgChar
    from shasta.json_to_ast import to_ast_node
    import copy

    list_eval_node = to_ast_node(make_assignment('HS_LOOP_LIST', string_to_argument('0')))

    list_arguments = copy.deepcopy(loop_list_args[0])
    for a in loop_list_args[1:]:
        list_arguments.append(CArgChar(ord(' ')))
        list_arguments.extend(copy.deepcopy(a))

    list_eval_node.assignments[0].val = [QArgChar(list_arguments)]

    return list_eval_node


def make_increment_var(var_name: str):
    arg = string_to_argument(f"{var_name}+1")
    arith_expr = make_arith(arg)
    assignments = [[var_name, [arith_expr]]]
    node = make_command([], assignments=assignments)
    return node
