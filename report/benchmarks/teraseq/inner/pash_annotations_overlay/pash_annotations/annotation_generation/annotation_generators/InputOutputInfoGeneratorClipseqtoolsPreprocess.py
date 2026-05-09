from pash_annotations.annotation_generation.annotation_generators.InputOutputInfoGenerator_Interface import InputOutputInfoGeneratorInterface

from pash_annotations.annotation_generation.annotation_generators.TeraSeqCommon import (
    CONFIG_INPUT,
    OTHER_OUTPUT,
    operand_names,
    set_operand_types,
)


class InputOutputInfoGeneratorClipseqtoolsPreprocess(InputOutputInfoGeneratorInterface):
    def generate_info(self) -> None:
        names = operand_names(self)
        typed_indexes = {}
        skip = set()

        for index, name in enumerate(names):
            if index in skip:
                continue
            if name == "--database" and index + 1 < len(names):
                typed_indexes[index + 1] = OTHER_OUTPUT
                skip.add(index + 1)
            elif name in {"--a_file", "--gtf"} and index + 1 < len(names):
                typed_indexes[index + 1] = CONFIG_INPUT
                skip.add(index + 1)

        set_operand_types(self, typed_indexes)
