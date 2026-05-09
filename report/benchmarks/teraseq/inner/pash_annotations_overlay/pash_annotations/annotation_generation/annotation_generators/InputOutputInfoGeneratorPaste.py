from pash_annotations.annotation_generation.annotation_generators.InputOutputInfoGenerator_Interface import InputOutputInfoGeneratorInterface

from pash_annotations.annotation_generation.annotation_generators.TeraSeqCommon import (
    STREAM_INPUT,
    operand_names,
    set_operand_types,
)


class InputOutputInfoGeneratorPaste(InputOutputInfoGeneratorInterface):
    def generate_info(self) -> None:
        names = operand_names(self)
        typed_indexes = {}

        for index, name in enumerate(names):
            if name == "-":
                self.set_implicit_use_of_stdin()
            elif not name.startswith("-"):
                typed_indexes[index] = STREAM_INPUT

        if not names:
            self.set_implicit_use_of_stdin()
        self.set_implicit_use_of_stdout()
        set_operand_types(self, typed_indexes)
