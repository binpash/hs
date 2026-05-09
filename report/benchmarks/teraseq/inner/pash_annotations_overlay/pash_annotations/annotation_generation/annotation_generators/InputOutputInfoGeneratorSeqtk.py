from pash_annotations.annotation_generation.annotation_generators.InputOutputInfoGenerator_Interface import InputOutputInfoGeneratorInterface

from pash_annotations.annotation_generation.annotation_generators.TeraSeqCommon import (
    CONFIG_INPUT,
    STREAM_INPUT,
    operand_names,
    set_operand_types,
)


SUBCOMMANDS = {"subseq"}


class InputOutputInfoGeneratorSeqtk(InputOutputInfoGeneratorInterface):
    def generate_info(self) -> None:
        names = operand_names(self)
        typed_indexes = {}
        data_operands = [
            (index, name)
            for index, name in enumerate(names)
            if not (index == 0 and name in SUBCOMMANDS)
        ]

        if data_operands:
            read_index, read_name = data_operands[0]
            if read_name == "-":
                self.set_implicit_use_of_stdin()
            else:
                typed_indexes[read_index] = STREAM_INPUT

        if len(data_operands) > 1:
            names_index, _ = data_operands[1]
            typed_indexes[names_index] = CONFIG_INPUT

        self.set_implicit_use_of_stdout()
        set_operand_types(self, typed_indexes)
