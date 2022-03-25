# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = welcome_from_dict(json.loads(json_string))

from dataclasses import dataclass
from typing import Any, List, TypeVar, Type, cast, Callable


T = TypeVar("T")


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_bool(x: Any) -> bool:
    assert isinstance(x, bool)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


class HeaderVectorSpec:
    bit_width: int
    count: int
    alu: str

    def __init__(self, bit_width: int, count: int, alu: str) -> None:
        self.bit_width = bit_width
        self.count = count
        self.alu = alu

    @staticmethod
    def from_dict(obj: Any) -> 'HeaderVectorSpec':
        assert isinstance(obj, dict)
        bit_width = from_int(obj.get("BitWidth"))
        count = from_int(obj.get("Count"))
        alu = from_str(obj.get("ALU"))
        return HeaderVectorSpec(bit_width, count, alu)

    def to_dict(self) -> dict:
        result: dict = {}
        result["BitWidth"] = from_int(self.bit_width)
        result["Count"] = from_int(self.count)
        result["ALU"] = from_str(self.alu)
        return result


@dataclass
class Resource:
    name: str
    count: int

    @staticmethod
    def from_dict(obj: Any) -> 'Resource':
        assert isinstance(obj, dict)
        name = from_str(obj.get("name"))
        count = from_int(obj.get("count"))
        return Resource(name, count)

    def to_dict(self) -> dict:
        result: dict = {}
        result["name"] = from_str(self.name)
        result["count"] = from_int(self.count)
        return result


@dataclass
class PerSRAMMatBlockSpec:
    sram_bit_width: int
    hashing_way: int

    @staticmethod
    def from_dict(obj: Any) -> 'PerSRAMMatBlockSpec':
        assert isinstance(obj, dict)
        sram_bit_width = from_int(obj.get("SRAMBitWidth"))
        hashing_way = from_int(obj.get("HashingWay"))
        return PerSRAMMatBlockSpec(sram_bit_width, hashing_way)

    def to_dict(self) -> dict:
        result: dict = {}
        result["SRAMBitWidth"] = from_int(self.sram_bit_width)
        result["HashingWay"] = from_int(self.hashing_way)
        return result


@dataclass
class SupportedMatchTypes:
    exact: bool
    lpm: bool
    range: bool
    ternary: bool

    @staticmethod
    def from_dict(obj: Any) -> 'SupportedMatchTypes':
        assert isinstance(obj, dict)
        exact = from_bool(obj.get("exact"))
        lpm = from_bool(obj.get("lpm"))
        range = from_bool(obj.get("range"))
        ternary = from_bool(obj.get("ternary"))
        return SupportedMatchTypes(exact, lpm, range, ternary)

    def to_dict(self) -> dict:
        result: dict = {}
        result["exact"] = from_bool(self.exact)
        result["lpm"] = from_bool(self.lpm)
        result["range"] = from_bool(self.range)
        result["ternary"] = from_bool(self.ternary)
        return result


@dataclass
class SRAMMatResources:
    # sram_mat_field_count: int
    match_crossbar_bit_width: int
    block_count: int
    supported_match_types: SupportedMatchTypes
    per_sram_mat_block_spec: PerSRAMMatBlockSpec

    @staticmethod
    def from_dict(obj: Any) -> 'SRAMMatResources':
        assert isinstance(obj, dict)
        # sram_mat_field_count = from_int(obj.get("SRAMMatFieldCount"))
        match_crossbar_bit_width = from_int(obj.get("MatchCrossbarBitWidth"))
        block_count = from_int(obj.get("BlockCount"))
        supported_match_types = SupportedMatchTypes.from_dict(obj.get("SupportedMatchTypes"))
        per_sram_mat_block_spec = PerSRAMMatBlockSpec.from_dict(obj.get("PerSRAMMatBlockSpec"))
        # return SRAMMatResources(sram_mat_field_count, match_crossbar_bit_width, block_count, supported_match_types, per_sram_mat_block_spec)
        return SRAMMatResources( match_crossbar_bit_width, block_count, supported_match_types, per_sram_mat_block_spec)

    def to_dict(self) -> dict:
        result: dict = {}
        # result["SRAMMatFieldCount"] = from_int(self.sram_mat_field_count)
        result["MatchCrossbarBitWidth"] = from_int(self.match_crossbar_bit_width)
        result["BlockCount"] = from_int(self.block_count)
        result["SupportedMatchTypes"] = to_class(SupportedMatchTypes, self.supported_match_types)
        result["PerSRAMMatBlockSpec"] = to_class(PerSRAMMatBlockSpec, self.per_sram_mat_block_spec)
        return result


@dataclass
class SRAMResources:
    memory_port_width: int
    memory_port_count: int
    memory_block_count: int
    memory_block_bit_width: int
    memoroy_block_row_count: int

    @staticmethod
    def from_dict(obj: Any) -> 'SRAMResources':
        assert isinstance(obj, dict)
        memory_port_width = from_int(obj.get("MemoryPortWidth"))
        memory_port_count = from_int(obj.get("MemoryPortCount"))
        memory_block_count = from_int(obj.get("MemoryBlockCount"))
        memory_block_bit_width = from_int(obj.get("MemoryBlockBitWidth"))
        memoroy_block_row_count = from_int(obj.get("MemoroyBlockRowCount"))
        return SRAMResources(memory_port_width, memory_port_count, memory_block_count, memory_block_bit_width, memoroy_block_row_count)

    def to_dict(self) -> dict:
        result: dict = {}
        result["MemoryPortWidth"] = from_int(self.memory_port_width)
        result["MemoryPortCount"] = from_int(self.memory_port_count)
        result["MemoryBlockCount"] = from_int(self.memory_block_count)
        result["MemoryBlockBitWidth"] = from_int(self.memory_block_bit_width)
        result["MemoroyBlockRowCount"] = from_int(self.memoroy_block_row_count)
        return result


@dataclass
class PerTCAMMatBlockSpec:
    tcam_bit_width: int
    tcam_row_count: int

    @staticmethod
    def from_dict(obj: Any) -> 'PerTCAMMatBlockSpec':
        assert isinstance(obj, dict)
        tcam_bit_width = from_int(obj.get("TCAMBitWidth"))
        tcam_row_count = from_int(obj.get("TCAMRowCount"))
        return PerTCAMMatBlockSpec(tcam_bit_width, tcam_row_count)

    def to_dict(self) -> dict:
        result: dict = {}
        result["TCAMBitWidth"] = from_int(self.tcam_bit_width)
        result["TCAMRowCount"] = from_int(self.tcam_row_count)
        return result


@dataclass
class TCAMMatResources:
    # tcam_mat_field_count: int
    match_crossbar_bit_width: int
    block_count: int
    supported_match_types: SupportedMatchTypes
    per_tcam_mat_block_spec: PerTCAMMatBlockSpec

    @staticmethod
    def from_dict(obj: Any) -> 'TCAMMatResources':
        assert isinstance(obj, dict)
        # tcam_mat_field_count = from_int(obj.get("TCAMMatFieldCount"))
        match_crossbar_bit_width = from_int(obj.get("MatchCrossbarBitWidth"))
        block_count = from_int(obj.get("BlockCount"))
        supported_match_types = SupportedMatchTypes.from_dict(obj.get("SupportedMatchTypes"))
        per_tcam_mat_block_spec = PerTCAMMatBlockSpec.from_dict(obj.get("PerTCAMMatBlockSpec"))
        # return TCAMMatResources(tcam_mat_field_count, match_crossbar_bit_width, block_count, supported_match_types, per_tcam_mat_block_spec)
        return TCAMMatResources( match_crossbar_bit_width, block_count, supported_match_types, per_tcam_mat_block_spec)


    def to_dict(self) -> dict:
        result: dict = {}
        # result["TCAMMatFieldCount"] = from_int(self.tcam_mat_field_count)
        result["MatchCrossbarBitWidth"] = from_int(self.match_crossbar_bit_width)
        result["BlockCount"] = from_int(self.block_count)
        result["SupportedMatchTypes"] = to_class(SupportedMatchTypes, self.supported_match_types)
        result["PerTCAMMatBlockSpec"] = to_class(PerTCAMMatBlockSpec, self.per_tcam_mat_block_spec)
        return result
class RegisterExtern:
    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    @staticmethod
    def from_dict(obj: Any) -> 'RegisterExtern':
        assert isinstance(obj, dict)
        name = from_str(obj.get("name"))
        return RegisterExtern(name)

    def to_dict(self) -> dict:
        result: dict = {}
        result["name"] = from_str(self.name)
        return result


class ExternResources:
    register_extern: List[RegisterExtern]

    def __init__(self, register_extern: List[RegisterExtern]) -> None:
        self.register_extern = register_extern

    @staticmethod
    def from_dict(obj: Any) -> 'ExternResources':
        assert isinstance(obj, dict)
        register_extern = from_list(RegisterExtern.from_dict, obj.get("RegisterExtern"))
        return ExternResources(register_extern)

    def to_dict(self) -> dict:
        result: dict = {}
        result["RegisterExtern"] = from_list(lambda x: to_class(RegisterExtern, x), self.register_extern)
        return result

class StageDescription:
    index: str
    per_mat_instruction_memory_capacity: int
    action_crossbar_bit_width: int
    # action_memory_block_width: int
    # action_memory_block_bitwdith: int
    maximum_actions_supported: int
    sram_resources: SRAMResources
    tcam_mat_resources: TCAMMatResources
    sram_mat_resources: SRAMMatResources
    # alu_resources: List[Resource]
    extern_resources: ExternResources

    def __init__(self, index: str, per_mat_instruction_memory_capacity: int, action_crossbar_bit_width: int,  sram_resources: SRAMResources, tcam_mat_resources: TCAMMatResources, sram_mat_resources: SRAMMatResources,  extern_resources: List[Resource]) -> None:
        self.index = index
        self.per_mat_instruction_memory_capacity = per_mat_instruction_memory_capacity
        self.action_crossbar_bit_width = action_crossbar_bit_width
        # self.action_memory_block_width = action_memory_block_width
        # self.action_memory_block_bitwdith = action_memory_block_bitwdith
        self.sram_resources = sram_resources
        self.tcam_mat_resources = tcam_mat_resources
        self.sram_mat_resources = sram_mat_resources
        # self.alu_resources = alu_resources
        self.extern_resources = extern_resources

    @staticmethod
    def from_dict(obj: Any) -> 'StageDescription':
        assert isinstance(obj, dict)
        index = from_str(obj.get("Index"))
        per_mat_instruction_memory_capacity = from_int(obj.get("PerMATInstructionMemoryCapacity"))
        action_crossbar_bit_width = from_int(obj.get("ActionCrossbarBitWidth"))
        # action_memory_block_width = from_int(obj.get("ActionMemoryBlockWidth"))
        # action_memory_block_bitwdith = from_int(obj.get("ActionMemoryBlockBitwdith"))
        sram_resources = SRAMResources.from_dict(obj.get("SRAMResources"))
        tcam_mat_resources = TCAMMatResources.from_dict(obj.get("TCAMMatResources"))
        sram_mat_resources = SRAMMatResources.from_dict(obj.get("SRAMMatResources"))
        # alu_resources = from_list(Resource.from_dict, obj.get("ALUResources"))
        extern_resources = ExternResources.from_dict(obj.get("ExternResources"))
        return StageDescription(index, per_mat_instruction_memory_capacity, action_crossbar_bit_width,  sram_resources, tcam_mat_resources, sram_mat_resources,  extern_resources)

    def to_dict(self) -> dict:
        result: dict = {}
        result["Index"] = from_str(self.index)
        result["PerMATInstructionMemoryCapacity"] = from_int(self.per_mat_instruction_memory_capacity)
        result["ActionCrossbarBitWidth"] = from_int(self.action_crossbar_bit_width)
        # result["ActionMemoryBlockWidth"] = from_int(self.action_memory_block_width)
        # result["ActionMemoryBlockBitwdith"] = from_int(self.action_memory_block_bitwdith)
        result["SRAMResources"] = to_class(SRAMResources, self.sram_resources)
        result["TCAMMatResources"] = to_class(TCAMMatResources, self.tcam_mat_resources)
        result["SRAMMatResources"] = to_class(SRAMMatResources, self.sram_mat_resources)
        # result["ALUResources"] = from_list(lambda x: to_class(Resource, x), self.alu_resources)
        result["ExternResources"] = to_class(ExternResources, self.extern_resources)
        return result

class ParserSpecs:
    parsing_rate: int
    header_identification_buffer_size: int
    max_identifieable_header: int
    max_move_ahead_bit: int
    tcam_length: int
    tcam_lookup_field_count: int
    tcam_lookup_field_width: int
    max_extractable_data: int

    def __init__(self, parsing_rate: int, header_identification_buffer_size: int, max_identifieable_header: int, max_move_ahead_bit: int, tcam_length: int, tcam_lookup_field_count: int, tcam_lookup_field_width: int, max_extractable_data: int) -> None:
        self.parsing_rate = parsing_rate
        self.header_identification_buffer_size = header_identification_buffer_size
        self.max_identifieable_header = max_identifieable_header
        self.max_move_ahead_bit = max_move_ahead_bit
        self.tcam_length = tcam_length
        self.tcam_lookup_field_count = tcam_lookup_field_count
        self.tcam_lookup_field_width = tcam_lookup_field_width
        self.max_extractable_data = max_extractable_data

    @staticmethod
    def from_dict(obj: Any) -> 'ParserSpecs':
        assert isinstance(obj, dict)
        parsing_rate = from_int(obj.get("ParsingRate"))
        header_identification_buffer_size = from_int(obj.get("HeaderIdentificationBufferSize"))
        max_identifieable_header = from_int(obj.get("MaxIdentifieableHeader"))
        max_move_ahead_bit = from_int(obj.get("MaxMoveAheadBit"))
        tcam_length = from_int(obj.get("TCAMLength"))
        tcam_lookup_field_count = from_int(obj.get("TCAMLookupFieldCount"))
        tcam_lookup_field_width = from_int(obj.get("TCAMLookupFieldWidth"))
        max_extractable_data = from_int(obj.get("MaxExtractableData"))
        return ParserSpecs(parsing_rate, header_identification_buffer_size, max_identifieable_header, max_move_ahead_bit, tcam_length, tcam_lookup_field_count, tcam_lookup_field_width, max_extractable_data)

    def to_dict(self) -> dict:
        result: dict = {}
        result["ParsingRate"] = from_int(self.parsing_rate)
        result["HeaderIdentificationBufferSize"] = from_int(self.header_identification_buffer_size)
        result["MaxIdentifieableHeader"] = from_int(self.max_identifieable_header)
        result["MaxMoveAheadBit"] = from_int(self.max_move_ahead_bit)
        result["TCAMLength"] = from_int(self.tcam_length)
        result["TCAMLookupFieldCount"] = from_int(self.tcam_lookup_field_count)
        result["TCAMLookupFieldWidth"] = from_int(self.tcam_lookup_field_width)
        result["MaxExtractableData"] = from_int(self.max_extractable_data)
        return result

class DependencyDelayInCycleLegth:
    match_dependency: int
    action_dependency: int
    successor_dependency: int
    reverse_match_dependency: int
    default_dependency: int

    def __init__(self, match_dependency: int, action_dependency: int, successor_dependency: int, reverse_match_dependency: int, default: int) -> None:
        self.match_dependency = match_dependency
        self.action_dependency = action_dependency
        self.successor_dependency = successor_dependency
        self.reverse_match_dependency = reverse_match_dependency
        self.default_dependency = default

    @staticmethod
    def from_dict(obj: Any) -> 'DependencyDelayInCycleLegth':
        assert isinstance(obj, dict)
        match_dependency = from_int(obj.get("match_dependency"))
        action_dependency = from_int(obj.get("action_dependency"))
        successor_dependency = from_int(obj.get("successor_dependency"))
        reverse_match_dependency = from_int(obj.get("reverse_match_dependency"))
        default = from_int(obj.get("default"))
        return DependencyDelayInCycleLegth(match_dependency, action_dependency, successor_dependency, reverse_match_dependency, default)

    def to_dict(self) -> dict:
        result: dict = {}
        result["match_dependency"] = from_int(self.match_dependency)
        result["action_dependency"] = from_int(self.action_dependency)
        result["successor_dependency"] = from_int(self.successor_dependency)
        result["reverse_match_dependency"] = from_int(self.reverse_match_dependency)
        result["default"] = from_int(self.default_dependency)
        return result



@dataclass
class RMTV1HardwareConfiguration:
    name: str
    clock_rate: int
    total_stages: int
    header_vector_specs: List[HeaderVectorSpec]
    parser_specs: ParserSpecs
    stage_description: List[StageDescription]
    single_stage_cycle_length: int
    dependency_delay_in_cycle_legth: DependencyDelayInCycleLegth

    def __init__(self, name: str, clock_rate: int, total_stages: int, header_vector_specs: List[HeaderVectorSpec], parser_specs: ParserSpecs, stage_description: List[StageDescription], single_stage_cycle_length: int, dependency_delay_in_cycle_legth: DependencyDelayInCycleLegth) -> None:
        self.name = name
        self.clock_rate = clock_rate
        self.total_stages = total_stages
        self.header_vector_specs = header_vector_specs
        self.parser_specs = parser_specs
        self.stage_description = stage_description
        self.single_stage_cycle_length = single_stage_cycle_length
        self.dependency_delay_in_cycle_legth = dependency_delay_in_cycle_legth

    @staticmethod
    def from_dict(obj: Any) -> 'RMTV1HardwareConfiguration':
        assert isinstance(obj, dict)
        name = from_str(obj.get("Name"))
        clock_rate = from_int(obj.get("ClockRate"))
        total_stages = from_int(obj.get("TotalStages"))
        header_vector_specs = from_list(HeaderVectorSpec.from_dict, obj.get("HeaderVectorSpecs"))
        parser_specs = ParserSpecs.from_dict(obj.get("ParserSpecs"))
        stage_description = from_list(StageDescription.from_dict, obj.get("StageDescription"))
        single_stage_cycle_length = from_int(obj.get("SingleStageCycleLength"))
        dependency_delay_in_cycle_legth = DependencyDelayInCycleLegth.from_dict(obj.get("DependencyDelayInCycleLegth"))
        return RMTV1HardwareConfiguration(name, clock_rate, total_stages, header_vector_specs, parser_specs, stage_description, single_stage_cycle_length, dependency_delay_in_cycle_legth)

    def to_dict(self) -> dict:
        result: dict = {}
        result["Name"] = from_str(self.name)
        result["ClockRate"] = from_int(self.clock_rate)
        result["TotalStages"] = from_int(self.total_stages)
        result["HeaderVectorSpecs"] = from_list(lambda x: to_class(HeaderVectorSpec, x), self.header_vector_specs)
        result["ParserSpecs"] = to_class(ParserSpecs, self.parser_specs)
        result["StageDescription"] = from_list(lambda x: to_class(StageDescription, x), self.stage_description)
        result["SingleStageCycleLength"] = from_int(self.single_stage_cycle_length)
        result["DependencyDelayInCycleLegth"] = to_class(DependencyDelayInCycleLegth, self.dependency_delay_in_cycle_legth)
        return result


def RMTV1HardwareConfiguration_from_dict(s: Any) -> RMTV1HardwareConfiguration:
    return RMTV1HardwareConfiguration.from_dict(s)


def RMTV1HardwareConfiguration_to_dict(x: RMTV1HardwareConfiguration) -> Any:
    return to_class(RMTV1HardwareConfiguration, x)
