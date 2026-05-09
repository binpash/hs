from pash_annotations.annotation_generation.annotation_generators.InputOutputInfoGenerator_Interface import InputOutputInfoGeneratorInterface

from pash_annotations.annotation_generation.annotation_generators.TeraSeqCommon import (
    OTHER_OUTPUT,
    STREAM_INPUT,
    flag_names,
    operand_names,
    set_operand_types,
)


class InputOutputInfoGeneratorGunzip(InputOutputInfoGeneratorInterface):
    def generate_info(self) -> None:
        names = operand_names(self)
        writes_stdout = any(name in {"-c", "--stdout", "--to-stdout"} for name in flag_names(self))

        if not names:
            self.set_implicit_use_of_stdin()
            self.set_implicit_use_of_stdout()
            return

        if writes_stdout:
            self.set_implicit_use_of_stdout()
            set_operand_types(self, {index: STREAM_INPUT for index, _ in enumerate(names)})
        else:
            self.input_output_info.operand_list_typer = [OTHER_OUTPUT] * len(names)
