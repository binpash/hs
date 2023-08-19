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


## Returns true if the script is safe to speculate and execute outside
##  of the original shell context.
##
## The script is not safe if it might contain a shell primitive. Therefore
##  the analysis checks if the command in question is one of the underlying
##  shell's primitives (in our case bash) and if so returns False
def safe_to_execute(asts: "list[AstNode]", variables: dict) -> bool:
    ## There should always be a single AST per node and it must be a command
    assert(len(asts) == 1)
    ast = asts[0]
    assert(isinstance(ast, CommandNode))
    logging.debug(f'Ast in question: {ast}')
    ## Expand and check whether the asts contain
    ##  a command substitution or a primitive.
    ## If so, then we need to tell the original script to execute the command.

    ## Expand the command argument
    if (len(ast.arguments) > 0):
        cmd_arg = ast.arguments[0]
        exp_state = expand.ExpansionState(variables)
        ## TODO: Catch exceptions around here
        expanded_cmd_arg = expand.expand_arg(cmd_arg, exp_state)
        cmd_str = string_of_arg(expanded_cmd_arg)
        logging.critical(f'Expanded command argument: {expanded_cmd_arg} (str: "{cmd_str}")')

    ## TODO: Determine if the ast contains a command substitution and if so
    ##        run it in the original script.
    ##       In the future, we should be able to perform stateful expansion too,
    ##        and properly execute and trace command substitutions.

    ## KK 2023-05-26 We need to keep in mind that whenever we execute something
    ##               in the original shell, then we cannot speculate anything
    ##               after it, because we cannot track read-write dependencies
    ##               in the original shell.

        if cmd_str in BASH_PRIMITIVES:
            return False
    
    return True


def parse_and_gather_rw_sets_early(asts, variables: dict) -> "tuple[set[str], set[str]]":
    read_set, write_set = set(), set()
    assert(len(asts) == 1)
    ast = asts[0]
    assert(isinstance(ast, CommandNode))
    logging.debug(f'Ast in question: {ast}')
    if len(ast.arguments) > 0:
        cmd_arg = ast.arguments[0]
        exp_state = expand.ExpansionState(variables)
        expanded_cmd_arg = expand.expand_arg(cmd_arg, exp_state)
        cmd_str = string_of_arg(expanded_cmd_arg)
        # Command cmd assignment
        if len(ast.arguments) == 1:
            return read_set, write_set # TODO
        elif cmd_str in BASH_VAR_ASSIGNMENTS:
            # This will fail if the assignment contains a variable ref
            try:
                expanded_rest_args = [string_of_arg(expand.expand_arg(arg, exp_state)) for arg in ast.arguments[1:]]
            except:
                expanded_rest_args = [string_of_arg(arg) for arg in ast.arguments[1:]]
            read_set, write_set = parse_and_gather_rw_sets_early_command_variable_assignments(expanded_cmd_arg, expanded_rest_args, variables)
            return read_set, write_set
        # We cannot get anything from these primitives
        elif cmd_str in BASH_PRIMITIVES:
            return read_set, write_set
        else: # Other commands
            # This will fail if the assignment contains a variable ref
            try:
                expanded_rest_args = [string_of_arg(expand.expand_arg(arg, exp_state)) for arg in ast.arguments[1:]]
            except:
                expanded_rest_args = [string_of_arg(arg) for arg in ast.arguments[1:]]
            read_set, write_set = parse_and_gather_rw_sets_early_other_commands(expanded_cmd_arg, expanded_rest_args, variables)
            return read_set, write_set
    else:
        exp_state = expand.ExpansionState(variables)
        assignments = ast.assignments
        if len(assignments) > 0:
            read_set, write_set = parse_and_gather_rw_sets_early_simple_variable_assignments(assignments, exp_state)
            return read_set, write_set

# Handles simple cases of variable assignments (e.g. var=val)
def parse_and_gather_rw_sets_early_simple_variable_assignments(assignments: "list[AssignNode]", exp_state: dict) -> "tuple[set[str], set[str]]":
    logging.debug(f'> Simple Variable assignment spotted: {" ".join([assignment.pretty() for assignment in assignments])}')
    # If assigning a value to a variable, then we need to add the variable to the write set
    vars, vals = zip(*[(assignment.pretty().split('=')[0], assignment.pretty().split('=')[1].strip('"').strip("'")) for assignment in assignments])
    # Surround vars with ${} to match the expansion
    vars = {'${' + var + '}' for var in vars}
    variable_vals = {val for val in vals if val.startswith('$') and not val.startswith('$(')} # TODO: more cases
    logging.critical(f"vars & vals: {vars} {variable_vals}")
    return variable_vals, vars

# Handles other cases of variable assignments (e.g. export var=val, declare var=val, etc.)
def parse_and_gather_rw_sets_early_command_variable_assignments(expanded_cmd_arg, expanded_rest_args, variables: dict) -> "tuple[set[str], set[str]]":
    logging.debug(f'> Command variable assignment spotted: {string_of_arg(expanded_cmd_arg)} {" ".join([expanded_rest_arg for expanded_rest_arg in expanded_rest_args])}')
    cmd_str = string_of_arg(expanded_cmd_arg)
    rest_arg_str = " ".join((expanded_rest_args))
    # assign_nodes = [AssignNode(expanded_rest_arg.split('=')[0], expanded_rest_arg.split('=')[1]) for expanded_rest_arg in expanded_rest_args]
    vars, vals = zip(*[(expanded_cmd_arg.split('=')[0], expanded_cmd_arg.split('=')[1].strip('"').strip("'")) for expanded_cmd_arg in expanded_rest_args])
    vars = {'${' + var + '}' for var in vars}
    variable_vals = {val for val in vals if val.startswith('$') and not val.startswith('$(')} # TODO: more cases
    return variable_vals, vars


def parse_and_gather_rw_sets_early_other_commands(expanded_cmd_arg, expanded_rest_args, variables: dict) -> "tuple[set[str], set[str]]":
    logging.debug(f'> Command spotted: {string_of_arg(expanded_cmd_arg)} {" ".join([expanded_rest_arg for expanded_rest_arg in expanded_rest_args])}')

    read_set, write_set = set(), set()

    # Gathering read set
    for expanded_rest_arg in expanded_rest_args:
        if expanded_rest_arg.startswith('$') and not expanded_rest_arg.startswith('$('):
            read_set.add(expanded_rest_arg)

    # GL: Here, we don't modify the write set since we're assuming general commands won't modify shell variables.
    # However, if we have specific commands that we know modify shell variables, 
    # we would handle them here.
    # Write sets will generally be resolved by Riker.
    # TODO maybe for far later: Here, we could even use PaSh's annotations to help us resolve write sets.

    return read_set, write_set
    

BASH_PRIMITIVES = ["break", 
                   "continue", 
                   "return"]

BASH_VAR_ASSIGNMENTS = ["export", 
                        "local", 
                        "readonly", 
                        "typeset", 
                        "declare", 
                        "unset", 
                        # "read"
                        ]


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

