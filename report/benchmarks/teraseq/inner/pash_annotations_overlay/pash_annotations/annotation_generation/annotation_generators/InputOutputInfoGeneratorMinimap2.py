from pash_annotations.annotation_generation.annotation_generators.InputOutputInfoGenerator_Interface import InputOutputInfoGeneratorInterface

from pash_annotations.annotation_generation.annotation_generators.TeraSeqCommon import (
    CONFIG_INPUT,
    OTHER_OUTPUT,
    STREAM_INPUT,
    option_map,
    set_operand_types,
)


class InputOutputInfoGeneratorMinimap2(InputOutputInfoGeneratorInterface):
    def generate_info(self) -> None:
        options = option_map(self)
        if "-d" in options:
            self.input_output_info.operand_list_typer = [OTHER_OUTPUT] * self.get_operand_list_length()
            return

        self.set_implicit_use_of_stdout()
        typed_indexes = {}
        if self.get_operand_list_length() > 0:
            typed_indexes[0] = CONFIG_INPUT
        for index in range(1, self.get_operand_list_length()):
            typed_indexes[index] = STREAM_INPUT
        set_operand_types(self, typed_indexes)
