import logging

from shasta.ast_node import *
from shasta.json_to_ast import to_ast_node

import libdash.parser

## Keeps track of the first time we call the parser
first_time_calling_parser = True

## Parses straight a shell script to an AST
## through python without calling it as an executable
def parse_shell_to_asts(input_script_path):
    global first_time_calling_parser

    try:
        ## The libdash parser must not be initialized when called the second
        ## time because it hangs!
        new_ast_objects = libdash.parser.parse(input_script_path, init=first_time_calling_parser)
        first_time_calling_parser = False

        ## Transform the untyped ast objects to typed ones
        typed_ast_objects = []
        for untyped_ast, original_text, linno_before, linno_after, in new_ast_objects:
             typed_ast = to_ast_node(untyped_ast)
             typed_ast_objects.append((typed_ast, original_text, linno_before, linno_after))

        return typed_ast_objects
    except libdash.parser.ParsingException as e:
        logging.error(f'Parsing error: {e}')
        exit(1)


## Returns true if the script is safe to speculate and execute outside
##  of the original shell context.
def safe_to_execute(asts) -> bool:
    logging.debug(f'Asts in question: {asts}')
    ## TODO: Expand and check whether the asts contain
    ##  a command substitution or a primitive.
    ## If so, then we need to tell the original script to execute the command.
    ##
    ## TODO: Write my analysis here, then move it to expand, 
    ##       and then move expand to its own library
    ##
    ## TODO: Also, add a test with a break and see it fail
    
    ## TODO: Push the changes that modify the tests to show stderr incrementally

    ## KK 2023-05-26 We need to keep in mind that whenever we execute something
    ##               in the original shell, then we cannot speculate anything
    ##               after it, because we cannot track read-write dependencies
    ##               in the original shell.
    return True

