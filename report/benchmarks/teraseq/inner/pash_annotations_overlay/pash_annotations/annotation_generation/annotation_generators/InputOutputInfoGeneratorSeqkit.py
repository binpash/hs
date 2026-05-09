from pash_annotations.annotation_generation.annotation_generators.InputOutputInfoGenerator_Interface import InputOutputInfoGeneratorInterface

from pash_annotations.annotation_generation.annotation_generators.TeraSeqCommon import (
    CONFIG_INPUT,
    STREAM_INPUT,
    STREAM_OUTPUT,
    flag_names,
    operand_names,
    set_operand_types,
)


SUBCOMMANDS = {"grep", "seq", "subseq"}
OPTIONS_WITH_ARGS = {
    "-f",
    "--pattern-file",
    "-m",
    "-M",
    "-o",
    "--out-file",
    "-r",
}


class InputOutputInfoGeneratorSeqkit(InputOutputInfoGeneratorInterface):
    def generate_info(self) -> None:
        names = operand_names(self)
        typed_indexes = {}
        skip = set()
        has_output_file = False
        subcommand_is_operand = bool(names and names[0] in SUBCOMMANDS)
        subcommand_is_flag = any(name in SUBCOMMANDS for name in flag_names(self))

        for index, name in enumerate(names):
            if subcommand_is_operand and index == 0:
                continue
            if name in {"-o", "--out-file"} and index + 1 < len(names):
                typed_indexes[index + 1] = STREAM_OUTPUT
                skip.add(index + 1)
                has_output_file = True
            elif (name in {"-f", "--pattern-file"} or (name.startswith("-") and "f" in name)) and index + 1 < len(names):
                typed_indexes[index + 1] = CONFIG_INPUT
                skip.add(index + 1)
            elif name in {"-m", "-M", "-r"} and index + 1 < len(names):
                skip.add(index + 1)

        for index, name in enumerate(names):
            if (subcommand_is_operand and index == 0) or index in skip or name.startswith("-"):
                continue
            typed_indexes.setdefault(index, STREAM_INPUT)

        if not has_output_file:
            self.set_implicit_use_of_stdout()
        if not any(value == STREAM_INPUT for value in typed_indexes.values()):
            self.set_implicit_use_of_stdin()
        set_operand_types(self, typed_indexes)
