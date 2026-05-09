from pash_annotations.annotation_generation.annotation_generators.InputOutputInfoGenerator_Interface import InputOutputInfoGeneratorInterface

from pash_annotations.annotation_generation.annotation_generators.TeraSeqCommon import (
    STREAM_INPUT,
    indexes_after_options,
    operand_names,
    set_operand_types,
)


OPTIONS_WITH_ARGS = {
    "-a",
    "-g",
    "--error-rate",
    "--minimum-length",
    "--output",
    "--overlap",
    "--untrimmed-output",
}


class InputOutputInfoGeneratorCutadapt(InputOutputInfoGeneratorInterface):
    def generate_info(self) -> None:
        names = operand_names(self)
        skip = indexes_after_options(names, OPTIONS_WITH_ARGS)
        typed_indexes = {}

        for index, name in enumerate(names):
            if index in skip or name.startswith("-"):
                continue
            typed_indexes[index] = STREAM_INPUT

        # cutadapt writes its human report to stdout; the benchmark redirects it to logfiles.
        self.set_implicit_use_of_stdout()
        set_operand_types(self, typed_indexes)
