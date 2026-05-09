from pash_annotations.annotation_generation.annotation_generators.InputOutputInfoGenerator_Interface import InputOutputInfoGeneratorInterface

from pash_annotations.annotation_generation.annotation_generators.TeraSeqCommon import (
    ARGSTRING,
    OTHER_OUTPUT,
    STREAM_INPUT,
    STREAM_OUTPUT,
    flag_names,
    indexes_after_options,
    operand_names,
    option_map,
    set_operand_types,
)


SUBCOMMANDS = {"view", "sort", "index"}
OPTIONS_WITH_ARGS = {
    "-@",
    "--threads",
    "-F",
    "-G",
    "-q",
    "-l",
    "-r",
    "-R",
    "-t",
    "-T",
    "-L",
    "-M",
    "-N",
    "-o",
    "--output",
    "-O",
    "-U",
}


def subcommand_from_flags_or_operands(generator, names):
    for name in flag_names(generator):
        if name in SUBCOMMANDS:
            return name, False
    if names and names[0] in SUBCOMMANDS:
        return names[0], True
    return None, False


class InputOutputInfoGeneratorSamtools(InputOutputInfoGeneratorInterface):
    def generate_info(self) -> None:
        names = operand_names(self)
        subcommand, subcommand_is_operand = subcommand_from_flags_or_operands(self, names)

        if subcommand == "index":
            typed_indexes = {
                index: OTHER_OUTPUT
                for index, name in enumerate(names)
                if not (subcommand_is_operand and index == 0) and not name.startswith("-")
            }
            set_operand_types(self, typed_indexes)
            return

        if subcommand == "sort":
            options = option_map(self)
            skip = indexes_after_options(names, OPTIONS_WITH_ARGS)
            typed_indexes = {}
            saw_stdin = False
            has_output_file = "-o" in options or "--output" in options

            for index, name in enumerate(names):
                if subcommand_is_operand and index == 0:
                    continue
                if index in skip:
                    if index > 0 and names[index - 1] in {"-o", "--output"}:
                        typed_indexes[index] = STREAM_OUTPUT
                        has_output_file = True
                    continue
                if name == "-":
                    saw_stdin = True
                    continue
                if name in {"-o", "--output"} and index + 1 < len(names):
                    typed_indexes[index + 1] = STREAM_OUTPUT
                    skip.add(index + 1)
                    has_output_file = True
                    continue
                if name.startswith("-"):
                    continue
                typed_indexes[index] = STREAM_INPUT

            if saw_stdin or not any(value == STREAM_INPUT for value in typed_indexes.values()):
                self.set_implicit_use_of_stdin()
            if not has_output_file:
                self.set_implicit_use_of_stdout()
            set_operand_types(self, typed_indexes)
            return

        if subcommand == "view":
            options = option_map(self)
            if "-o" not in options and "--output" not in options:
                self.set_implicit_use_of_stdout()
            skip = indexes_after_options(names, OPTIONS_WITH_ARGS)
            typed_indexes = {}
            saw_stdin = False
            for index, name in enumerate(names):
                if subcommand_is_operand and index == 0:
                    continue
                if index in skip:
                    if index > 0 and names[index - 1] in {"-o", "--output"}:
                        typed_indexes[index] = STREAM_OUTPUT
                    continue
                if name == "-":
                    saw_stdin = True
                    continue
                if name in {"-o", "--output"} and index + 1 < len(names):
                    typed_indexes[index + 1] = STREAM_OUTPUT
                    skip.add(index + 1)
                    continue
                if name.startswith("-"):
                    continue
                typed_indexes[index] = STREAM_INPUT
            if not typed_indexes or saw_stdin:
                self.set_implicit_use_of_stdin()
            set_operand_types(self, typed_indexes)
            return

        self.input_output_info.operand_list_typer = [ARGSTRING] * len(names)
