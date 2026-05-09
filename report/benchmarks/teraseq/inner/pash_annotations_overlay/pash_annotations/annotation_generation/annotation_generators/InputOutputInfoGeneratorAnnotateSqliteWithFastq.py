from pash_annotations.annotation_generation.annotation_generators.InputOutputInfoGenerator_Interface import InputOutputInfoGeneratorInterface

from pash_annotations.annotation_generation.annotation_generators.TeraSeqCommon import (
    ARGSTRING,
    operand_names,
)


class InputOutputInfoGeneratorAnnotateSqliteWithFastq(InputOutputInfoGeneratorInterface):
    def generate_info(self) -> None:
        # File options carry the real IO: --database mutates SQLite state and --ifile is FASTQ input.
        self.input_output_info.operand_list_typer = [ARGSTRING] * len(operand_names(self))
