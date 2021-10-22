from enum import Enum


class P4ProgramNodeType(Enum):
    ACTION_NODE = "action_node"
    TABLE_NODE = "table_node"
    SUPER_TABLE_NODE = "super_table_node"
    CONDITIONAL_NODE = "conditionals"
    DUMMY_NODE = "dummy_node"
    PRIMITIVE_OP_NODE = "primitive_op_node"
    EXPRESSION_NODE = "expression"

class PipelineID(Enum):
    INGRESS_PIPELINE = "ingress"
    EGRESS_PIPELINE = "egress"

class DependencyType(Enum):
    MATCH_DEPENDENCY = "match_dependency"
    ACTION_DEPENDENCY = "action_dependency"
    SUCCESOR_DEPENDENCY = "successor_dependency"
    REVERSE_MATCH_DEPENDENCY = "reverse_match_dependency"
    EXPRESSION_DEPENDENCY = "expression_dependency" # WHen an expression requires more than one stage that creates a expression depednecy . such as a+b+c a+b and +c there is a expression
    #dependency between the node represented by (a+b) and c
    STAEFUL_MEMORY_DEPENDENCY = "stateful_memory_dependency" # If 2 nodes access same stateful memory then these 2 have stateful memory dependency
    DUMMY_DEPENDENCY_TO_START = "dummy_dependency_to_start"
    DUMMY_DEPENDENCY_TO_END = "dummy_dependency_to_end"