import os

from pash_annotations.annotation_generation.annotation_generators.ParallelizabilityInfoGenerator_Interface import (
    ParallelizabilityInfoGeneratorInterface,
)
from pash_annotations.annotation_generation.annotation_generators.TeraSeqCommon import (
    flag_names,
    operand_names,
    option_map,
)
from pash_annotations.annotation_generation.datatypes.parallelizability.AggregatorSpec import (
    make_aggregator_spec_custom_2_ary_from_string_representation,
)
from pash_annotations.annotation_generation.datatypes.parallelizability.MapperSpec import (
    make_mapper_spec_custom,
)
from pash_annotations.annotation_generation.datatypes.parallelizability.Parallelizer import (
    make_parallelizer_consec_chunks,
)
from pash_annotations.annotation_generation.datatypes.parallelizability.TransformerFlagOptionList import (
    TransformerFlagOptionListRemove,
)


SUBCOMMANDS = {"view", "sort", "index"}
UNSUPPORTED_SORT_OPTIONS = {
    "-o",
    "--output",
    "-O",
    "--output-fmt",
    "-T",
    "--write-index",
    "-t",
}
MAPPER_OPTIONS_TO_REMOVE = {
    "-@",
    "--threads",
    # The mapper writes to PaSh-managed temporary outputs. Reusing a fixed sort
    # temp prefix across shards can collide, so only opt in when PaSh owns temps.
    "-T",
}


def subcommand_from_flags_or_operands(generator):
    flags = set(flag_names(generator))
    for subcommand in SUBCOMMANDS:
        if subcommand in flags:
            return subcommand
    names = operand_names(generator)
    if names and names[0] in SUBCOMMANDS:
        return names[0]
    return None


class ParallelizabilityInfoGeneratorSamtools(ParallelizabilityInfoGeneratorInterface):
    def generate_info(self) -> None:
        if os.environ.get("PASH_SAMTOOLS_SORT_PARALLEL") != "1":
            return

        if subcommand_from_flags_or_operands(self) != "sort":
            return

        flags = set(flag_names(self))
        options = set(option_map(self))
        if (flags | options) & UNSUPPORTED_SORT_OPTIONS:
            return

        aggregator_cmd = (
            "samtools-sort-name-merge" if "-n" in flags else "samtools-sort-merge"
        )
        aggregator_spec = make_aggregator_spec_custom_2_ary_from_string_representation(
            cmd_inv_as_str=aggregator_cmd,
            is_implemented=True,
        )
        mapper_spec = make_mapper_spec_custom(
            spec_mapper_cmd_name=None,
            flag_option_list_transformer=TransformerFlagOptionListRemove(
                list(MAPPER_OPTIONS_TO_REMOVE)
            ),
            is_implemented=True,
        )
        self.set_commutative()
        self.append_to_parallelizer_list(
            make_parallelizer_consec_chunks(
                mapper_spec=mapper_spec,
                aggregator_spec=aggregator_spec,
            )
        )
