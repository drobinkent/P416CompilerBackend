# # To use this code, make sure you
# #
# #     import json
# #
# # and then, to convert JSON from a string, do
# #
# #     result = ParsedP416Program_from_dict(json.loads(json_string))
# 
# from enum import Enum
# from dataclasses import dataclass
# from typing import List, Any, Union, Optional, Dict, TypeVar, Callable, Type, cast
#
#
# T = TypeVar("T")
# EnumT = TypeVar("EnumT", bound=Enum)
#
#
# def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
#     assert isinstance(x, list)
#     return [f(y) for y in x]
#
#
# def from_str(x: Any) -> str:
#     assert isinstance(x, str)
#     return x
#
#
# def to_enum(c: Type[EnumT], x: Any) -> EnumT:
#     assert isinstance(x, c)
#     return x.value
#
#
# def to_class(c: Type[T], x: Any) -> dict:
#     assert isinstance(x, c)
#     return cast(Any, x).to_dict()
#
#
# def from_union(fs, x):
#     print("X is "+str(x))
#     print("fs are "+str(fs))
#     for f in fs:
#         try:
#             return f(x)
#         except:
#             pass
#     assert False
#
#
# def from_none(x: Any) -> Any:
#     assert x is None
#     return x
#
#
# def from_int(x: Any) -> int:
#     assert isinstance(x, int) and not isinstance(x, bool)
#     return x
#
#
# def from_bool(x: Any) -> bool:
#     assert isinstance(x, bool)
#     return x
#
#
# def from_dict(f: Callable[[Any], T], x: Any) -> Dict[str, T]:
#     assert isinstance(x, dict)
#     return { k: f(v) for (k, v) in x.items() }
#
#
# class PrimitiveOp(Enum):
#     ADD_HEADER = "add_header"
#     ASSIGN = "assign"
#     CLONE_EGRESS_PKT_TO_EGRESS = "clone_egress_pkt_to_egress"
#     COUNT = "count"
#     EXECUTE_METER = "execute_meter"
#     EXIT = "exit"
#     MARK_TO_DROP = "mark_to_drop"
#     MODIFY_FIELD_WITH_HASH_BASED_OFFSET = "modify_field_with_hash_based_offset"
#     RECIRCULATE = "recirculate"
#     REGISTER_READ = "register_read"
#     REGISTER_WRITE = "register_write"
#     REMOVE_HEADER = "remove_header"
#
#
# class ValueType(Enum):
#     CALCULATION = "calculation"
#     COUNTER_ARRAY = "counter_array"
#     EXPRESSION = "expression"
#     FIELD = "field"
#     HEADER = "header"
#     HEXSTR = "hexstr"
#     METER_ARRAY = "meter_array"
#     REGISTER_ARRAY = "register_array"
#     RUNTIME_DATA = "runtime_data"
#
#
# class PurpleType(Enum):
#     EXPRESSION = "expression"
#     FIELD = "field"
#     LOCAL = "local"
#
#
# class ParserOpOp(Enum):
#     EXTRACT = "extract"
#     SET = "set"
#
#
# class TentacledType(Enum):
#     FIELD = "field"
#     HEXSTR = "hexstr"
#     REGULAR = "regular"
#
#
# @dataclass
# class Element:
#     type: ValueType
#     value: List[str]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Element':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = from_list(from_str, obj.get("value"))
#         return Element(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = from_list(from_str, self.value)
#         return result
#
#
# class PurpleOp(Enum):
#     B2_D = "b2d"
#     EMPTY = "&"
#
#
# class RightValueEnum(Enum):
#     THE_0_X2 = "0x2"
#     THE_0_XFFFFFFFF = "0xffffffff"
#     THE_0_XFFFFFFFFFFFF = "0xffffffffffff"
#
#
# @dataclass
# class PurpleRight:
#     type: ValueType
#     value: RightValueEnum
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'PurpleRight':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = RightValueEnum(obj.get("value"))
#         return PurpleRight(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = to_enum(RightValueEnum, self.value)
#         return result
#
#
# @dataclass
# class StickyValue:
#     op: PurpleOp
#     left: Element
#     right: PurpleRight
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'StickyValue':
#         assert isinstance(obj, dict)
#         op = PurpleOp(obj.get("op"))
#         left = Element.from_dict(obj.get("left"))
#         right = PurpleRight.from_dict(obj.get("right"))
#         return StickyValue(op, left, right)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["op"] = to_enum(PurpleOp, self.op)
#         result["left"] = to_class(Element, self.left)
#         result["right"] = to_class(PurpleRight, self.right)
#         return result
#
#
# @dataclass
# class FluffyLeft:
#     type: ValueType
#     value: Union[List[str], StickyValue]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'FluffyLeft':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = from_union([lambda x: from_list(from_str, x), StickyValue.from_dict], obj.get("value"))
#         return FluffyLeft(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = from_union([lambda x: from_list(from_str, x), lambda x: to_class(StickyValue, x)], self.value)
#         return result
#
#
# class FluffyOp(Enum):
#     EMPTY = "+"
#     OP = "-"
#     PURPLE = ">>"
#
#
# class TentacledOp(Enum):
#     D2_B = "d2b"
#     EMPTY = "-"
#
#
# @dataclass
# class IfCondValue:
#     op: TentacledOp
#     right: Element
#     left: Optional[Element] = None
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'IfCondValue':
#         assert isinstance(obj, dict)
#         op = TentacledOp(obj.get("op"))
#         right = Element.from_dict(obj.get("right"))
#         left = from_union([Element.from_dict, from_none], obj.get("left"))
#         return IfCondValue(op, right, left)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["op"] = to_enum(TentacledOp, self.op)
#         result["right"] = to_class(Element, self.right)
#         result["left"] = from_union([lambda x: to_class(Element, x), from_none], self.left)
#         return result
#
#
# @dataclass
# class IfCond:
#     type: ValueType
#     value: IfCondValue
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'IfCond':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = IfCondValue.from_dict(obj.get("value"))
#         return IfCond(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = to_class(IfCondValue, self.value)
#         return result
#
#
# @dataclass
# class HilariousValue:
#     op: PurpleOp
#     left: IfCond
#     right: PurpleRight
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'HilariousValue':
#         assert isinstance(obj, dict)
#         op = PurpleOp(obj.get("op"))
#         left = IfCond.from_dict(obj.get("left"))
#         right = PurpleRight.from_dict(obj.get("right"))
#         return HilariousValue(op, left, right)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["op"] = to_enum(PurpleOp, self.op)
#         result["left"] = to_class(IfCond, self.left)
#         result["right"] = to_class(PurpleRight, self.right)
#         return result
#
#
# @dataclass
# class StickyLeft:
#     type: ValueType
#     value: HilariousValue
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'StickyLeft':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = HilariousValue.from_dict(obj.get("value"))
#         return StickyLeft(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = to_class(HilariousValue, self.value)
#         return result
#
#
# @dataclass
# class IndecentValue:
#     op: FluffyOp
#     left: StickyLeft
#     right: PurpleRight
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'IndecentValue':
#         assert isinstance(obj, dict)
#         op = FluffyOp(obj.get("op"))
#         left = StickyLeft.from_dict(obj.get("left"))
#         right = PurpleRight.from_dict(obj.get("right"))
#         return IndecentValue(op, left, right)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["op"] = to_enum(FluffyOp, self.op)
#         result["left"] = to_class(StickyLeft, self.left)
#         result["right"] = to_class(PurpleRight, self.right)
#         return result
#
#
# @dataclass
# class TentacledLeft:
#     type: ValueType
#     value: IndecentValue
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'TentacledLeft':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = IndecentValue.from_dict(obj.get("value"))
#         return TentacledLeft(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = to_class(IndecentValue, self.value)
#         return result
#
#
# @dataclass
# class IndigoValue:
#     op: PurpleOp
#     left: TentacledLeft
#     right: PurpleRight
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'IndigoValue':
#         assert isinstance(obj, dict)
#         op = PurpleOp(obj.get("op"))
#         left = TentacledLeft.from_dict(obj.get("left"))
#         right = PurpleRight.from_dict(obj.get("right"))
#         return IndigoValue(op, left, right)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["op"] = to_enum(PurpleOp, self.op)
#         result["left"] = to_class(TentacledLeft, self.left)
#         result["right"] = to_class(PurpleRight, self.right)
#         return result
#
#
# @dataclass
# class FluffyRight:
#     type: ValueType
#     value: Union[List[str], IndigoValue, str]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'FluffyRight':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = from_union([lambda x: from_list(from_str, x), IndigoValue.from_dict, from_str], obj.get("value"))
#         return FluffyRight(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = from_union([lambda x: from_list(from_str, x), lambda x: to_class(IndigoValue, x), from_str], self.value)
#         return result
#
#
# @dataclass
# class TentacledValue:
#     op: FluffyOp
#     left: FluffyLeft
#     right: FluffyRight
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'TentacledValue':
#         assert isinstance(obj, dict)
#         op = FluffyOp(obj.get("op"))
#         left = FluffyLeft.from_dict(obj.get("left"))
#         right = FluffyRight.from_dict(obj.get("right"))
#         return TentacledValue(op, left, right)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["op"] = to_enum(FluffyOp, self.op)
#         result["left"] = to_class(FluffyLeft, self.left)
#         result["right"] = to_class(FluffyRight, self.right)
#         return result
#
#
# @dataclass
# class PurpleLeft:
#     type: PurpleType
#     value: Union[List[str], TentacledValue, int]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'PurpleLeft':
#         assert isinstance(obj, dict)
#         type = PurpleType(obj.get("type"))
#         value = from_union([lambda x: from_list(from_str, x), from_int, TentacledValue.from_dict], obj.get("value"))
#         return PurpleLeft(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(PurpleType, self.type)
#         result["value"] = from_union([lambda x: from_list(from_str, x), from_int, lambda x: to_class(TentacledValue, x)], self.value)
#         return result
#
#
# class FluffyType(Enum):
#     BOOL = "bool"
#     HEXSTR = "hexstr"
#
#
# class ValueValueEnum(Enum):
#     THE_0_XFF = "0xff"
#     THE_0_XFFFF = "0xffff"
#     THE_0_XFFFFFFFF = "0xffffffff"
#     THE_0_XFFFFFFFFFFFF = "0xffffffffffff"
#
# class ValueEnum(Enum):
#     THE_0_XFF = "0xff"
#     THE_0_XFFFF = "0xffff"
#     THE_0_XFFFFFFFF = "0xffffffff"
#     THE_0_XFFFFFFFFFFFF = "0xffffffffffff"
#
#
# @dataclass
# class TentacledRight:
#     type: FluffyType
#     value: Union[bool, ValueEnum]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'TentacledRight':
#         assert isinstance(obj, dict)
#         type = FluffyType(obj.get("type"))
#         value = from_union([from_bool, ValueEnum], obj.get("value"))
#         return TentacledRight(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(FluffyType, self.type)
#         result["value"] = from_union([from_bool, lambda x: to_enum(ValueEnum, x)], self.value)
#         return result
#
#
# @dataclass
# class FluffyValue:
#     op: TentacledOp
#     right: TentacledRight
#     left: Optional[PurpleLeft] = None
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'FluffyValue':
#         assert isinstance(obj, dict)
#         op = TentacledOp(obj.get("op"))
#         right = TentacledRight.from_dict(obj.get("right"))
#         left = from_union([from_none, PurpleLeft.from_dict], obj.get("left"))
#         return FluffyValue(op, right, left)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["op"] = to_enum(TentacledOp, self.op)
#         result["right"] = to_class(TentacledRight, self.right)
#         result["left"] = from_union([from_none, lambda x: to_class(PurpleLeft, x)], self.left)
#         return result
#
#
# @dataclass
# class PurpleValue:
#     type: ValueType
#     value: FluffyValue
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'PurpleValue':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = FluffyValue.from_dict(obj.get("value"))
#         return PurpleValue(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = to_class(FluffyValue, self.value)
#         return result
#
# class Calculation:
#     def __init__(self):
#         pass
#
#
# # class CounterArray:
# #     def __init__(self):
# #         pass
# @dataclass
# class Value3:
#     op: str
#     left: IfCond
#     right: IfCond
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Value3':
#         assert isinstance(obj, dict)
#         op = from_str(obj.get("op"))
#         left = IfCond.from_dict(obj.get("left"))
#         right = IfCond.from_dict(obj.get("right"))
#         return Value3(op, left, right)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["op"] = from_str(self.op)
#         result["left"] = to_class(IfCond, self.left)
#         result["right"] = to_class(IfCond, self.right)
#         return result
#
# @dataclass
# class FriskyLeft:
#     type: ValueType
#     value: Value3
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'FriskyLeft':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = Value3.from_dict(obj.get("value"))
#         return FriskyLeft(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = to_class(Value3, self.value)
#         return result
#
#
# @dataclass
# class Value2:
#     op: str
#     left: FriskyLeft
#     right: IfCond
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Value2':
#         assert isinstance(obj, dict)
#         op = from_str(obj.get("op"))
#         left = FriskyLeft.from_dict(obj.get("left"))
#         right = IfCond.from_dict(obj.get("right"))
#         return Value2(op, left, right)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["op"] = from_str(self.op)
#         result["left"] = to_class(FriskyLeft, self.left)
#         result["right"] = to_class(IfCond, self.right)
#         return result
#
# @dataclass
# class CunningRight:
#     type: ValueType
#     value: Union[List[str], Value2, str]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'CunningRight':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = from_union([lambda x: from_list(from_str, x), Value2.from_dict, from_str], obj.get("value"))
#         return CunningRight(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = from_union([lambda x: from_list(from_str, x), lambda x: to_class(Value2, x), from_str], self.value)
#         return result
#
# @dataclass
# class StickyRight:
#     type: ValueType
#     value: Union[List[str], IfCondValue]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'StickyRight':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = from_union([lambda x: from_list(from_str, x), IfCondValue.from_dict], obj.get("value"))
#         return StickyRight(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = from_union([lambda x: from_list(from_str, x), lambda x: to_class(IfCondValue, x)], self.value)
#         return result
#
#
# @dataclass
# class MagentaValue:
#     op: str
#     right: StickyRight
#     left: Optional[IfCond] = None
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'MagentaValue':
#         assert isinstance(obj, dict)
#         op = from_str(obj.get("op"))
#         right = StickyRight.from_dict(obj.get("right"))
#         left = from_union([from_none, IfCond.from_dict], obj.get("left"))
#         return MagentaValue(op, right, left)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["op"] = from_str(self.op)
#         result["right"] = to_class(StickyRight, self.right)
#         result["left"] = from_union([from_none, lambda x: to_class(IfCond, x)], self.left)
#         return result
#
# @dataclass
# class HilariousLeft:
#     type: ValueType
#     value: Union[List[str], MagentaValue]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'HilariousLeft':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = from_union([lambda x: from_list(from_str, x), MagentaValue.from_dict], obj.get("value"))
#         return HilariousLeft(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = from_union([lambda x: from_list(from_str, x), lambda x: to_class(MagentaValue, x)], self.value)
#         return result
#
# @dataclass
# class RightElement:
#     type: TentacledType
#     value: Union[List[str], str]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'RightElement':
#         assert isinstance(obj, dict)
#         type = TentacledType(obj.get("type"))
#         value = from_union([lambda x: from_list(from_str, x), from_str], obj.get("value"))
#         return RightElement(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(TentacledType, self.type)
#         result["value"] = from_union([lambda x: from_list(from_str, x), from_str], self.value)
#         return result
#
# @dataclass
# class AmbitiousLeft:
#     type: ValueType
#     value: Union[List[str], IndecentValue]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'AmbitiousLeft':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = from_union([IndecentValue.from_dict, lambda x: from_list(from_str, x)], obj.get("value"))
#         return AmbitiousLeft(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = from_union([lambda x: to_class(IndecentValue, x), lambda x: from_list(from_str, x)], self.value)
#         return result
#
# @dataclass
# class FriskyValue:
#     op: str
#     right: RightElement
#     left: Optional[AmbitiousLeft] = None
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'FriskyValue':
#         assert isinstance(obj, dict)
#         op = from_str(obj.get("op"))
#         right = RightElement.from_dict(obj.get("right"))
#         left = from_union([AmbitiousLeft.from_dict, from_none], obj.get("left"))
#         return FriskyValue(op, right, left)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["op"] = from_str(self.op)
#         result["right"] = to_class(RightElement, self.right)
#         result["left"] = from_union([lambda x: to_class(AmbitiousLeft, x), from_none], self.left)
#         return result
#
# @dataclass
# class IndigoRight:
#     type: ValueType
#     value: Union[List[str], FriskyValue]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'IndigoRight':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = from_union([FriskyValue.from_dict, lambda x: from_list(from_str, x)], obj.get("value"))
#         return IndigoRight(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = from_union([lambda x: to_class(FriskyValue, x), lambda x: from_list(from_str, x)], self.value)
#         return result
#
# @dataclass
# class CunningValue:
#     op: str
#     right: IndigoRight
#     left: Optional[HilariousLeft] = None
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'CunningValue':
#         assert isinstance(obj, dict)
#         op = from_str(obj.get("op"))
#         right = IndigoRight.from_dict(obj.get("right"))
#         left = from_union([HilariousLeft.from_dict, from_none], obj.get("left"))
#         return CunningValue(op, right, left)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["op"] = from_str(self.op)
#         result["right"] = to_class(IndigoRight, self.right)
#         result["left"] = from_union([lambda x: to_class(HilariousLeft, x), from_none], self.left)
#         return result
#
#
# @dataclass
# class IndecentLeft:
#     type: ValueType
#     value: Union[List[str], CunningValue]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'IndecentLeft':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = from_union([CunningValue.from_dict, lambda x: from_list(from_str, x)], obj.get("value"))
#         return IndecentLeft(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = from_union([lambda x: to_class(CunningValue, x), lambda x: from_list(from_str, x)], self.value)
#         return result
#
#
#
# @dataclass
# class MischievousValue:
#     op: str
#     right: RightElement
#     left: Optional[Element] = None
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'MischievousValue':
#         assert isinstance(obj, dict)
#         op = from_str(obj.get("op"))
#         right = RightElement.from_dict(obj.get("right"))
#         left = from_union([Element.from_dict, from_none], obj.get("left"))
#         return MischievousValue(op, right, left)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["op"] = from_str(self.op)
#         result["right"] = to_class(RightElement, self.right)
#         result["left"] = from_union([lambda x: to_class(Element, x), from_none], self.left)
#         return result
#
#
# @dataclass
# class IndecentRight:
#     type: ValueType
#     value: Union[List[str], MischievousValue, str]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'IndecentRight':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = from_union([lambda x: from_list(from_str, x), MischievousValue.from_dict, from_str], obj.get("value"))
#         return IndecentRight(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = from_union([lambda x: from_list(from_str, x), lambda x: to_class(MischievousValue, x), from_str], self.value)
#         return result
#
#
# @dataclass
# class AmbitiousValue:
#     op: str
#     right: IndecentRight
#     left: Optional[IndecentLeft] = None
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'AmbitiousValue':
#         assert isinstance(obj, dict)
#         op = from_str(obj.get("op"))
#         right = IndecentRight.from_dict(obj.get("right"))
#         left = from_union([from_none, IndecentLeft.from_dict], obj.get("left"))
#         return AmbitiousValue(op, right, left)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["op"] = from_str(self.op)
#         result["right"] = to_class(IndecentRight, self.right)
#         result["left"] = from_union([from_none, lambda x: to_class(IndecentLeft, x)], self.left)
#         return result
#
# @dataclass
# class IndigoLeft:
#     type: ValueType
#     value: Union[List[str], AmbitiousValue]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'IndigoLeft':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = from_union([AmbitiousValue.from_dict, lambda x: from_list(from_str, x)], obj.get("value"))
#         return IndigoLeft(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = from_union([lambda x: to_class(AmbitiousValue, x), lambda x: from_list(from_str, x)], self.value)
#         return result
#
# @dataclass
# class ExpressionValue:
#     op: str
#     right: CunningRight
#     left: Optional[IndigoLeft] = None
#
#     def __init__(self,op, right, left):
#         self.op = op
#         self.right = right
#         self.left = left
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'ExpressionValue':
#         assert isinstance(obj, dict)
#         op = from_str(obj.get("op"))
#         right = CunningRight.from_dict(obj.get("right"))
#         left = from_union([from_none, IndigoLeft.from_dict], obj.get("left"))
#         return ExpressionValue(op, right, left)
#
# class Expression:
#     type: ValueType
#     value: ExpressionValue
#
#     # def __init__(self,type, value):
#     #     self.type = type
#     #     self.value = value
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Expression':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = ExpressionValue.from_dict(obj.get("value"))
#         value = obj.get("value")
#         return Expression(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = to_class(ExpressionValue, self.value)
#         return result
#
#
#
# class Field:
#     def __init__(self):
#         pass
#
# class Hexstr:
#     def __init__(self):
#         pass
#
# class MeterArray:
#     def __init__(self):
#         pass
#
# class RegisterArray:
#     def __init__(self):
#         pass
#
# class RuntimeData:
#     def __init__(self):
#         pass
#
# @dataclass
# class SourceInfo:
#     filename: str
#     line: int
#     column: int
#     source_fragment: str
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'SourceInfo':
#         assert isinstance(obj, dict)
#         filename = from_str(obj.get("filename"))
#         line = from_int(obj.get("line"))
#         column = from_int(obj.get("column"))
#         source_fragment = from_str(obj.get("source_fragment"))
#         return SourceInfo(filename, line, column, source_fragment)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["filename"] = to_enum(Program, self.filename)
#         result["line"] = from_int(self.line)
#         result["column"] = from_int(self.column)
#         result["source_fragment"] = from_str(self.source_fragment)
#         return result
#
# @dataclass
# class CounterArray:
#     name: str
#     id: int
#     source_info: SourceInfo
#     is_direct: bool
#     binding: Optional[str] = None
#     size: Optional[int] = None
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'CounterArray':
#         assert isinstance(obj, dict)
#         name = from_str(obj.get("name"))
#         id = from_int(obj.get("id"))
#         source_info = SourceInfo.from_dict(obj.get("source_info"))
#         is_direct = from_bool(obj.get("is_direct"))
#         binding = from_union([from_str, from_none], obj.get("binding"))
#         size = from_union([from_int, from_none], obj.get("size"))
#         return CounterArray(name, id, source_info, is_direct, binding, size)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["name"] = from_str(self.name)
#         result["id"] = from_int(self.id)
#         result["source_info"] = to_class(SourceInfo, self.source_info)
#         result["is_direct"] = from_bool(self.is_direct)
#         result["binding"] = from_union([from_str, from_none], self.binding)
#         result["size"] = from_union([from_int, from_none], self.size)
#         return result
#
# @dataclass()
# class PrimitiveHeader:
#     value: str
#     # id: int
#     # header_type: str
#     # metadata: bool
#     # pi_omit: bool
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Header':
#         assert isinstance(obj, dict)
#         # name = from_str(obj.get("name"))
#         # id = from_int(obj.get("id"))
#         # header_type = from_str(obj.get("header_type"))
#         # metadata = from_bool(obj.get("metadata"))
#         # pi_omit = from_bool(obj.get("pi_omit"))
#         # return Header(name, id, header_type, metadata, pi_omit)
#         value = from_str(obj.get("value"))
#         return  PrimitiveHeader(value)
#
# @dataclass
# class PrimitiveParameter:
#     type: ValueType
#     value: Union[Calculation, RuntimeData, RegisterArray, MeterArray, Hexstr, Field, Expression, CounterArray]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'PrimitiveParameter':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         if (type == ValueType.CALCULATION):
#             value = Calculation()
#         elif (type == ValueType.COUNTER_ARRAY):
#             value = CounterArray.from_dict(obj)
#         elif (type == ValueType.EXPRESSION):
#             value = Expression.from_dict(obj)
#         elif (type == ValueType.FIELD):
#             value = Field()
#         elif (type == ValueType.HEADER):
#             value = PrimitiveHeader.from_dict(obj)
#         elif (type == ValueType.HEXSTR):
#             value = Hexstr()
#         elif (type == ValueType.METER_ARRAY):
#             value = MeterArray()
#         elif (type == ValueType.REGISTER_ARRAY):
#             value = RegisterArray()
#         elif (type == ValueType.RUNTIME_DATA):
#             value = RuntimeData()
#         else:
#             value = str(obj.get("value"))
#
#         return PrimitiveParameter(type, value)
#
#     # @staticmethod
#     # def from_dict(obj: Any) -> 'PrimitiveParameter':
#     #     assert isinstance(obj, dict)
#     #     type = ValueType(obj.get("type"))
#     #     value = from_union([lambda x: from_list(from_str, x), PurpleValue.from_dict, from_int, from_str], obj.get("value"))
#     #     return PrimitiveParameter(type, value)
#
#     # def to_dict(self) -> dict:
#     #     result: dict = {}
#     #     result["type"] = to_enum(ValueType, self.type)
#     #     result["value"] = from_union([lambda x: from_list(from_str, x), lambda x: to_class(PurpleValue, x), from_int, from_str], self.value)
#     #     return result
#
#
# class Program(Enum):
#     P4_SRC_SRC_CONSTANTS_P4 = "p4src/src/CONSTANTS.p4"
#     P4_SRC_SRC_EGRESS_QUEUE_DEPTH_MONITOR_P4 = "p4src/src/egress_queue_depth_monitor.p4"
#     P4_SRC_SRC_EGRESS_RATE_MONITOR_P4 = "p4src/src/egress_rate_monitor.p4"
#     P4_SRC_SRC_INGRESS_RATE_MONITOR_P4 = "p4src/src/ingress_rate_monitor.p4"
#     P4_SRC_SRC_INT_DELAY_PROCESSOR_P4 = "p4src/src/int_delay_processor.p4"
#     P4_SRC_SRC_L2_TERNARY_P4 = "p4src/src/l2_ternary.p4"
#     P4_SRC_SRC_LEAF_DOWNSTREAM_ROUTING_P4 = "p4src/src/leaf_downstream_routing.p4"
#     P4_SRC_SRC_LEAF_P4 = "p4src/src/leaf.p4"
#     P4_SRC_SRC_MY_STATION_P4 = "p4src/src/my_station.p4"
#     P4_SRC_SRC_NDP_P4 = "p4src/src/ndp.p4"
#     P4_SRC_SRC_UPSTREAM_ROUTING_P4 = "p4src/src/upstream_routing.p4"
#
#
#
#
#
# @dataclass
# class Primitive:
#     op: PrimitiveOp
#     parameters: List[PrimitiveParameter]
#     source_info: str
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Primitive':
#         assert isinstance(obj, dict)
#         op = PrimitiveOp(obj.get("op"))
#         parameters = from_list(PrimitiveParameter.from_dict, obj.get("parameters"))
#         source_info = obj.get("source_info")
#         return Primitive(op, parameters, source_info)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["op"] = to_enum(PrimitiveOp, self.op)
#         result["parameters"] = from_list(lambda x: to_class(PrimitiveParameter, x), self.parameters)
#         result["source_info"] = to_class(SourceInfo, self.source_info)
#         return result
#
#
# @dataclass
# class RuntimeDatum:
#     name: str
#     bitwidth: int
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'RuntimeDatum':
#         assert isinstance(obj, dict)
#         name = from_str(obj.get("name"))
#         bitwidth = from_int(obj.get("bitwidth"))
#         return RuntimeDatum(name, bitwidth)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["name"] = from_str(self.name)
#         result["bitwidth"] = from_int(self.bitwidth)
#         return result
#
#
# @dataclass
# class Action:
#     name: str
#     id: int
#     runtime_data: List[RuntimeDatum]
#     primitives: List[Primitive]
#
#
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Action':
#         assert isinstance(obj, dict)
#         name = from_str(obj.get("name"))
#         id = from_int(obj.get("id"))
#         runtime_data = from_list(RuntimeDatum.from_dict, obj.get("runtime_data"))
#         # runtime_data = obj.get("runtime_data") # we do not need to parse the runtime data
#         primitives = from_list(Primitive.from_dict, obj.get("primitives"))
#         return Action(name, id, runtime_data, primitives)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["name"] = from_str(self.name)
#         result["id"] = from_int(self.id)
#         result["runtime_data"] = from_list(lambda x: to_class(RuntimeDatum, x), self.runtime_data)
#         result["primitives"] = from_list(lambda x: to_class(Primitive, x), self.primitives)
#         return result
#
#
# @dataclass
# class Input:
#     type: ValueType
#     value: Union[List[str], str]
#     bitwidth: Optional[int] = None
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Input':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = from_union([lambda x: from_list(from_str, x), from_str], obj.get("value"))
#         bitwidth = from_union([from_int, from_none], obj.get("bitwidth"))
#         return Input(type, value, bitwidth)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = from_union([lambda x: from_list(from_str, x), from_str], self.value)
#         result["bitwidth"] = from_union([from_int, from_none], self.bitwidth)
#         return result
#
#
# @dataclass
# class Calculation:
#     name: str
#     id: int
#     algo: str
#     input: List[Input]
#     source_info: Optional[SourceInfo] = None
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Calculation':
#         assert isinstance(obj, dict)
#         name = from_str(obj.get("name"))
#         id = from_int(obj.get("id"))
#         algo = from_str(obj.get("algo"))
#         input = from_list(Input.from_dict, obj.get("input"))
#         source_info = from_union([SourceInfo.from_dict, from_none], obj.get("source_info"))
#         return Calculation(name, id, algo, input, source_info)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["name"] = from_str(self.name)
#         result["id"] = from_int(self.id)
#         result["algo"] = from_str(self.algo)
#         result["input"] = from_list(lambda x: to_class(Input, x), self.input)
#         result["source_info"] = from_union([lambda x: to_class(SourceInfo, x), from_none], self.source_info)
#         return result
#
#
# @dataclass
# class Checksum:
#     name: str
#     id: int
#     source_info: SourceInfo
#     target: List[str]
#     type: str
#     calculation: str
#     verify: bool
#     update: bool
#     if_cond: IfCond
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Checksum':
#         assert isinstance(obj, dict)
#         name = from_str(obj.get("name"))
#         id = from_int(obj.get("id"))
#         source_info = SourceInfo.from_dict(obj.get("source_info"))
#         target = from_list(from_str, obj.get("target"))
#         type = from_str(obj.get("type"))
#         calculation = from_str(obj.get("calculation"))
#         verify = from_bool(obj.get("verify"))
#         update = from_bool(obj.get("update"))
#         if_cond = IfCond.from_dict(obj.get("if_cond"))
#         return Checksum(name, id, source_info, target, type, calculation, verify, update, if_cond)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["name"] = from_str(self.name)
#         result["id"] = from_int(self.id)
#         result["source_info"] = to_class(SourceInfo, self.source_info)
#         result["target"] = from_list(from_str, self.target)
#         result["type"] = from_str(self.type)
#         result["calculation"] = from_str(self.calculation)
#         result["verify"] = from_bool(self.verify)
#         result["update"] = from_bool(self.update)
#         result["if_cond"] = to_class(IfCond, self.if_cond)
#         return result
#
#
#
#
#
# @dataclass
# class Deparser:
#     name: str
#     id: int
#     source_info: SourceInfo
#     order: List[str]
#     primitives: List[Any]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Deparser':
#         assert isinstance(obj, dict)
#         name = from_str(obj.get("name"))
#         id = from_int(obj.get("id"))
#         source_info = SourceInfo.from_dict(obj.get("source_info"))
#         order = from_list(from_str, obj.get("order"))
#         primitives = from_list(lambda x: x, obj.get("primitives"))
#         return Deparser(name, id, source_info, order, primitives)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["name"] = from_str(self.name)
#         result["id"] = from_int(self.id)
#         result["source_info"] = to_class(SourceInfo, self.source_info)
#         result["order"] = from_list(from_str, self.order)
#         result["primitives"] = from_list(lambda x: x, self.primitives)
#         return result
#
#
# @dataclass
# class FieldList:
#     id: int
#     name: str
#     source_info: SourceInfo
#     elements: List[Element]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'FieldList':
#         assert isinstance(obj, dict)
#         id = from_int(obj.get("id"))
#         name = from_str(obj.get("name"))
#         source_info = SourceInfo.from_dict(obj.get("source_info"))
#         elements = from_list(Element.from_dict, obj.get("elements"))
#         return FieldList(id, name, source_info, elements)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["id"] = from_int(self.id)
#         result["name"] = from_str(self.name)
#         result["source_info"] = to_class(SourceInfo, self.source_info)
#         result["elements"] = from_list(lambda x: to_class(Element, x), self.elements)
#         return result
#
#
# @dataclass
# class HeaderType:
#     name: str
#     id: int
#     fields: List[List[Union[bool, int, str]]]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'HeaderType':
#         assert isinstance(obj, dict)
#         name = from_str(obj.get("name"))
#         id = from_int(obj.get("id"))
#         fields = from_list(lambda x: from_list(lambda x: from_union([from_int, from_bool, from_str], x), x), obj.get("fields"))
#         return HeaderType(name, id, fields)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["name"] = from_str(self.name)
#         result["id"] = from_int(self.id)
#         result["fields"] = from_list(lambda x: from_list(lambda x: from_union([from_int, from_bool, from_str], x), x), self.fields)
#         return result
#
#
# @dataclass
# class Header:
#     name: str
#     id: int
#     header_type: str
#     metadata: bool
#     pi_omit: bool
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Header':
#         assert isinstance(obj, dict)
#         name = from_str(obj.get("name"))
#         id = from_int(obj.get("id"))
#         header_type = from_str(obj.get("header_type"))
#         metadata = from_bool(obj.get("metadata"))
#         pi_omit = from_bool(obj.get("pi_omit"))
#         return Header(name, id, header_type, metadata, pi_omit)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["name"] = from_str(self.name)
#         result["id"] = from_int(self.id)
#         result["header_type"] = from_str(self.header_type)
#         result["metadata"] = from_bool(self.metadata)
#         result["pi_omit"] = from_bool(self.pi_omit)
#         return result
#
#
# @dataclass
# class Meta:
#     version: List[int]
#     compiler: str
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Meta':
#         assert isinstance(obj, dict)
#         version = from_list(from_int, obj.get("version"))
#         compiler = from_str(obj.get("compiler"))
#         return Meta(version, compiler)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["version"] = from_list(from_int, self.version)
#         result["compiler"] = from_str(self.compiler)
#         return result
#
#
# @dataclass
# class MeterArray:
#     name: str
#     id: int
#     source_info: SourceInfo
#     is_direct: bool
#     size: int
#     rate_count: int
#     type: str
#     binding: Optional[str] = None
#     result_target: Optional[List[str]] = None
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'MeterArray':
#         assert isinstance(obj, dict)
#         name = from_str(obj.get("name"))
#         id = from_int(obj.get("id"))
#         source_info = SourceInfo.from_dict(obj.get("source_info"))
#         is_direct = from_bool(obj.get("is_direct"))
#         size = from_int(obj.get("size"))
#         rate_count = from_int(obj.get("rate_count"))
#         type = from_str(obj.get("type"))
#         binding = from_union([from_str, from_none], obj.get("binding"))
#         result_target = from_union([lambda x: from_list(from_str, x), from_none], obj.get("result_target"))
#         return MeterArray(name, id, source_info, is_direct, size, rate_count, type, binding, result_target)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["name"] = from_str(self.name)
#         result["id"] = from_int(self.id)
#         result["source_info"] = to_class(SourceInfo, self.source_info)
#         result["is_direct"] = from_bool(self.is_direct)
#         result["size"] = from_int(self.size)
#         result["rate_count"] = from_int(self.rate_count)
#         result["type"] = from_str(self.type)
#         result["binding"] = from_union([from_str, from_none], self.binding)
#         result["result_target"] = from_union([lambda x: from_list(from_str, x), from_none], self.result_target)
#         return result
#
#
#
#
#
#
#
# @dataclass
# class ParserOp:
#     parameters: List[RightElement]
#     op: ParserOpOp
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'ParserOp':
#         assert isinstance(obj, dict)
#         parameters = from_list(RightElement.from_dict, obj.get("parameters"))
#         op = ParserOpOp(obj.get("op"))
#         return ParserOp(parameters, op)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["parameters"] = from_list(lambda x: to_class(RightElement, x), self.parameters)
#         result["op"] = to_enum(ParserOpOp, self.op)
#         return result
#
#
# class TransitionType(Enum):
#     DEFAULT = "default"
#     HEXSTR = "hexstr"
#
#
# @dataclass
# class Transition:
#     type: TransitionType
#     mask: None
#     value: Optional[str] = None
#     next_state: Optional[str] = None
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Transition':
#         assert isinstance(obj, dict)
#         type = TransitionType(obj.get("type"))
#         mask = from_none(obj.get("mask"))
#         value = from_union([from_none, from_str], obj.get("value"))
#         next_state = from_union([from_none, from_str], obj.get("next_state"))
#         return Transition(type, mask, value, next_state)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(TransitionType, self.type)
#         result["mask"] = from_none(self.mask)
#         result["value"] = from_union([from_none, from_str], self.value)
#         result["next_state"] = from_union([from_none, from_str], self.next_state)
#         return result
#
#
# @dataclass
# class ParseState:
#     name: str
#     id: int
#     parser_ops: List[ParserOp]
#     transitions: List[Transition]
#     transition_key: List[Element]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'ParseState':
#         assert isinstance(obj, dict)
#         name = from_str(obj.get("name"))
#         id = from_int(obj.get("id"))
#         parser_ops = from_list(ParserOp.from_dict, obj.get("parser_ops"))
#         transitions = from_list(Transition.from_dict, obj.get("transitions"))
#         transition_key = from_list(Element.from_dict, obj.get("transition_key"))
#         return ParseState(name, id, parser_ops, transitions, transition_key)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["name"] = from_str(self.name)
#         result["id"] = from_int(self.id)
#         result["parser_ops"] = from_list(lambda x: to_class(ParserOp, x), self.parser_ops)
#         result["transitions"] = from_list(lambda x: to_class(Transition, x), self.transitions)
#         result["transition_key"] = from_list(lambda x: to_class(Element, x), self.transition_key)
#         return result
#
#
# @dataclass
# class Parser:
#     name: str
#     id: int
#     init_state: str
#     parse_states: List[ParseState]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Parser':
#         assert isinstance(obj, dict)
#         name = from_str(obj.get("name"))
#         id = from_int(obj.get("id"))
#         init_state = from_str(obj.get("init_state"))
#         parse_states = from_list(ParseState.from_dict, obj.get("parse_states"))
#         return Parser(name, id, init_state, parse_states)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["name"] = from_str(self.name)
#         result["id"] = from_int(self.id)
#         result["init_state"] = from_str(self.init_state)
#         result["parse_states"] = from_list(lambda x: to_class(ParseState, x), self.parse_states)
#         return result
#
#
# @dataclass
# class Selector:
#     algo: str
#     input: List[Element]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Selector':
#         assert isinstance(obj, dict)
#         algo = from_str(obj.get("algo"))
#         input = from_list(Element.from_dict, obj.get("input"))
#         return Selector(algo, input)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["algo"] = from_str(self.algo)
#         result["input"] = from_list(lambda x: to_class(Element, x), self.input)
#         return result
#
#
# @dataclass
# class ActionProfile:
#     name: str
#     id: int
#     source_info: SourceInfo
#     max_size: int
#     selector: Selector
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'ActionProfile':
#         assert isinstance(obj, dict)
#         name = from_str(obj.get("name"))
#         id = from_int(obj.get("id"))
#         source_info = SourceInfo.from_dict(obj.get("source_info"))
#         max_size = from_int(obj.get("max_size"))
#         selector = Selector.from_dict(obj.get("selector"))
#         return ActionProfile(name, id, source_info, max_size, selector)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["name"] = from_str(self.name)
#         result["id"] = from_int(self.id)
#         result["source_info"] = to_class(SourceInfo, self.source_info)
#         result["max_size"] = from_int(self.max_size)
#         result["selector"] = to_class(Selector, self.selector)
#         return result
#
#
#
#
# @dataclass
# class MagentaLeft:
#     type: ValueType
#     value: Union[List[str], Value2]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'MagentaLeft':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = from_union([lambda x: from_list(from_str, x), Value2.from_dict], obj.get("value"))
#         return MagentaLeft(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = from_union([lambda x: from_list(from_str, x), lambda x: to_class(Value2, x)], self.value)
#         return result
#
#
# @dataclass
# class AmbitiousRight:
#     type: ValueType
#     value: Union[IfCondValue, str]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'AmbitiousRight':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = from_union([IfCondValue.from_dict, from_str], obj.get("value"))
#         return AmbitiousRight(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = from_union([lambda x: to_class(IfCondValue, x), from_str], self.value)
#         return result
#
#
# @dataclass
# class Value1:
#     op: str
#     left: MagentaLeft
#     right: AmbitiousRight
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Value1':
#         assert isinstance(obj, dict)
#         op = from_str(obj.get("op"))
#         left = MagentaLeft.from_dict(obj.get("left"))
#         right = AmbitiousRight.from_dict(obj.get("right"))
#         return Value1(op, left, right)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["op"] = from_str(self.op)
#         result["left"] = to_class(MagentaLeft, self.left)
#         result["right"] = to_class(AmbitiousRight, self.right)
#         return result
#
#
# @dataclass
# class CunningLeft:
#     type: ValueType
#     value: Union[List[str], Value1]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'CunningLeft':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = from_union([lambda x: from_list(from_str, x), Value1.from_dict], obj.get("value"))
#         return CunningLeft(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = from_union([lambda x: from_list(from_str, x), lambda x: to_class(Value1, x)], self.value)
#         return result
#
#
#
#
#
# @dataclass
# class BraggadociousValue:
#     op: str
#     right: CunningRight
#     left: Optional[CunningLeft] = None
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'BraggadociousValue':
#         assert isinstance(obj, dict)
#         op = from_str(obj.get("op"))
#         right = CunningRight.from_dict(obj.get("right"))
#         left = from_union([CunningLeft.from_dict, from_none], obj.get("left"))
#         return BraggadociousValue(op, right, left)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["op"] = from_str(self.op)
#         result["right"] = to_class(CunningRight, self.right)
#         result["left"] = from_union([lambda x: to_class(CunningLeft, x), from_none], self.left)
#         return result
#
#
# @dataclass
# class HilariousRight:
#     type: ValueType
#     value: Union[List[str], BraggadociousValue, str]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'HilariousRight':
#         assert isinstance(obj, dict)
#         type = ValueType(obj.get("type"))
#         value = from_union([lambda x: from_list(from_str, x), BraggadociousValue.from_dict, from_str], obj.get("value"))
#         return HilariousRight(type, value)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["type"] = to_enum(ValueType, self.type)
#         result["value"] = from_union([lambda x: from_list(from_str, x), lambda x: to_class(BraggadociousValue, x), from_str], self.value)
#         return result
#
#
#
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["op"] = from_str(self.op)
#         result["right"] = to_class(CunningRight, self.right)
#         result["left"] = from_union([from_none, lambda x: to_class(IndigoLeft, x)], self.left)
#         return result
#
#
# # @dataclass
# # class Expression:
# #     type: ValueType
# #     value: ExpressionValue
# #
# #     @staticmethod
# #     def from_dict(obj: Any) -> 'Expression':
# #         assert isinstance(obj, dict)
# #         type = ValueType(obj.get("type"))
# #         # value = ExpressionValue.from_dict(obj.get("value"))
# #         value = obj.get("value")
# #         return Expression(type, value)
# #
# #     def to_dict(self) -> dict:
# #         result: dict = {}
# #         result["type"] = to_enum(ValueType, self.type)
# #         result["value"] = to_class(ExpressionValue, self.value)
# #         return result
#
#
# @dataclass
# class Conditional:
#     name: str
#     id: int
#     source_info: SourceInfo
#     expression: Expression
#     true_next: str
#     false_next: Optional[str] = None
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Conditional':
#         assert isinstance(obj, dict)
#         name = from_str(obj.get("name"))
#         id = from_int(obj.get("id"))
#         source_info = SourceInfo.from_dict(obj.get("source_info"))
#         expression = Expression.from_dict(obj.get("expression"))
#         true_next = from_str(obj.get("true_next"))
#         false_next = from_union([from_none, from_str], obj.get("false_next"))
#         return Conditional(name, id, source_info, expression, true_next, false_next)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["name"] = from_str(self.name)
#         result["id"] = from_int(self.id)
#         result["source_info"] = to_class(SourceInfo, self.source_info)
#         result["expression"] = to_class(Expression, self.expression)
#         result["true_next"] = from_str(self.true_next)
#         result["false_next"] = from_union([from_none, from_str], self.false_next)
#         return result
#
#
# @dataclass
# class DefaultEntry:
#     action_id: int
#     action_const: bool
#     action_data: List[Any]
#     action_entry_const: bool
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'DefaultEntry':
#         assert isinstance(obj, dict)
#         action_id = from_int(obj.get("action_id"))
#         action_const = from_bool(obj.get("action_const"))
#         action_data = from_list(lambda x: x, obj.get("action_data"))
#         action_entry_const = from_bool(obj.get("action_entry_const"))
#         return DefaultEntry(action_id, action_const, action_data, action_entry_const)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["action_id"] = from_int(self.action_id)
#         result["action_const"] = from_bool(self.action_const)
#         result["action_data"] = from_list(lambda x: x, self.action_data)
#         result["action_entry_const"] = from_bool(self.action_entry_const)
#         return result
#
#
# class MatchType(Enum):
#     EXACT = "exact"
#     LPM = "lpm"
#     TERNARY = "ternary"
#     RANGE = "range"
#
#
# @dataclass
# class Key:
#     match_type: MatchType
#     name: str
#     target: List[str]
#     mask: None
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Key':
#         assert isinstance(obj, dict)
#         match_type = MatchType(obj.get("match_type"))
#         name = from_str(obj.get("name"))
#         target = from_list(from_str, obj.get("target"))
#         mask = from_none(obj.get("mask"))
#         return Key(match_type, name, target, mask)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["match_type"] = to_enum(MatchType, self.match_type)
#         result["name"] = from_str(self.name)
#         result["target"] = from_list(from_str, self.target)
#         result["mask"] = from_none(self.mask)
#         return result
#
#
# class TableType(Enum):
#     INDIRECT_WS = "indirect_ws"
#     SIMPLE = "simple"
#
#
# @dataclass
# class Table:
#     name: str
#     id: int
#     source_info: SourceInfo
#     key: List[Key]
#     match_type: MatchType
#     type: TableType
#     max_size: int
#     with_counters: bool
#     support_timeout: bool
#     action_ids: List[int]
#     actions: List[str]
#     next_tables: Dict[str, str]
#     direct_meters: Optional[str] = None
#     base_default_next: Optional[str] = None
#     default_entry: Optional[DefaultEntry] = None
#     action_profile: Optional[str] = None
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Table':
#         assert isinstance(obj, dict)
#         name = from_str(obj.get("name"))
#         id = from_int(obj.get("id"))
#         source_info = SourceInfo.from_dict(obj.get("source_info"))
#         key = from_list(Key.from_dict, obj.get("key"))
#         match_type = MatchType(obj.get("match_type"))
#         type = TableType(obj.get("type"))
#         max_size = from_int(obj.get("max_size"))
#         with_counters = from_bool(obj.get("with_counters"))
#         support_timeout = from_bool(obj.get("support_timeout"))
#         action_ids = from_list(from_int, obj.get("action_ids"))
#         actions = from_list(from_str, obj.get("actions"))
#         next_tables = from_dict(lambda x: from_union([from_none, from_str], x), obj.get("next_tables"))
#         direct_meters = from_union([from_none, from_str], obj.get("direct_meters"))
#         base_default_next = from_union([from_none, from_str], obj.get("base_default_next"))
#         default_entry = from_union([DefaultEntry.from_dict, from_none], obj.get("default_entry"))
#         action_profile = from_union([from_str, from_none], obj.get("action_profile"))
#         return Table(name, id, source_info, key, match_type, type, max_size, with_counters, support_timeout, action_ids, actions, next_tables, direct_meters, base_default_next, default_entry, action_profile)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["name"] = from_str(self.name)
#         result["id"] = from_int(self.id)
#         result["source_info"] = to_class(SourceInfo, self.source_info)
#         result["key"] = from_list(lambda x: to_class(Key, x), self.key)
#         result["match_type"] = to_enum(MatchType, self.match_type)
#         result["type"] = to_enum(TableType, self.type)
#         result["max_size"] = from_int(self.max_size)
#         result["with_counters"] = from_bool(self.with_counters)
#         result["support_timeout"] = from_bool(self.support_timeout)
#         result["action_ids"] = from_list(from_int, self.action_ids)
#         result["actions"] = from_list(from_str, self.actions)
#         result["next_tables"] = from_dict(lambda x: from_union([from_none, from_str], x), self.next_tables)
#         result["direct_meters"] = from_union([from_none, from_str], self.direct_meters)
#         result["base_default_next"] = from_union([from_none, from_str], self.base_default_next)
#         result["default_entry"] = from_union([lambda x: to_class(DefaultEntry, x), from_none], self.default_entry)
#         result["action_profile"] = from_union([from_str, from_none], self.action_profile)
#         return result
#
#
# @dataclass
# class Pipeline:
#     name: str
#     id: int
#     source_info: SourceInfo
#     init_table: str
#     tables: List[Table]
#     action_profiles: List[ActionProfile]
#     conditionals: List[Conditional]
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'Pipeline':
#         assert isinstance(obj, dict)
#         name = from_str(obj.get("name"))
#         id = from_int(obj.get("id"))
#         source_info = SourceInfo.from_dict(obj.get("source_info"))
#         init_table = from_str(obj.get("init_table"))
#         tables = from_list(Table.from_dict, obj.get("tables"))
#         action_profiles = from_list(ActionProfile.from_dict, obj.get("action_profiles"))
#         conditionals = from_list(Conditional.from_dict, obj.get("conditionals"))
#         return Pipeline(name, id, source_info, init_table, tables, action_profiles, conditionals)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["name"] = from_str(self.name)
#         result["id"] = from_int(self.id)
#         result["source_info"] = to_class(SourceInfo, self.source_info)
#         result["init_table"] = from_str(self.init_table)
#         result["tables"] = from_list(lambda x: to_class(Table, x), self.tables)
#         result["action_profiles"] = from_list(lambda x: to_class(ActionProfile, x), self.action_profiles)
#         result["conditionals"] = from_list(lambda x: to_class(Conditional, x), self.conditionals)
#         return result
#
#
# @dataclass
# class RegisterArray:
#     name: str
#     id: int
#     source_info: SourceInfo
#     size: int
#     bitwidth: int
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'RegisterArray':
#         assert isinstance(obj, dict)
#         name = from_str(obj.get("name"))
#         id = from_int(obj.get("id"))
#         source_info = SourceInfo.from_dict(obj.get("source_info"))
#         size = from_int(obj.get("size"))
#         bitwidth = from_int(obj.get("bitwidth"))
#         return RegisterArray(name, id, source_info, size, bitwidth)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["name"] = from_str(self.name)
#         result["id"] = from_int(self.id)
#         result["source_info"] = to_class(SourceInfo, self.source_info)
#         result["size"] = from_int(self.size)
#         result["bitwidth"] = from_int(self.bitwidth)
#         return result
#
#
# @dataclass
# class ParsedP416Program:
#     header_types: List[HeaderType]
#     headers: List[Header]
#     header_stacks: List[Any]
#     header_union_types: List[Any]
#     header_unions: List[Any]
#     header_union_stacks: List[Any]
#     field_lists: List[FieldList]
#     errors: List[List[Union[int, str]]]
#     enums: List[Any]
#     parsers: List[Parser]
#     parse_vsets: List[Any]
#     deparsers: List[Deparser]
#     meter_arrays: List[MeterArray]
#     counter_arrays: List[CounterArray]
#     register_arrays: List[RegisterArray]
#     calculations: List[Calculation]
#     learn_lists: List[Any]
#     actions: List[Action]
#     pipelines: List[Pipeline]
#     checksums: List[Checksum]
#     force_arith: List[Any]
#     extern_instances: List[Any]
#     field_aliases: List[List[Union[List[str], str]]]
#     program: Program
#     meta: Meta
#
#     @staticmethod
#     def from_dict(obj: Any) -> 'ParsedP416Program':
#         assert isinstance(obj, dict)
#         header_types = from_list(HeaderType.from_dict, obj.get("header_types"))
#         headers = from_list(Header.from_dict, obj.get("headers"))
#         header_stacks = from_list(lambda x: x, obj.get("header_stacks"))
#         header_union_types = from_list(lambda x: x, obj.get("header_union_types"))
#         header_unions = from_list(lambda x: x, obj.get("header_unions"))
#         header_union_stacks = from_list(lambda x: x, obj.get("header_union_stacks"))
#         field_lists = from_list(FieldList.from_dict, obj.get("field_lists"))
#         errors = from_list(lambda x: from_list(lambda x: from_union([from_int, from_str], x), x), obj.get("errors"))
#         enums = from_list(lambda x: x, obj.get("enums"))
#         parsers = from_list(Parser.from_dict, obj.get("parsers"))
#         parse_vsets = from_list(lambda x: x, obj.get("parse_vsets"))
#         deparsers = from_list(Deparser.from_dict, obj.get("deparsers"))
#         meter_arrays = from_list(MeterArray.from_dict, obj.get("meter_arrays"))
#         counter_arrays = from_list(CounterArray.from_dict, obj.get("counter_arrays"))
#         register_arrays = from_list(RegisterArray.from_dict, obj.get("register_arrays"))
#         calculations = from_list(Calculation.from_dict, obj.get("calculations"))
#         learn_lists = from_list(lambda x: x, obj.get("learn_lists"))
#         actions = from_list(Action.from_dict, obj.get("actions"))
#         pipelines = from_list(Pipeline.from_dict, obj.get("pipelines"))
#         checksums = from_list(Checksum.from_dict, obj.get("checksums"))
#         force_arith = from_list(lambda x: x, obj.get("force_arith"))
#         extern_instances = from_list(lambda x: x, obj.get("extern_instances"))
#         field_aliases = from_list(lambda x: from_list(lambda x: from_union([lambda x: from_list(from_str, x), from_str], x), x), obj.get("field_aliases"))
#         program = Program(obj.get("program"))
#         meta = Meta.from_dict(obj.get("__meta__"))
#         return ParsedP416Program(header_types, headers, header_stacks, header_union_types, header_unions, header_union_stacks, field_lists, errors, enums, parsers, parse_vsets, deparsers, meter_arrays, counter_arrays, register_arrays, calculations, learn_lists, actions, pipelines, checksums, force_arith, extern_instances, field_aliases, program, meta)
#
#     def to_dict(self) -> dict:
#         result: dict = {}
#         result["header_types"] = from_list(lambda x: to_class(HeaderType, x), self.header_types)
#         result["headers"] = from_list(lambda x: to_class(Header, x), self.headers)
#         result["header_stacks"] = from_list(lambda x: x, self.header_stacks)
#         result["header_union_types"] = from_list(lambda x: x, self.header_union_types)
#         result["header_unions"] = from_list(lambda x: x, self.header_unions)
#         result["header_union_stacks"] = from_list(lambda x: x, self.header_union_stacks)
#         result["field_lists"] = from_list(lambda x: to_class(FieldList, x), self.field_lists)
#         result["errors"] = from_list(lambda x: from_list(lambda x: from_union([from_int, from_str], x), x), self.errors)
#         result["enums"] = from_list(lambda x: x, self.enums)
#         result["parsers"] = from_list(lambda x: to_class(Parser, x), self.parsers)
#         result["parse_vsets"] = from_list(lambda x: x, self.parse_vsets)
#         result["deparsers"] = from_list(lambda x: to_class(Deparser, x), self.deparsers)
#         result["meter_arrays"] = from_list(lambda x: to_class(MeterArray, x), self.meter_arrays)
#         result["counter_arrays"] = from_list(lambda x: to_class(CounterArray, x), self.counter_arrays)
#         result["register_arrays"] = from_list(lambda x: to_class(RegisterArray, x), self.register_arrays)
#         result["calculations"] = from_list(lambda x: to_class(Calculation, x), self.calculations)
#         result["learn_lists"] = from_list(lambda x: x, self.learn_lists)
#         result["actions"] = from_list(lambda x: to_class(Action, x), self.actions)
#         result["pipelines"] = from_list(lambda x: to_class(Pipeline, x), self.pipelines)
#         result["checksums"] = from_list(lambda x: to_class(Checksum, x), self.checksums)
#         result["force_arith"] = from_list(lambda x: x, self.force_arith)
#         result["extern_instances"] = from_list(lambda x: x, self.extern_instances)
#         result["field_aliases"] = from_list(lambda x: from_list(lambda x: from_union([lambda x: from_list(from_str, x), from_str], x), x), self.field_aliases)
#         result["program"] = to_enum(Program, self.program)
#         result["__meta__"] = to_class(Meta, self.meta)
#         return result
#
#
# def ParsedP416Program_from_dict(s: Any) -> ParsedP416Program:
#     return ParsedP416Program.from_dict(s)
#
#
# def ParsedP416Program_to_dict(x: ParsedP416Program) -> Any:
#     return to_class(ParsedP416Program, x)
