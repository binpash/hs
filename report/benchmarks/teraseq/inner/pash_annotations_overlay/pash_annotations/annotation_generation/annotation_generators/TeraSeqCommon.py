from pash_annotations.datatypes.AccessKind import (
    make_config_input,
    make_other_output,
    make_stream_input,
    make_stream_output,
)
from pash_annotations.datatypes.BasicDatatypes import WhichClassForArg


ARGSTRING = (WhichClassForArg.ARGSTRING, None)
CONFIG_INPUT = (WhichClassForArg.FILESTD, make_config_input())
OTHER_OUTPUT = (WhichClassForArg.FILESTD, make_other_output())
STREAM_INPUT = (WhichClassForArg.FILESTD, make_stream_input())
STREAM_OUTPUT = (WhichClassForArg.FILESTD, make_stream_output())


def operand_names(generator):
    return [str(operand.get_name()) for operand in generator.cmd_inv.operand_list]


def set_operand_types(generator, typed_indexes):
    names = operand_names(generator)
    operand_types = [ARGSTRING] * len(names)
    for index, operand_type in typed_indexes.items():
        if 0 <= index < len(operand_types):
            operand_types[index] = operand_type
    generator.input_output_info.operand_list_typer = operand_types


def option_map(generator):
    return {
        flag_option.get_name(): flag_option.get_arg()
        for flag_option in generator.cmd_inv.flag_option_list
        if hasattr(flag_option, "get_arg")
    }


def flag_names(generator):
    return [
        str(flag_option.get_name())
        for flag_option in generator.cmd_inv.flag_option_list
        if not hasattr(flag_option, "get_arg")
    ]


def indexes_after_options(names, options_with_args):
    skip = set()
    for index, name in enumerate(names):
        if name in options_with_args and index + 1 < len(names):
            skip.add(index + 1)
    return skip
