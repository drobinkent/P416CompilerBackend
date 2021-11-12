# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = welcome_from_dict(json.loads(json_string))

from dataclasses import dataclass
from typing import Any, List, Union, TypeVar, Type, cast, Callable


T = TypeVar("T")


def from_bool(x: Any) -> bool:
    assert isinstance(x, bool)
    return x


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


@dataclass
class SupportedDataTypes:
    header_field: bool
    standard_metadata: bool
    local_metadata: bool
    constant: bool
    register: bool

    @staticmethod
    def from_dict(obj: Any) -> 'SupportedDataTypes':
        assert isinstance(obj, dict)
        header_field = from_bool(obj.get("header-field"))
        standard_metadata = from_bool(obj.get("standard-metadata"))
        local_metadata = from_bool(obj.get("local-metadata"))
        constant = from_bool(obj.get("constant"))
        register = from_bool(obj.get("register"))
        return SupportedDataTypes(header_field, standard_metadata, local_metadata, constant, register)

    def to_dict(self) -> dict:
        result: dict = {}
        result["header-field"] = from_bool(self.header_field)
        result["standard-metadata"] = from_bool(self.standard_metadata)
        result["local-metadata"] = from_bool(self.local_metadata)
        result["constant"] = from_bool(self.constant)
        result["register"] = from_bool(self.register)
        return result


@dataclass
class ALUInstructionParameter:
    name: str
    bitwidth: int
    supported_data_types: SupportedDataTypes

    @staticmethod
    def from_dict(obj: Any) -> 'ALUInstructionParameter':
        assert isinstance(obj, dict)
        name = from_str(obj.get("name"))
        bitwidth = from_int(obj.get("bitwidth"))
        supported_data_types = SupportedDataTypes.from_dict(obj.get("SupportedDataTypes"))
        return ALUInstructionParameter(name, bitwidth, supported_data_types)

    def to_dict(self) -> dict:
        result: dict = {}
        result["name"] = from_str(self.name)
        result["bitwidth"] = from_int(self.bitwidth)
        result["SupportedDataTypes"] = to_class(SupportedDataTypes, self.supported_data_types)
        return result


@dataclass
class ALUInstruction:
    name: str
    alu_bitwidth: int
    op: List[str]
    parameters: List[ALUInstructionParameter]

    @staticmethod
    def from_dict(obj: Any) -> 'ALUInstruction':
        assert isinstance(obj, dict)
        name = from_str(obj.get("name"))
        alu_bitwidth = from_int(obj.get("ALUBitwidth"))
        op = from_list(from_str, obj.get("op"))
        parameters = from_list(ALUInstructionParameter.from_dict, obj.get("parameters"))
        return ALUInstruction(name, alu_bitwidth, op, parameters)

    def to_dict(self) -> dict:
        result: dict = {}
        result["name"] = from_str(self.name)
        result["ALUBitwidth"] = from_int(self.alu_bitwidth)
        result["op"] = from_list(from_str, self.op)
        result["parameters"] = from_list(lambda x: to_class(ALUInstructionParameter, x), self.parameters)
        return result


@dataclass
class ExternInstructionParameter:
    name: str
    bitwidth: Union[int, str]
    supported_data_types: SupportedDataTypes

    @staticmethod
    def from_dict(obj: Any) -> 'ExternInstructionParameter':
        assert isinstance(obj, dict)
        name = from_str(obj.get("name"))
        bitwidth = from_union([from_int, from_str], obj.get("bitwidth"))
        supported_data_types = SupportedDataTypes.from_dict(obj.get("SupportedDataTypes"))
        return ExternInstructionParameter(name, bitwidth, supported_data_types)

    def to_dict(self) -> dict:
        result: dict = {}
        result["name"] = from_str(self.name)
        result["bitwidth"] = from_union([from_int, from_str], self.bitwidth)
        result["SupportedDataTypes"] = to_class(SupportedDataTypes, self.supported_data_types)
        return result


@dataclass
class ExternInstruction:
    name: str
    op: str
    extern_bitwidth: int
    parameters: List[ExternInstructionParameter]

    @staticmethod
    def from_dict(obj: Any) -> 'ExternInstruction':
        assert isinstance(obj, dict)
        name = from_str(obj.get("name"))
        op = from_str(obj.get("op"))
        extern_bitwidth = from_int(obj.get("ExternBitwidth"))
        parameters = from_list(ExternInstructionParameter.from_dict, obj.get("parameters"))
        return ExternInstruction(name, op, extern_bitwidth, parameters)

    def to_dict(self) -> dict:
        result: dict = {}
        result["name"] = from_str(self.name)
        result["op"] = from_str(self.op)
        result["ExternBitwidth"] = from_int(self.extern_bitwidth)
        result["parameters"] = from_list(lambda x: to_class(ExternInstructionParameter, x), self.parameters)
        return result


@dataclass
class RMTV1InstrctionSet:
    name: str
    alu_instructions: List[ALUInstruction]
    extern_instructions: List[ExternInstruction]

    @staticmethod
    def from_dict(obj: Any) -> 'RMTV1InstrctionSet':
        assert isinstance(obj, dict)
        name = from_str(obj.get("Name"))
        alu_instructions = from_list(ALUInstruction.from_dict, obj.get("ALUInstructions"))
        extern_instructions = from_list(ExternInstruction.from_dict, obj.get("ExternInstructions"))
        return RMTV1InstrctionSet(name, alu_instructions, extern_instructions)

    def to_dict(self) -> dict:
        result: dict = {}
        result["Name"] = from_str(self.name)
        result["ALUInstructions"] = from_list(lambda x: to_class(ALUInstruction, x), self.alu_instructions)
        result["ExternInstructions"] = from_list(lambda x: to_class(ExternInstruction, x), self.extern_instructions)
        return result


def RMTV1InstrctionSet_from_dict(s: Any) -> RMTV1InstrctionSet:
    return RMTV1InstrctionSet.from_dict(s)


def RMTV1InstrctionSet_to_dict(x: RMTV1InstrctionSet) -> Any:
    return to_class(RMTV1InstrctionSet, x)
