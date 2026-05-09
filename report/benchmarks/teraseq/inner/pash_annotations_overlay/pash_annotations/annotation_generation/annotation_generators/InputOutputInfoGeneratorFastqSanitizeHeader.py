from pash_annotations.annotation_generation.annotation_generators.InputOutputInfoGenerator_Interface import InputOutputInfoGeneratorInterface

from pash_annotations.annotation_generation.annotation_generators.TeraSeqCommon import option_map


class InputOutputInfoGeneratorFastqSanitizeHeader(InputOutputInfoGeneratorInterface):
    def generate_info(self) -> None:
        options = option_map(self)
        if "--input" not in options:
            self.set_implicit_use_of_stdin()
        self.set_implicit_use_of_stdout()
        self.set_all_operands_as_config_arg_type_string()
