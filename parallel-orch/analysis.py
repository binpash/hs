import logging

import libdash.parser
from shasta.ast_node import *
from shasta.json_to_ast import to_ast_node
from sh_expand import expand

## Keeps track of the first time we call the parser
first_time_calling_parser = True

## Parses straight a shell script to an AST
## through python without calling it as an executable
def parse_shell_to_asts(input_script_path) -> "list[AstNode]":
    global first_time_calling_parser

    try:
        ## The libdash parser must not be initialized when called the second
        ## time because it hangs!
        new_ast_objects = libdash.parser.parse(input_script_path, init=first_time_calling_parser)
        first_time_calling_parser = False

        ## Transform the untyped ast objects to typed ones
        typed_ast_objects = []
        for untyped_ast, _original_text, _linno_before, _linno_after, in new_ast_objects:
             typed_ast = to_ast_node(untyped_ast)
             typed_ast_objects.append(typed_ast)

        return typed_ast_objects
    except libdash.parser.ParsingException as e:
        logging.error(f'Parsing error: {e}')
        exit(1)
        

def validate_node(ast) -> bool:
    assert(isinstance(ast, (CommandNode, PipeNode)))
    if isinstance(ast, CommandNode):
        return True
    else:
        for cmd in ast.items:
            assert isinstance(cmd, CommandNode)


def is_node_safe(node: CommandNode, variables: dict) -> str:
    ## Expand and check whether the asts contain
    ## a command substitution or a primitive.
    ## If so, then we need to tell the original script to execute the command.

    ## Expand the command argument
    cmd_arg = node.arguments[0]
    exp_state = expand.ExpansionState(variables)
    ## TODO: Catch exceptions around here
    expanded_cmd_arg = expand.expand_arg(cmd_arg, exp_state)
    cmd_str = string_of_arg(expanded_cmd_arg)
    logging.debug(f'Expanded command argument: {expanded_cmd_arg} (str: "{cmd_str}")')
    
    ## KK 2023-05-26 We need to keep in mind that whenever we execute something
    ##               in the original shell, then we cannot speculate anything
    ##               after it, because we cannot track read-write dependencies
    ##               in the original shell.
    if cmd_str in BASH_PRIMITIVES:
        return False
    return True


def is_pipe_node_safe_to_execute(node: PipeNode, variables: dict) -> bool:
    for cmd in node.items:
        logging.debug(f'Ast in question: {cmd}')
        if not is_node_safe(cmd, variables):
            return False
    return True

## Returns true if the script is safe to speculate and execute outside
##  of the original shell context.
##
## The script is not safe if it might contain a shell primitive. Therefore
##  the analysis checks if the command in question is one of the underlying
##  shell's primitives (in our case bash) and if so returns False
def safe_to_execute(asts: "list[AstNode]", variables: dict) -> bool:
    ## There should always be a single AST per node and it must be a command
    assert(len(asts) == 1)
    if isinstance(asts[0], PipeNode):
        return is_pipe_node_safe_to_execute(asts[0], variables)
    else:
        assert(isinstance(asts[0], CommandNode))
        logging.debug(f'Ast in question: {asts[0]}')
        return is_node_safe(asts[0], variables)
    ## TODO: Determine if the ast contains a command substitution and if so
    ##        run it in the original script.
    ##       In the future, we should be able to perform stateful expansion too,
    ##        and properly execute and trace command substitutions.


BASH_PRIMITIVES = ["break", 
                   "continue", 
                   "return",
                   "exit"]


safe_cases = {
        "Pipe": (lambda:
                 lambda ast_node: safe_default(ast_node)),
        "Command": (lambda:
                    lambda ast_node: safe_simple(ast_node)),
        "And": (lambda:
                lambda ast_node: safe_default(ast_node)),
        "Or": (lambda:
               lambda ast_node: safe_default(ast_node)),
        "Semi": (lambda:
                 lambda ast_node: safe_default(ast_node)),
        "Redir": (lambda:
                  lambda ast_node: safe_default(ast_node)),
        "Subshell": (lambda:
                     lambda ast_node: safe_default(ast_node)),
        "Background": (lambda:
                       lambda ast_node: safe_default(ast_node)),
        "Defun": (lambda:
                  lambda ast_node: safe_default(ast_node)),
        "For": (lambda:
                  lambda ast_node: safe_default(ast_node)),
        "While": (lambda:
                  lambda ast_node: safe_default(ast_node)),
        "Case": (lambda:
                  lambda ast_node: safe_default(ast_node)),
        "If": (lambda:
                  lambda ast_node: safe_default(ast_node))
        }

def safe_command(command):
    global safe_cases
    return ast_match(command, safe_cases)

def safe_simple(node: CommandNode):
    global BASH_PRIMITIVES

    if (len(node.arguments) <= 0):
        ## KK 2023-05-30 It is unclear if this is ever reachable
        return True

    ## We only care about the command itself
    cmd = expand_arg(node.arguments[0])
    if (cmd in BASH_PRIMITIVES):
        return False
    
    return True 

## By construction we only expect commands in here,
##  and we cannot recursively see the other constructs because of the way we handle
##  backquotes.
def safe_default(node: Command) -> bool:
    return False

