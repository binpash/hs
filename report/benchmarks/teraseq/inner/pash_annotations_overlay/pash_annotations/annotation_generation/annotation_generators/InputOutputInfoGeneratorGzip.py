from pash_annotations.annotation_generation.annotation_generators.InputOutputInfoGenerator_Interface import InputOutputInfoGeneratorInterface

from pash_annotations.annotation_generation.annotation_generators.TeraSeqCommon import (
    OTHER_OUTPUT,
    STREAM_INPUT,
    flag_names,
    operand_names,
    set_operand_types,
)


class InputOutputInfoGeneratorGzip(InputOutputInfoGeneratorInterface):
    def generate_info(self) -> None:
        names = operand_names(self)
        if self.get_operand_list_length() == 0:
            self.set_implicit_use_of_stdin()
            self.set_implicit_use_of_stdout()
        elif any(name in {"-c", "--stdout", "--to-stdout"} for name in flag_names(self)):
            self.set_implicit_use_of_stdout()
            set_operand_types(self, {index: STREAM_INPUT for index, _ in enumerate(names)})
        else:
            self.input_output_info.operand_list_typer = [OTHER_OUTPUT] * self.get_operand_list_length()
