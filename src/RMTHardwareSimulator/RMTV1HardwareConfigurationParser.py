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


@dataclass
class HeaderVectorSpec:
    bit_width: int
    count: int

    @staticmethod
    def from_dict(obj: Any) -> 'HeaderVectorSpec':
        assert isinstance(obj, dict)
        bit_width = from_int(obj.get("BitWidth"))
        count = from_int(obj.get("Count"))
        return HeaderVectorSpec(bit_width, count)

    def to_dict(self) -> dict:
        result: dict = {}
        result["BitWidth"] = from_int(self.bit_width)
        result["Count"] = from_int(self.count)
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
    sram_mat_field_count: int
    match_crossbar_bit_width: int
    block_count: str
    supported_match_types: SupportedMatchTypes
    per_sram_mat_block_spec: PerSRAMMatBlockSpec

    @staticmethod
    def from_dict(obj: Any) -> 'SRAMMatResources':
        assert isinstance(obj, dict)
        sram_mat_field_count = from_int(obj.get("SRAMMatFieldCount"))
        match_crossbar_bit_width = from_int(obj.get("MatchCrossbarBitWidth"))
        block_count = from_str(obj.get("BlockCount"))
        supported_match_types = SupportedMatchTypes.from_dict(obj.get("SupportedMatchTypes"))
        per_sram_mat_block_spec = PerSRAMMatBlockSpec.from_dict(obj.get("PerSRAMMatBlockSpec"))
        return SRAMMatResources(sram_mat_field_count, match_crossbar_bit_width, block_count, supported_match_types, per_sram_mat_block_spec)

    def to_dict(self) -> dict:
        result: dict = {}
        result["SRAMMatFieldCount"] = from_int(self.sram_mat_field_count)
        result["MatchCrossbarBitWidth"] = from_int(self.match_crossbar_bit_width)
        result["BlockCount"] = from_str(self.block_count)
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
    tcam_mat_field_count: int
    match_crossbar_bit_width: int
    block_count: int
    supported_match_types: SupportedMatchTypes
    per_tcam_mat_block_spec: PerTCAMMatBlockSpec

    @staticmethod
    def from_dict(obj: Any) -> 'TCAMMatResources':
        assert isinstance(obj, dict)
        tcam_mat_field_count = from_int(obj.get("TCAMMatFieldCount"))
        match_crossbar_bit_width = from_int(obj.get("MatchCrossbarBitWidth"))
        block_count = from_int(obj.get("BlockCount"))
        supported_match_types = SupportedMatchTypes.from_dict(obj.get("SupportedMatchTypes"))
        per_tcam_mat_block_spec = PerTCAMMatBlockSpec.from_dict(obj.get("PerTCAMMatBlockSpec"))
        return TCAMMatResources(tcam_mat_field_count, match_crossbar_bit_width, block_count, supported_match_types, per_tcam_mat_block_spec)

    def to_dict(self) -> dict:
        result: dict = {}
        result["TCAMMatFieldCount"] = from_int(self.tcam_mat_field_count)
        result["MatchCrossbarBitWidth"] = from_int(self.match_crossbar_bit_width)
        result["BlockCount"] = from_int(self.block_count)
        result["SupportedMatchTypes"] = to_class(SupportedMatchTypes, self.supported_match_types)
        result["PerTCAMMatBlockSpec"] = to_class(PerTCAMMatBlockSpec, self.per_tcam_mat_block_spec)
        return result


@dataclass
class StageDescription:
    index: str
    action_crossbar_bit_width: int
    sram_resources: SRAMResources
    tcam_mat_resources: TCAMMatResources
    sram_mat_resources: SRAMMatResources
    alu_resources: List[Resource]
    extern_resources: List[Resource]

    @staticmethod
    def from_dict(obj: Any) -> 'StageDescription':
        assert isinstance(obj, dict)
        index = from_str(obj.get("Index"))
        action_crossbar_bit_width = from_int(obj.get("ActionCrossbarBitWidth"))
        sram_resources = SRAMResources.from_dict(obj.get("SRAMResources"))
        tcam_mat_resources = TCAMMatResources.from_dict(obj.get("TCAMMatResources"))
        sram_mat_resources = SRAMMatResources.from_dict(obj.get("SRAMMatResources"))
        alu_resources = from_list(Resource.from_dict, obj.get("ALUResources"))
        extern_resources = from_list(Resource.from_dict, obj.get("ExternResources"))
        return StageDescription(index, action_crossbar_bit_width, sram_resources, tcam_mat_resources, sram_mat_resources, alu_resources, extern_resources)

    def to_dict(self) -> dict:
        result: dict = {}
        result["Index"] = from_str(self.index)
        result["ActionCrossbarBitWidth"] = from_int(self.action_crossbar_bit_width)
        result["SRAMResources"] = to_class(SRAMResources, self.sram_resources)
        result["TCAMMatResources"] = to_class(TCAMMatResources, self.tcam_mat_resources)
        result["SRAMMatResources"] = to_class(SRAMMatResources, self.sram_mat_resources)
        result["ALUResources"] = from_list(lambda x: to_class(Resource, x), self.alu_resources)
        result["ExternResources"] = from_list(lambda x: to_class(Resource, x), self.extern_resources)
        return result


@dataclass
class RMTV1HardwareConfiguration:
    name: str
    total_stages: int
    header_vector_specs: List[HeaderVectorSpec]
    stage_description: List[StageDescription]

    @staticmethod
    def from_dict(obj: Any) -> 'RMTV1HardwareConfiguration':
        assert isinstance(obj, dict)
        name = from_str(obj.get("Name"))
        total_stages = from_int(obj.get("TotalStages"))
        header_vector_specs = from_list(HeaderVectorSpec.from_dict, obj.get("HeaderVectorSpecs"))
        stage_description = from_list(StageDescription.from_dict, obj.get("StageDescription"))
        return RMTV1HardwareConfiguration(name, total_stages, header_vector_specs, stage_description)

    def to_dict(self) -> dict:
        result: dict = {}
        result["Name"] = from_str(self.name)
        result["TotalStages"] = from_int(self.total_stages)
        result["HeaderVectorSpecs"] = from_list(lambda x: to_class(HeaderVectorSpec, x), self.header_vector_specs)
        result["StageDescription"] = from_list(lambda x: to_class(StageDescription, x), self.stage_description)
        return result


def RMTV1HardwareConfiguration_from_dict(s: Any) -> RMTV1HardwareConfiguration:
    return RMTV1HardwareConfiguration.from_dict(s)


def RMTV1HardwareConfiguration_to_dict(x: RMTV1HardwareConfiguration) -> Any:
    return to_class(RMTV1HardwareConfiguration, x)
