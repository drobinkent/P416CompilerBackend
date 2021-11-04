import logging
import math
from enum import Enum
import sys
from copy import deepcopy

from networkx.drawing.nx_agraph import to_agraph


from P4ProgramParser.P416Bmv2JsonParser.P416JsonParser import Expression, PrimitiveOpblock, PrimitiveField, \
    HexStr, PrimitiveHeader, BoolPrimitive, RegisterArrayPrimitive, PrimitiveOp

sys.path.append("..")
from OldCodes import ConfigurationConstants as confConst
from OldCodes.DependencyAnlyzer.P4TEAnalyzer import MATNode


import networkx as nx
logger = logging.getLogger('DependencyGraphBuilder')
hdlr = logging.FileHandler(confConst.LOG_FILE_PATH )
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)


class P4ProgramNodeType(Enum):
    ACTION_NODE = "action_node"
    TABLE_NODE = "table_node"
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

class Dependency:
    def __init__(self, node1, node2, dependencyType):
        self.node1 = node1
        self.node2 = node2
        self.dependencyType = dependencyType

class HeaderField:

    def __init__(self, name, bitWidth, isSigned):
        self.name = name
        self.bitWidth = bitWidth
        self.isSigned = isSigned
        self.opList = []

    def __str__(self):
        val = ""
        val = val + "Header field Name: "+self.name+" Bitwidth: "+str(self.bitWidth)
        return val

class PipelineGraph:
    def __init__(self, pipelineID,pipeline, actions):
        self.pipelineID = pipelineID
        self.dummyStart = P4ProgramNode(confConst.DUMMY_START_NODE, confConst.DUMMY_START_NODE, P4ProgramNodeType.DUMMY_NODE, pipelineID)
        self.dummyEnd = P4ProgramNode(confConst.DUMMY_END_NODE, confConst.DUMMY_END_NODE,P4ProgramNodeType.DUMMY_NODE, pipelineID)
        self.p4Graph = nx.DiGraph()
        self.p4Graph.add_node(self.dummyStart, label="Start")
        self.p4Graph.add_node(self.dummyEnd, label="End")
        self.pipeline = pipeline
        self.matchDependencyMap = {}
        self.actionDependencyMap = {}
        self.succesorDependencyMap = {}
        self.reverseMatchDependencyMap = {}
        self.alreadyLoadedTables={}
        self.nameToP4NodeMap ={}
        self.actions = actions
        self.registerNameToTableMap = {}
        self.conditionalNodes = {}
        self.matchlessActionNodes = {}
        self.matchActionNodes= {}

    def getActionByName(self, actName):
        for act in self.actions:
            if(act.name == actName):
                return act
        return None

    # def addDependency(self, node1Name, node2Name, dependencyType):
    #     if (dependencyType == DependencyType.MATCH_DEPENDENCY):
    #         dependencyMap = self.matchDependencyMap
    #     elif (dependencyType == DependencyType.ACTION_DEPENDENCY):
    #         dependencyMap = self.actionDependencyMap
    #     elif (dependencyType == DependencyType.SUCCESOR_DEPENDENCY):
    #         dependencyMap =  self.succesorDependencyMap
    #     elif (dependencyType == DependencyType.REVERSE_MATCH_DEPENDENCY):
    #         dependencyMap = self.reverseMatchDependencyMap
    #     val = dependencyMap[node1Name]
    #     if (val ==None):
    #         val = []
    #         val.append(node2Name)
    #         dependencyMap[node1Name] = val
    #     else:
    #         val.append(node2Name)

    def getAllFieldsModifedInActionsOfTheTable(self, tblName):
        tbl = self.pipeline.getTblByName(tblName)
        if(tbl == None):
            return []
        totalFieldList = []
        for a in tbl.actions:
            act = self.getActionByName(a)
            if (act != None):
                newfieldList = act.getListOfFieldsModifedAndUsed()[0]
                totalFieldList = totalFieldList + newfieldList
        return totalFieldList

    def loadNodes(self):


        for tbl in self.pipeline.tables:
            if(len(tbl.key)<=0):
                self.matchlessActionNodes[tbl.name] = tbl
            else:
                self.matchActionNodes[tbl.name]=tbl
        for cond in self.pipeline.conditionals:
            self.conditionalNodes[cond.name] = cond
        logger.info("Total Tables in the pipeline is "+str(len(self.pipeline.tables)))
        logger.info("total number of matchlessActionNodes is "+ str(len(self.matchlessActionNodes)))
        logger.info("total number of match Action Nodes is "+ str(len(self.matchActionNodes)))
        logger.info("total number of conditional Nodes is "+ str(len(self.conditionalNodes)))

    # def analyzeDependency(self):
    #     #checks between all pair (u,v) belongs to unionr of (conditional and tables)
    # 
    #     for tbl1 in self.pipeline.tables:
    #         for tbl2 in self.pipeline.tables:
    #             dependencyType = self.getDependencyType(tbl1,tbl2)
    #             self.addDependency(tbl1.name, tbl2.name, dependencyType)
    #     for tbl in self.pipeline.tables:
    #         for cond in self.pipeline.conditionals:
    #             Here is a big trouble. for conditional and table we need to find their order. This is also true in case of table pairs
    #                 so better way is to keep a map of previously added nodes. if the current node have dependency with one of them then add edge
    #             in the way also handle the expression node. if a node have no dependency with his immediate predeccesor then they can be excecuted parallel.
    #             dependencyType = self.getDependencyType(tbl1,tbl2)
    #             self.addDependency(tbl1.name, tbl2.name, dependencyType)

    def getDependencyType(self, tbl1, tbl2):
        '''
        The order of the tables are important here. tbl1 will be in earlier stages of the program and tble2 should be in later
        :param tbl1:
        :param tbl2:
        :return:
        '''
        pass


    # make a function that will collect all the actions of a table node. if the next tables are actions that means these actions hae to be merged with this table node.
    # then collect each actions next nodes. they are the true next node of the table that have to be embedded on next stage.

    # conditional
    # next node is table --> map to other stage
    # next node is only action --> map to same stage
    # next node is another conditional --> map to next stage
    #
    # table
    # next node is table --> map to other stage
    # next node is only action --> map to same stage
    # next node is  conditional and next node of that conditioanl is simple action --> map to same stage
    # next node is  conditional and next node of that conditioanl is another contitional --> map to next  stage


    def getNodeWithActionsForP4TEAnalysis(self, name, pipelineID):
        if(name==None):
            logger.info("Name is None in getNode. returning None")
            return None
        tbl = self.pipeline.getTblByName(name)
        conditional = self.pipeline.getConditionalByName(name)

        if(tbl != None):
            # print("Table name is "+name)
            p4teTableNode =MATNode(nodeType= P4ProgramNodeType.TABLE_NODE, name = name, oriiginalP4node = tbl )
            p4teTableNode.matchKey = tbl.getAllMatchFields()
            p4teTableNode.actions = tbl.actions
            p4teTableNode.actionObjectList = []
            for a in p4teTableNode.actions:
                actionObject = self.getActionByName(a)
                p4teTableNode.actionObjectList.append(actionObject)
                # Todo : get the list of fields modifiede here.
                # print(self.getActionByName(a).getListOfFieldsModifedAndUsed())
                statefulMemoeryBeingUsed = actionObject.getListOfStatefulMemoriesBeingUsed()
                for statefulMem in statefulMemoeryBeingUsed:
                    if(self.registerNameToTableMap.get(statefulMem) == None):
                        self.registerNameToTableMap[statefulMem] = []
                    if (not(name in self.registerNameToTableMap.get(statefulMem))):
                        self.registerNameToTableMap.get(statefulMem).append(name)

            for a in list(tbl.next_tables.values()):
                nodeList = self.getNextNodeForP4TEAnalysis(a)
                p4teTableNode.nextNodes = p4teTableNode.nextNodes + nodeList
            return p4teTableNode
        elif(conditional != None):
            # print("conditional name is "+name)
            p4teConditionalNode =MATNode(nodeType= P4ProgramNodeType.CONDITIONAL_NODE , name = name, oriiginalP4node = conditional)
            p4teConditionalNode.exprNode = ExpressionNode(p4Node = conditional.expression, name= name,  p4NodeType = P4ProgramNodeType.CONDITIONAL_NODE, pipelineID=pipelineID)
            #p4teConditionalNode.actions = self actions  # A conditional is itself an action so its actions are itself own
            # store the action used in the conditional
            p4teConditionalNode.matchKey = None
            # p4teConditionalNode.actions =
            p4teConditionalNode.next_tables = [conditional.true_next, conditional.false_next]
            for a in p4teConditionalNode.next_tables:
                nodeList = self.getNextNodeForP4TEAnalysis(a, isArrivingFromConditional=True)
                p4teConditionalNode.nextNodes = p4teConditionalNode.nextNodes + nodeList
            return p4teConditionalNode
        pass



    def getNextNodeForP4TEAnalysis(self, nodeName, isArrivingFromConditional=False):
        nextNodeList = []
        for actionEntry in self.actions:
            if actionEntry.name  == nodeName:
                nextNodeList.append(nodeName)
        for matchlessAction in self.matchlessActionNodes:
            if matchlessAction  == nodeName:
                nextNodeList.append(nodeName)

        for matchTable in self.matchActionNodes:
            if matchTable  == nodeName:
                nextNodeList.append(nodeName)
        for cond in self.conditionalNodes:
            if cond  == nodeName:
                nextNodeList.append(nodeName)
        return nextNodeList


    def getNode(self, name):
        if(name==None):
            logger.info("Name is None in getNode. returning None")
            return None
        val = self.nameToP4NodeMap.get(name)
        if (val != None): # If the node is already analyed then just retrieve it
            return val
        tbl = self.pipeline.getTblByName(name)
        conditional = self.pipeline.getConditionalByName(name)
        if(tbl != None):
            if(len(tbl.key) ==0):
                p4Node =  P4ProgramNode(p4Node = tbl, name = name, p4NodeType = P4ProgramNodeType.ACTION_NODE, pipelineID= self.pipelineID)
                p4Node.isAnalyzed = True
                self.nameToP4NodeMap[name] = p4Node
                return  p4Node
            else:
                p4Node =  P4ProgramNode(p4Node = tbl, name = name, p4NodeType = P4ProgramNodeType.TABLE_NODE, pipelineID= self.pipelineID)
                p4Node.isAnalyzed = True
                self.nameToP4NodeMap[name] = p4Node
                return  p4Node
        elif (conditional != None):
            p4Node =  P4ProgramNode(p4Node = conditional, name = name,  p4NodeType = P4ProgramNodeType.CONDITIONAL_NODE, pipelineID= self.pipelineID)
            p4Node.isAnalyzed = True
            self.nameToP4NodeMap[name] = p4Node
            return  p4Node
        else:
            return None

    def populateGraph(self, nodeName, predNode):
        '''
        Forms the graph representation of the piepline tables and conditionals
        :return:
        '''
        node = self.getNode(nodeName)
        if(node == None):
            logger.info("No relevant node is found in the pipeline for : "+ nodeName)
            return
        else:
            if(node.p4NodeType == P4ProgramNodeType.CONDITIONAL_NODE):
                exprNode = ExpressionNode(node.p4Node.expression , name= node.name,  p4NodeType = P4ProgramNodeType.CONDITIONAL_NODE, pipelineID=PipelineID.INGRESS_PIPELINE)
                exprSubgraph = exprNode.expressionToSubgraph()

                # get all field list and find their predecessor
                # refine the subgraph so that the intermediate nodes get a header field name and operation type. we will use them in later embedding.
                # At first find the depndency type with the predNode
                #
                # find all the leaf nodes
                # reverse the graph, and edge between the leaf nodes found in previsou step and the predNode
                # then call the populateGraph function with last node representing the conditional's expression as the predNode and the trueNext,
                # also the falseNext but here the predNode will remain the predNode passed as the predNode in this call

                # find the depndency of the conditional's true and false next's with the predNode
                # both truenext and false next can be conditionals
                # either one of them can be conditional and another a tbl.
                #
                # if the expression of this conditional have dependency with the pred then add edge
                #     similarly if the trur and false next have dependency woth the pred then add edge,
                # otherwise run a for loop of over all the prredecessor of the pred node. and make a recursive call to find the with whom it might have a depdency.
                # after finding the depdency, both the true next and false next will have separate node each having same conditional and respective predecessor.
                #  but the predecessor will be same (a single predeccesor for conditional, true_next and false_next)
                #
                # conditional expression to it's true and false next place 2 edge. true_next, false_next -- 2 types pf edges.
                # basically, if a table or action have depdendency with a  conditional then we can not place the conditional with the table or action in same stage.
                # so at graph building stage we ae just building the graph. in embeddin stage we will use the knowledge in the graph.
                #
                # One special thing we need to identify. assume a table and a conditional. if we want to support read-modify-condition-write (such as flowlet) then
                # we need to identify when it happens. that is the only special case we need to identify. otherwise all things are same. focus on this.
                predEdge = self.getPredNode(node, predNode)
                for e in predEdge:
                    self.p4Graph.a
                    pass
                pass
            elif(node.p4NodeType == P4ProgramNodeType.TABLE_NODE):
                pass
            elif(node.p4NodeType == P4ProgramNodeType.ACTION_NODE):
                # find dependency with pred. if there is no depepndency then go upward in the tree.
                self.getPredNode(node, predNode)
                pass


    # consider an example of chain A --> B --> C and X --> B --> C
    # now C have no depemdemcy with its predecessor B but thave dependency with A.
    # Now C have a striciter depndency with X. But B have a stricter dependnecy with A.
    # So to handle this, at first in graph we have to form all the dependencies. Then
    # a pass on the graph is neeed to find what are the dependencies of a node and keep only the strictest.

    def getPredNode(self, node, predNode):
        if (predNode == self.dummyStart):
            return [( predNode,node, DependencyType.DUMMY_DEPENDENCY_TO_START)]
        else:
            dependency = findDependencyBetweenP4Nodes(predNode, node)
            dependecyList = []
            if(dependency == None):
                # check dependency with all the predecessors of pred node. list each of the dependency
                predsOfPredNode= self.p4Graph.predecessors(predNode)
                for p in predsOfPredNode:
                    dep = findDependencyBetweenP4Nodes(p, node)
                    dependecyList.append([(p, node, dep)])
                return  dependecyList
            else:
                return [( predNode,node, dependency)]
        pass




    def populateDependencyGraphAsSimplePathGraph(self, nodeName, predNode, dependencyGraph, dummyEnd, pipelineID):
        node = self.getNodeWithActionsForP4TEAnalysis(nodeName, pipelineID)
        nextNodesLists = []
        if(node == None):
            logger.info("No relevant node is found in the pipeline for : " + nodeName)
            return
        else:
            nodeToBeAddedInGraph = self.getNode(nodeName)
            nodeToBeAddedInGraph.processedData = node
            # print("Adding node "+nodeName)
            dependencyGraph.add_nodes_from([(nodeToBeAddedInGraph, {"label" : nodeName,"color": "red"})])
            # dependencyGraph.add_node(nodeToBeAddedInGraph)
            # dependencyGraph.add_edge(predNode, nodeToBeAddedInGraph)
            dependencyGraph.add_edges_from([(predNode, nodeToBeAddedInGraph)], label="")
            if (len(node.nextNodes)<=0):
                dependencyGraph.add_edges_from([(nodeToBeAddedInGraph, dummyEnd)],label="")
                return
            else:
                for nxtNodeName in node.nextNodes:
                    self.populateDependencyGraphAsSimplePathGraph(nxtNodeName, nodeToBeAddedInGraph, dependencyGraph, dummyEnd,pipelineID)
        pass





class P4ProgramNode:

    def __init__(self, p4Node, name, p4NodeType, pipelineID):
        self.p4Node = p4Node
        self.p4NodeType = p4NodeType
        self.pipelineID = pipelineID
        self.isAssignedFlag = False
        self.isAnalyzed = False
        self.name = name
        self.stageIndex = None
        self.processedData = None
        self.addExtraBitInMatchKey = False

        pass

    def __str__(self):
        return self.name

class ExpressionNode(P4ProgramNode):

    # def __init__(self, p4Node, name, p4NodeType, pipelineID, expression):
    #     super().__init__(p4Node, name, p4NodeType, pipelineID)
    #     self.expression = expression


    def expressionToSubgraph1(self):
        # if (e == None):
        #     return
        e = self.p4Node
        typ = e.type
        left = e.value.left
        right = e.value.right
        newGraph= nx.DiGraph()
        newGraph.add_node(self.p4Node)

        newP4Node = None
        # an expression's right can never be none. only left can be none in case of "valid" check operation. Obviously which is a stupidity
        if(left ==None):
            pass
        elif(type(left) == PrimitiveOpblock):
            #means this is direct operation. no need to do expansion
            newP4Node = P4ProgramNode(p4Node = left, p4NodeType= P4ProgramNodeType.PRIMITIVE_OP_NODE, pipelineID=self.pipelineID)
            newGraph.add_node(newP4Node)
            newGraph.add_edge(self.p4Node, newP4Node)
        elif(type(left) == Expression):
            #means need expansion
            if(left.value.left ==None) and (type(left.value.right) == PrimitiveField):
                logger.info("Found null in left and Value type filed in left  for left of expression")
                newP4Node = P4ProgramNode(p4Node = left, p4NodeType= P4ProgramNodeType.PRIMITIVE_OP_NODE, pipelineID=self.pipelineID)
                newGraph.add_node(newP4Node)
                newGraph.add_edge(self.p4Node, newP4Node)
            elif(type(left.value.left) != Expression) and (type(left.value.right) != Expression):
                logger.info("Found Value type filed in both left and right  for left of expression")
                newP4Node = P4ProgramNode(p4Node = left, p4NodeType= P4ProgramNodeType.PRIMITIVE_OP_NODE, pipelineID=self.pipelineID)
                newGraph.add_node(newP4Node)
                newGraph.add_edge(self.p4Node, newP4Node)
            else:
                eNode = ExpressionNode(p4Node = left, p4NodeType = P4ProgramNodeType.EXPRESSION_NODE, pipelineID=self.pipelineID)
                newRoot, subGraph = eNode.expressionToSubgraph()
                # newEdge = (self.p4Node, newRoot)
                # newGraph.update(newEdge, subGraph)
                newGraph1= nx.DiGraph()
                newGraph1.add_edges_from(newGraph.edges())
                newGraph1.add_edges_from(subGraph.edges())
                newGraph1.add_nodes_from(newGraph.nodes())
                newGraph1.add_nodes_from(subGraph.nodes())
                newGraph1.add_edge(self.p4Node, newRoot)
                newGraph = newGraph1
        # if(tempGraph.number_of_nodes() >0):
        #     newEdge = (self.p4Node, newP4Node)
        #     newGraph.update(newEdge, tempGraph)

        newP4Node = None
        if(right==None):
            pass
        elif(type(right) == PrimitiveOpblock):
            newP4Node = P4ProgramNode(p4Node = right, p4NodeType= P4ProgramNodeType.PRIMITIVE_OP_NODE, pipelineID=self.pipelineID)
            newGraph.add_node(newP4Node)
            newGraph.add_edge(self.p4Node, newP4Node)
        elif(type(right) == Expression):
            #means this is direct operation . no need to do expansion
            if(right.value.left ==None) and (type(right.value.right) == PrimitiveField):
                logger.info("Found null in left and Value type filed in right  for right of expression")
                newP4Node = P4ProgramNode(p4Node = right, p4NodeType= P4ProgramNodeType.PRIMITIVE_OP_NODE, pipelineID=self.pipelineID)
                newGraph.add_node(newP4Node)
                newGraph.add_edge(self.p4Node, newP4Node)
            elif(type(right.value.left) != Expression) and (type(right.value.right) != Expression):
                logger.info("Found Value type filed in both left and right  for right of expression")
                newP4Node = P4ProgramNode(p4Node = right, p4NodeType= P4ProgramNodeType.PRIMITIVE_OP_NODE, pipelineID=self.pipelineID)
                newGraph.add_node(newP4Node)
                newGraph.add_edge(self.p4Node, newP4Node)
            else:
                eNode = ExpressionNode(p4Node = right, p4NodeType = P4ProgramNodeType.EXPRESSION_NODE, pipelineID=self.pipelineID)
                newRoot, subGraph = eNode.expressionToSubgraph()
                # newEdge = (self.p4Node, newRoot)
                # newGraph.update(newEdge, subGraph)
                newGraph1= nx.DiGraph()
                newGraph1.add_edges_from(newGraph.edges())
                newGraph1.add_edges_from(subGraph.edges())
                newGraph1.add_nodes_from(newGraph.nodes())
                newGraph1.add_nodes_from(subGraph.nodes())
                newGraph1.add_edge(self.p4Node, newRoot)
                newGraph = newGraph1
        # if(tempGraph.number_of_nodes() >0):
        #     newEdge = (self.p4Node, newP4Node)
        #     newGraph.update(newEdge, tempGraph)
        return self.p4Node, newGraph

    def expressionToSubgraph(self):
        # if (e == None):
        #     return
        e = self.p4Node
        op = e.type
        left = e.value.left
        right = e.value.right
        newGraph= nx.DiGraph()
        newGraph.add_node(self.p4Node)

        if((left==None) and (right==None)):
            return None
        elif(type(self.p4Node) == PrimitiveOpblock):
            return self.p4Node, newGraph
        # header_Stack and stack_field are not supported  in parsing. If they are supported in parsing we can handle them here also


        # print("left type is "+str(type(left)))
        # print("right type is "+str(type(right)))
        if((left==None) or (type(left) == HexStr) or (type(left) == PrimitiveField) or (type(left) == PrimitiveHeader) or (type(left) == BoolPrimitive) or \
                    (type(left) == RegisterArrayPrimitive) )  \
                and ((right==None) or (type(right) == HexStr) or (type(right) == PrimitiveField) or (type(right) == PrimitiveHeader) or (type(right) == BoolPrimitive) or \
                    (type(right) == RegisterArrayPrimitive)   ):
            #make a single node and add to the graph
            primOpNode = PrimitiveOpblock(primitiveOP = op, left = left, right=right)
            newP4Node = P4ProgramNode(p4Node = primOpNode, name = self.name+"left"+"right", p4NodeType= P4ProgramNodeType.PRIMITIVE_OP_NODE, pipelineID=self.pipelineID)
            newGraph.add_node(newP4Node)
            newGraph.add_edge(self.p4Node, newP4Node)
        if (type(left) == PrimitiveOpblock):
            newP4Node = P4ProgramNode(p4Node = left, name = self.name+"left"+"_primitive_op_block",  p4NodeType= P4ProgramNodeType.PRIMITIVE_OP_NODE, pipelineID=self.pipelineID)
            newGraph.add_node(newP4Node)
            newGraph.add_edge(self.p4Node, newP4Node)
        if (type(right) == PrimitiveOpblock):
            newP4Node = P4ProgramNode(p4Node = right, name = self.name+"right_primitive_op_block", p4NodeType= P4ProgramNodeType.PRIMITIVE_OP_NODE, pipelineID=self.pipelineID)
            newGraph.add_node(newP4Node)
            newGraph.add_edge(self.p4Node, newP4Node)
        if (type(left) == Expression):
            eNode = ExpressionNode(p4Node = left, name = self.name+"left_expression",  p4NodeType = P4ProgramNodeType.EXPRESSION_NODE, pipelineID=self.pipelineID)
            newRoot, subGraph = eNode.expressionToSubgraph()
            newGraph1= nx.DiGraph()
            newGraph1.add_edges_from(newGraph.edges())
            newGraph1.add_edges_from(subGraph.edges())
            newGraph1.add_nodes_from(newGraph.nodes())
            newGraph1.add_nodes_from(subGraph.nodes())
            newGraph1.add_edge(self.p4Node, newRoot)
            newGraph = newGraph1
        if (type(right) == Expression):
            eNode = ExpressionNode(p4Node = right, name = self.name+"right_expression", p4NodeType = P4ProgramNodeType.EXPRESSION_NODE, pipelineID=self.pipelineID)
            newRoot, subGraph = eNode.expressionToSubgraph()
            newGraph1= nx.DiGraph()
            newGraph1.add_edges_from(newGraph.edges())
            newGraph1.add_edges_from(subGraph.edges())
            newGraph1.add_nodes_from(newGraph.nodes())
            newGraph1.add_nodes_from(subGraph.nodes())
            newGraph1.add_edge(self.p4Node, newRoot)
            newGraph = newGraph1
        return self.p4Node, newGraph


    def getAllFieldList(self):
        root, exprGraph = self.expressionToSubgraph()
        nodesWithfiledList = [x for x in exprGraph.nodes() if exprGraph.out_degree(x)==0 and exprGraph.in_degree(x)==1]
        fieldList = []
        for n in nodesWithfiledList:
            lvalue = n.p4Node.left
            if((lvalue != None ) and (type(lvalue)== PrimitiveField)):
                fieldName = lvalue.header_name + "."+ lvalue.field_memeber_name
                fieldList.append(fieldName)
            elif((lvalue != None ) and (type(lvalue)== PrimitiveField)):
                logger.info("A node in expession found which is not PrimitiveField. Check It!!!")
            rvalue = n.p4Node.right
            if((rvalue != None ) and (type(rvalue)== PrimitiveField)):
                fieldName = rvalue.header_name + "."+ rvalue.field_memeber_name
                fieldList.append(fieldName)
            elif((rvalue != None ) and (type(rvalue)== PrimitiveField)):
                logger.info("A node in expession found which is not PrimitiveField. Check It!!!")

        return fieldList

    def getOnlyModifiedFieldList(self):
        '''
        Nope this function do not return the list of fields modified in the expression. To do that we need primitive operation wise analysis.
        But in expression used in conditionals we do not need to support fields that are modified. We only support fields that are checked against some value
        If someone wants to support field modification in expression then they have to add this support to the hardware and
        also implement the operator (architecture specific) nwise analysis
        :return:
        '''
        root, exprGraph = self.expressionToSubgraph()
        nodesWithfiledList = [x for x in exprGraph.nodes() if exprGraph.out_degree(x)==0 and exprGraph.in_degree(x)==1]
        fieldList = []
        for n in nodesWithfiledList:
            lvalue = n.p4Node.value.left
            if((lvalue != None ) and (type(lvalue)== PrimitiveField)):
                fieldName = lvalue.header_name + "."+ lvalue.field_memeber_name
                fieldList.append(fieldName)
            elif((lvalue != None ) and (type(lvalue)== PrimitiveField)):
                logger.info("A node in expession found which is not PrimitiveField. Check It!!!")
        return fieldList




# def makeFunction(root):
#     #make a function that will merge independenc childs into one. the process will start form leafr
#
#     if (root's sucessor is null that means it is leaf node):
#         get a list of  root's predecessor's nodes.
#         among them take only those nodes who are leaf.
#         merge them. remove all the edges. build only one edge from predecessor to the new node



#--------------------------------------------- All Static functions are here

def findDependencyBetweenP4Nodes(node1, node2):
    '''
    This functions finds dependency type between 2 nodes. Bothe the nodes have to be of type P4ProgramNode
    :param node1:
    :param node2:
    :return:
    '''

    node1 = P4ProgramNode()
    node2 = P4ProgramNode()
    if(node1.p4NodeType == P4ProgramNodeType.TABLE_NODE) and (node2.p4NodeType == P4ProgramNodeType.TABLE_NODE):
        return tbl2tblDependnecyanlysis(node1, node2)
    if(node1.p4NodeType == P4ProgramNodeType.TABLE_NODE) and (node2.p4NodeType == P4ProgramNodeType.ACTION_NODE):
        return tbl2tblDependnecyanlysis(node1, node2)
    if(node1.p4NodeType == P4ProgramNodeType.TABLE_NODE) and (node2.p4NodeType == P4ProgramNodeType.CONDITIONAL_NODE):
        # if table's hit or miss is a conditional
        pass
    if(node1.p4NodeType == P4ProgramNodeType.ACTION_NODE) and (node2.p4NodeType == P4ProgramNodeType.TABLE_NODE):
        return tbl2tblDependnecyanlysis(node1, node2)
    if(node1.p4NodeType == P4ProgramNodeType.ACTION_NODE) and (node2.p4NodeType == P4ProgramNodeType.ACTION_NODE):
        return tbl2tblDependnecyanlysis(node1, node2)
    if(node1.p4NodeType == P4ProgramNodeType.ACTION_NODE) and (node2.p4NodeType == P4ProgramNodeType.CONDITIONAL_NODE):
        pass
# The conncern is how to find successro dependency-- how to determine if tables1's execution result determines whther to execute table 2 or not
    #look at node_26. for example. but the example is written in such a way it creates match dependency. but it is actually can be written as successoe dependency.
    #but we have to test a program with successor dependency

    #if a hit statement follows a table node then it is a accessor dependency
    if(node1.p4NodeType == P4ProgramNodeType.CONDITIONAL_NODE) and (node2.p4NodeType == P4ProgramNodeType.TABLE_NODE):
        # both are table now find their respective dependencies
        pass
    if(node1.p4NodeType == P4ProgramNodeType.CONDITIONAL_NODE) and (node2.p4NodeType == P4ProgramNodeType.ACTION_NODE):
        pass
    if(node1.p4NodeType == P4ProgramNodeType.CONDITIONAL_NODE) and (node2.p4NodeType == P4ProgramNodeType.CONDITIONAL_NODE):
        pass
    return  None

def tbl2tblDependnecyanlysis(tblNode1, tblNode2):
    # This function will work for both action nodes (which is actually represented by table node in the json prepresentation) and
    # table nodes (real range, exact, lpm, ternary matches)
    #For 2 action nodes it will only basically use the 2nd if statement; because in action only nodes there will be no matching keys. so only actions are checked
    tbl1MatchKeyList = tblNode1.getAllMatchFields()
    tbl2MatchKeyList = tblNode2.getAllMatchFields()
    filedsModifiedByTbl1Actions = tblNode1.getListOfFieldsModifedAndUsed()
    filedsModifiedByTbl2Actions = tblNode2.getListOfFieldsModifedAndUsed()
    #todo: this is not totally correct. need to take the action of one table. we are not taking that here

    if (common_member(filedsModifiedByTbl1Actions, tbl2MatchKeyList)):
        return DependencyType.MATCH_DEPENDENCY # highest priority
    if (common_member(filedsModifiedByTbl1Actions, filedsModifiedByTbl2Actions)):
        return DependencyType.ACTION_DEPENDENCY
    if (common_member(tbl1MatchKeyList, filedsModifiedByTbl2Actions)):
        return DependencyType.REVERSE_MATCH_DEPENDENCY
    if(tblNode1.next_tables.get("__HIT__") != None) and (tblNode1.next_tables.get("__HIT__") == tblNode2.name) :
        return DependencyType.SUCCESOR_DEPENDENCY
    if(tblNode1.next_tables.get("__MISS__") != None) and (tblNode1.next_tables.get("__MISS__") == tblNode2.name) :
        return DependencyType.SUCCESOR_DEPENDENCY

    return None

#the trouble is created by the nested expressions in the form of header.field1 = header.field2 + header.field3+ x; header.field4 = header.field1+ 3
#
# action2action -- between 2 actions there can be a dependency because of multi level nesting. action 1 ---  a = b+ c, d = a+e; action 2 ---  p = d + p, d = a+m. so according to the order the
# execution have to happen. otherwise trouble will happen
# action2table
# table2Action
#
# -- the function tbl2tblDependnecyanlysis can handle all the depndency for table and actions.
#
# conditional2table
# conditional2action -- for conditional consider the conditional expression as the match part. and the action of the conditional as the normal action. then
#     follow the same dependency types as table and action discussed in previous.
# write a function to list all the fields used in an expression.
# action2conditional
# action2table
#
# For conditionals --> the list of fields used in the expression is equivalent to the match keys of a table. find it.

def common_member(a, b):
    a_set = set(a)
    b_set = set(b)
    if len(a_set.intersection(b_set)) > 0:
        return(True)
    return(False)



class P4ProgramGraph:
    def __init__(self, p4ProgramParserJsonObject):
        '''
        This program loads the parsed Json object representation of a P4 program into a graph
        :param p4ProgramParserJsonObject: this is the object that is generated by parsing the P4 json for bmv2.
        '''
        self.pipelineIdToPipelineGraphMap = {}
        self.pipelineIdToPipelineMap = {}
        self.parsedP4Program = p4ProgramParserJsonObject
        self.actions = p4ProgramParserJsonObject.actions

    def getActionByName(self, actName):
        for act in self.actions:
            if(act.name == actName):
                return act
        return None

    def getTotalHeaderLength(self):
        total = 0
        for k in self.nameToHeaderTypeObjectMap.keys():
           total = total + int(self.nameToHeaderTypeObjectMap.get(k).bitWidth)
        print("Total header legnth is ",total)

    def getTotalHeaderLengthForHeaderFieldList(self, headerFieldList):
        total = 0
        for k in headerFieldList:
            hf = self.nameToHeaderTypeObjectMap.get(k)
            if (hf==None):
                flag = False
                for headerStruct in self.parsedP4Program.headers:
                    if(headerStruct.name == k):
                        flag = True
                        break
                    else:
                        flag = False
                if (flag == False):
                    logger.info("Field not found in map . The field is "+str(k))
            else:
                total = total + int(self.nameToHeaderTypeObjectMap.get(k).bitWidth)
        print("Total header legnth for given headerfield list is ",total)
        return total

    def getHeaderCountByBitWidthForHeaderFieldList(self, headerFieldList):
        total = 0
        bitWidthByHeadercount = {}
        for k in headerFieldList:
            hf = self.nameToHeaderTypeObjectMap.get(k)
            if (hf==None):
                logger.info("Field not found in map . The field is "+str(k))
            else:
                if(bitWidthByHeadercount.get(self.nameToHeaderTypeObjectMap.get(k).bitWidth) == None):
                    bitWidthByHeadercount[self.nameToHeaderTypeObjectMap.get(k).bitWidth] = 1
                else:
                    bitWidthByHeadercount[self.nameToHeaderTypeObjectMap.get(k).bitWidth] = bitWidthByHeadercount[self.nameToHeaderTypeObjectMap.get(k).bitWidth] + 1
        return bitWidthByHeadercount

    def getDeepCopyOfHeaderVector(self):
        return deepcopy(self.nameToHeaderTypeObjectMap)

    def buildHeaderVector(self):
        self.nameToHeaderTypeObjectMap = {}
        for h in self.parsedP4Program.headers:
            headerTypeName = h.header_type
            # headertypeNameUsedInSource =
            if (headerTypeName == None):
                logger.error("Heeader Type Name for the header "+ h.get("name")+" is not found. Exiting")
                exit(1)
            headerType = self.parsedP4Program.getHeaderTypeFromName(headerTypeName)
            if (headerType == None):
                logger.error("Heeader Type for the header "+ h.get("name")+" is not found. Exiting")
                exit(1)
            for htf in headerType.fields:
                #hdr.packet_in.egress_rate_event_data = local_metadata.egress_rate_event_hdr.egress_rate_event_data
                # if(headerTypeName == "packet_in_t") and (htf[0]=="egress_rate_event_data"):
                #     bitWidth = math.ceil(float(19))*8
                # elif(headerTypeName == "packet_in_t") and (htf[0]=="egress_queue_event_data"):
                #     bitWidth = math.ceil(float(19))*8
                # elif(headerTypeName == "local_metadata_t") and (htf[0]=="egress_queue_event_hdr.egress_queue_event_data"):
                #     bitWidth = math.ceil(float(19))*8
                # elif(headerTypeName == "local_metadata_t") and (htf[0]=="local_metadata.egress_rate_event_hdr.egress_rate_event_data"):
                #     bitWidth = math.ceil(float(19))*8
                # else:
                bitWidth = math.ceil(float(htf[1]/8))*8
                hdrObj = HeaderField(name=h.name+"."+htf[0], bitWidth= bitWidth, isSigned= htf[2])
                # hdrObj = HeaderField(name=h.name+"."+htf[0], bitWidth= htf[1], isSigned= htf[2])
                self.nameToHeaderTypeObjectMap[hdrObj.name] = hdrObj
                pass
        return self.nameToHeaderTypeObjectMap

    def headeranalyzer(self):
        print(self.nameToHeaderTypeObjectMap)
        self.getTotalHeaderLength()
        print("\n\n Ingress stage header analysis")
        fullListOfHeaderFieldsUsedInThePipeline =self.headeranalyzerForSinglePipeline(PipelineID.INGRESS_PIPELINE)
        self.getTotalHeaderLengthForHeaderFieldList(fullListOfHeaderFieldsUsedInThePipeline)
        bitWidthByHeadercount = self.getHeaderCountByBitWidthForHeaderFieldList(fullListOfHeaderFieldsUsedInThePipeline)
        print("Bitwdith wise header count is ",bitWidthByHeadercount)
        print("\n\n Egress stage header analysis")
        fullListOfHeaderFieldsUsedInThePipeline = self.headeranalyzerForSinglePipeline(PipelineID.EGRESS_PIPELINE)
        self.getTotalHeaderLengthForHeaderFieldList(fullListOfHeaderFieldsUsedInThePipeline)
        bitWidthByHeadercount = self.getHeaderCountByBitWidthForHeaderFieldList(fullListOfHeaderFieldsUsedInThePipeline)
        print("Bitwdith wise header count is ",bitWidthByHeadercount)

        # print("\n\n\n\n analyzing match tables for ingress stage")
        # self.matMatchingAnalyzer(PipelineID.INGRESS_PIPELINE)
        # print("\n\n\n\n analyzing match tables for egress stage")
        # self.matMatchingAnalyzer(PipelineID.EGRESS_PIPELINE)



    def matMatchingAnalyzer(self,piepelineId):
        pipelineGraphObject = self.pipelineIdToPipelineGraphMap.get(piepelineId)
        i=0
        for tbl in pipelineGraphObject.pipeline.tables:
            allHeaderFieldUsedInOneMAT = tbl.getAllMatchFields()
            allHeaderFieldUsedInActionsOfOneMAT = pipelineGraphObject.getAllFieldsModifedInActionsOfTheTable(tbl.name)
            if len(allHeaderFieldUsedInOneMAT)>0:
                # print("Stage---- "+str(i)+"  Table : "+tbl.name+ " requires "+str(len(allHeaderFieldUsedInOneMAT))+" fields to match. Width of these match fields are ")
                self.getHeaderCountByBitWidthForHeaderFieldList(allHeaderFieldUsedInOneMAT)
            if len(allHeaderFieldUsedInActionsOfOneMAT)>0:
                # print("Stage---- "+str(i)+"  Table : "+tbl.name+ " requires "+str(len(allHeaderFieldUsedInActionsOfOneMAT))+" fields and action for each of them. Width of these action fields are ")
                self.getHeaderCountByBitWidthForHeaderFieldList(allHeaderFieldUsedInActionsOfOneMAT)
            print("\n")
            i= i+1



    def headeranalyzerForSinglePipeline(self, piepelineId):
        '''
        This function analyze which headers are used in a pipeline. and find what is their total length so that we can split the header fields in 2 different sets
        :param piepelineId:
        :return:
        '''
        #At first analyzig the match action table of the  pipeline
        pipelineGraphObject = self.pipelineIdToPipelineGraphMap.get(piepelineId)
        allHeaderFieldUsedInMatchPartAllMAT = []
        allHeaderFieldUsedInActionsOfAllMAT = []
        for tbl in pipelineGraphObject.pipeline.tables:
            allHeaderFieldUsedInOneMAT = tbl.getAllMatchFields()
            allHeaderFieldUsedInActionsOfOneMAT = pipelineGraphObject.getAllFieldsModifedInActionsOfTheTable(tbl.name)
            if len(allHeaderFieldUsedInOneMAT)>0:
                for e in allHeaderFieldUsedInOneMAT:
                    allHeaderFieldUsedInMatchPartAllMAT.append(e)
            if len(allHeaderFieldUsedInActionsOfOneMAT)>0:
                for e in allHeaderFieldUsedInActionsOfOneMAT:
                    allHeaderFieldUsedInActionsOfAllMAT.append(e)

        print("Before removing duplicate member of match fields "+str(len(allHeaderFieldUsedInMatchPartAllMAT)))
        allHeaderFieldUsedInMatchPartAllMAT = set(allHeaderFieldUsedInMatchPartAllMAT) # removing duplicate through set operations. Becuase multiple MAT can use same header fileds.
        print("After removing duplicate member  of match fields "+str(len(allHeaderFieldUsedInMatchPartAllMAT)))
        print(allHeaderFieldUsedInMatchPartAllMAT)
        print("Before removing duplicate member of action fields "+str(len(allHeaderFieldUsedInActionsOfAllMAT)))
        allHeaderFieldUsedInActionsOfAllMAT = set(allHeaderFieldUsedInActionsOfAllMAT) # removing duplicate through set operations. Becuase multiple MAT can use same header fileds in their actions.
        print("After removing duplicate member  of match fields "+str(len(allHeaderFieldUsedInActionsOfAllMAT)))
        fullListOfHeaderFieldsUsedInThePipeline= allHeaderFieldUsedInMatchPartAllMAT.union(allHeaderFieldUsedInActionsOfAllMAT)
        print("Total number of header fields used in the pipeline is "+str(len(fullListOfHeaderFieldsUsedInThePipeline)))

        #Now analyzig the conditionals of the pipeline
        allHeaderFieldUsedInConditionCheckingPartOfAllConditionals = []
        for conditionalObj in pipelineGraphObject.pipeline.conditionals:
            exprNode = ExpressionNode(p4Node = conditionalObj.expression, name =conditionalObj.name,  p4NodeType = P4ProgramNodeType.CONDITIONAL_NODE, pipelineID=piepelineId)
            allHeaderFieldUsedInConditionCheckingPartOfOneConditionals = exprNode.getAllFieldList()
            if len(allHeaderFieldUsedInConditionCheckingPartOfOneConditionals)>0:
                for e in allHeaderFieldUsedInConditionCheckingPartOfOneConditionals:
                    allHeaderFieldUsedInConditionCheckingPartOfAllConditionals.append(e)
        print("Before removing duplicate member of conditional checking of all the conditional  "+str(len(allHeaderFieldUsedInConditionCheckingPartOfAllConditionals)))
        allHeaderFieldUsedInConditionCheckingPartOfAllConditionals = set(allHeaderFieldUsedInConditionCheckingPartOfAllConditionals) # removing duplicate through set operations. Becuase multiple MAT can use same header fileds.
        print("After removing duplicate member of conditional checking of all the conditional  "+str(len(allHeaderFieldUsedInConditionCheckingPartOfAllConditionals)))
        #Condtioanls have either true or false. they do not have own action. their true_next or false_next is an action. These acrions are analyzed with match-action tables.
        #So need to proces them again
        fullListOfHeaderFieldsUsedInThePipeline = allHeaderFieldUsedInConditionCheckingPartOfAllConditionals.union(fullListOfHeaderFieldsUsedInThePipeline)
        print("Total number of header fields used in the pipeline is "+str(len(fullListOfHeaderFieldsUsedInThePipeline)))
        return fullListOfHeaderFieldsUsedInThePipeline

    def preProcessAllActions(self):
        self.actionNameToSubGraphMap= {}
        for a in self.parsedP4Program.actions:
            # if primitive op is add header then skip it . bcz for p4 16 we do not need it.
            for p in a.primitives:
                if(type(p.op) == PrimitiveOp.ADD_HEADER):  # Because this is used to tackle P4_14 programs. Not necessary actually add header
                    pass


    def dfsVisit(self, graph, current, stageIndex,stageWiseMatMap,registerNameToStageMap, registerNameToUserMatMap,isPredecessorConditional=False):
        if(stageWiseMatMap.get(stageIndex) == None):
            stageWiseMatMap[stageIndex] = [] # this part is common for all. because we need list for each stage
        if (current.stageIndex == None):
            current.stageIndex = stageIndex
            stageWiseMatMap[stageIndex].append(current)
            # if it's action access a memory store that info in a map
        else:
            if current.stageIndex >= stageIndex:
                pass # This node is already visited and it is assigned to mapped on a later stage
            else:
                currentStageIndex = current.stageIndex
                updatedStageIndex = stageIndex
                currentStageMATMapList = stageWiseMatMap[currentStageIndex]
                for mat in currentStageMATMapList:
                    if mat == current:
                        currentStageMATMapList.remove(current)
                if(stageWiseMatMap.get(updatedStageIndex) == None):
                        stageWiseMatMap[updatedStageIndex] = []
                stageWiseMatMap.get(updatedStageIndex).append(current)
                current.stageIndex = updatedStageIndex
                if ((current.processedData != None) and (current.processedData.nodeType == P4ProgramNodeType.TABLE_NODE)): #only table nodes can access the statefulmemory in their action
                    for a in current.processedData.actions:
                        actn = self.getActionByName(a)
                        statefulMemoryName = actn.getStatefulMemoryNameFromAction()
                        if(statefulMemoryName != None):
                            registerNameToStageMap[statefulMemoryName] = current.stageIndex
        if ((current.processedData != None) and (isPredecessorConditional==True)):
            current.addExtraBitInMatchKey = True

            # --- totally indepndent if check.. if the action access a stateful memory, then find the stage where the memory based table was mappped.
            # now if that index is less than currentstageindex  than update it's stage index. or if the current node's stagei ndex is less than that old node's index
            # then update current node's index into that old one.
        #if ((current.processedData != None) and (current.processedData.nodeType != P4ProgramNodeType.CONDITIONAL_NODE)): #only table nodes can access the statefulmemory in their action
        if ((current.processedData != None) and (current.processedData.actions != None)): #only table nodes can access the statefulmemory in their action
            # print("My action is "+str(current.processedData.actions))
            # iterate over all the actions. and find whichver is max we will assign the mat to that stage
            for a in current.processedData.actions:
                actn = self.getActionByName(a)
                statefulMemoryName = actn.getStatefulMemoryNameFromAction()
                # print("StatefulmemoryName is "+str(statefulMemoryName))
                # we need to repeat the follwing multiple times because ther may be multiple stateful memory used in one action. But at this moment for P4TE focusing onle on one is enough
                if(statefulMemoryName != None):
                    stageForTheStateFulMemory =  registerNameToStageMap.get(statefulMemoryName)
                    if(stageForTheStateFulMemory == None):
                        registerNameToStageMap[statefulMemoryName] =current.stageIndex
                    else:
                        if(stageForTheStateFulMemory > current.stageIndex):
                            # userMatList = registerNameToUserMatMap.get(statefulMemoryName)
                            # for mat in userMatList:
                            #     oldStageIndex = [x for x in graph.nodes if x.name==mat][0].stageIndex
                            #     if(oldStageIndex != None): #Becuase the mat may be a node that is not mapped yet
                            #         updatedStageIndex = stageForTheStateFulMemory
                            #         oldStageMATMapList = stageWiseMatMap.get(oldStageIndex)
                            #         for oldMat in oldStageMATMapList:
                            #             if oldMat.name == mat:
                            #                 oldStageMATMapList.remove(oldMat)
                            #         if(stageWiseMatMap.get(updatedStageIndex) == None):
                            #             stageWiseMatMap[updatedStageIndex] = []
                            #         stageWiseMatMap.get(updatedStageIndex).append(oldMat)
                            #         oldMat.stageIndex = updatedStageIndex
                            # stageWiseMatMap.get(stageForTheStateFulMemory).append(current)
                            # current.stageIndex = updatedStageIndex
                            # registerNameToStageMap[statefulMemoryName] = stageForTheStateFulMemory


                            currentStageIndex = current.stageIndex
                            updatedStageIndex = stageForTheStateFulMemory
                            currentStageMATMapList = stageWiseMatMap.get(currentStageIndex)
                            for mat in currentStageMATMapList:
                                if mat == current:
                                    currentStageMATMapList.remove(current)
                            if(stageWiseMatMap.get(updatedStageIndex) == None):
                                stageWiseMatMap[updatedStageIndex] = []
                            stageWiseMatMap.get(updatedStageIndex).append(current)
                            current.stageIndex = updatedStageIndex
                            registerNameToStageMap[statefulMemoryName] = updatedStageIndex

                        elif(stageForTheStateFulMemory < current.stageIndex):
                            # remove all the mat's that uses this stateful memory from their current stage. and insert into current.stageIndex'th stage
                            userMatList = registerNameToUserMatMap.get(statefulMemoryName)
                            for mat in userMatList:
                                oldStageIndex = [x for x in graph.nodes if x.name==mat][0].stageIndex
                                if(oldStageIndex != None): #Becuase the mat may be a node that is not mapped yet
                                    updatedStageIndex = current.stageIndex
                                    oldStageMATMapList = stageWiseMatMap.get(oldStageIndex)
                                    for oldMat in oldStageMATMapList:
                                        if oldMat.name == mat:
                                            oldStageMATMapList.remove(oldMat)
                                            break
                                    if(stageWiseMatMap.get(updatedStageIndex) == None):
                                        stageWiseMatMap[updatedStageIndex] = []
                                    stageWiseMatMap.get(updatedStageIndex).append(oldMat)
                                    oldMat.stageIndex = updatedStageIndex
                            # stageWiseMatMap.get(current.stageIndex).append(current)
                            registerNameToStageMap[statefulMemoryName] = current.stageIndex


        for s in graph.successors(current):
            if ((current.processedData != None) and (current.processedData.nodeType == P4ProgramNodeType.CONDITIONAL_NODE)):
                self.dfsVisit( graph, current=s, stageIndex=stageIndex+1,stageWiseMatMap=stageWiseMatMap, registerNameToStageMap=registerNameToStageMap, registerNameToUserMatMap = registerNameToUserMatMap,isPredecessorConditional=True)
            else:
                self.dfsVisit( graph, current=s, stageIndex=stageIndex+1,stageWiseMatMap=stageWiseMatMap, registerNameToStageMap=registerNameToStageMap, registerNameToUserMatMap = registerNameToUserMatMap,isPredecessorConditional=False)

        pass

    def stageWiseMATEorSinglePipelineForP4TE(self, piepelineId):
        pipelineGraphObject = self.pipelineIdToPipelineGraphMap.get(piepelineId).p4Graph
        print(pipelineGraphObject)
        startNode = self.pipelineIdToPipelineGraphMap.get(piepelineId).dummyStart
        stageWiseMatMap = {}
        registerNameToStageMap = {}
        self.dfsVisit( graph = pipelineGraphObject, current = startNode, stageIndex =-1,stageWiseMatMap= stageWiseMatMap, registerNameToStageMap= registerNameToStageMap, registerNameToUserMatMap = self.pipelineIdToPipelineGraphMap.get(piepelineId).registerNameToTableMap)
        # print("The stageWiseMatMap for the  pipeline"+ (str(piepelineId))+" is following")
        perStageHwRequirementsForThePipeline = self.calculateStageWiseHWRequirements(stageWiseMatMap, piepelineId)
        return stageWiseMatMap,perStageHwRequirementsForThePipeline,registerNameToStageMap

    def getHeaderBitCount(self, headerName):

        # if("local_metadata" in headerName):
        # print("header name is"+headerName)
        if headerName.endswith("$valid$"):
            return 8 # assuming the minimum number of bits. But need to recheck with hardware configurations
        else:
            hdrObj = self.nameToHeaderTypeObjectMap.get(headerName)
            if hdrObj == None:
                for hf in self.parsedP4Program.headers:
                    if(hf.name == headerName):
                        return 8  # This means the primitie was set valid/invalid or chekcing a headers validity. Therefore the whole header was used. So return onlyn 8
                for regArray in self.parsedP4Program.register_arrays:
                    if(regArray.name == headerName):
                        # return regArray.bitwidth
                        return math.ceil(float(regArray.bitwidth/8))*8
            else:
                if("temp_src_addr" in headerName): # skiipping this header field because, this fileds are used for swapping two ipv6 addresses. now for swapping in RMT we do not need tmp in real hardware
                    return  0
                else:
                    bitWidth = math.ceil(float(hdrObj.bitWidth/8))*8
                    return bitWidth
        # print("header not found "+headerName)
        return None
    def calculateStageWiseHWRequirements(self, stageWiseMatMap, piepelineId):
        # if matnode then just print the feild used and modified
        # else if conditional simply print the list of fields used in expression (heave to use expression node. also we have to make the requirments two times to facilliate if-else)
        print("Stagewise table and action mapping for "+str(piepelineId)+" is follwoing : ")
        perStageHwRequirementsForThePipeline = {}
        for k in stageWiseMatMap.keys():
            print("===============================================================================================================================")
            print("Stage:------------------"+str(k+1))
            if(k==-1):
                print("This is a dummy stage to handle a dummy node in the TDG. Not really mapped to the hardware. So please skip it. ")
            stageMatList = stageWiseMatMap.get(k)
            totalnumberofFieldsBeingModified = 0
            headerBitWidthOfFieldsBeingModified = 0
            totalNumberOfFieldsUsedAsParameter = 0
            totalBitWidthOfFieldsUsedAsParameter = 0

            maxBitWidthOfAction =0
            matKeyBitWidth = 0
            matKeyLength = 0
            for m in stageMatList:
                listOfFieldBeingModifedInThisStage = []
                listOfFieldBeingUsedAsParameterInThisStage = []

                if(m.processedData != None):
                    totalBitWidthOfTheAction=0
                    if m.processedData.nodeType == P4ProgramNodeType.TABLE_NODE:
                        p4teTableNode = m.processedData
                        print("MAT node: "+p4teTableNode.name)
                        print("Match Keys are: ")
                        actionIndex = 1
                        for f in p4teTableNode.matchKey:
                            matKeyBitWidth =  matKeyBitWidth + self.getHeaderBitCount(f)
                            print("\t\t *) "+str(f))
                        matKeyLength = matKeyLength + len(p4teTableNode.matchKey)
                        if(m.addExtraBitInMatchKey):
                            matKeyLength = matKeyLength + 1
                            matKeyBitWidth = matKeyBitWidth+ 8
                            m.addExtraBitInMatchKey = False # Only one time adding a field for conditioanl of previsou stage  enough. Because, the TDG is basically uniqie path from top to bottom. so
                            #if there is a consitioanl in previous stage. only one bit is enogh in this stage
                            print("\t\t *) "+"8 bit key for handling conditional of previous stage")
                        print("Actions are: ")
                        for a in p4teTableNode.actions:
                            listOfFieldBeingModifed, listOfFieldBeingUsed = self.getActionByName(a).getListOfFieldsModifedAndUsed()
                            listOfFieldBeingModifedInThisStage= listOfFieldBeingModifedInThisStage + listOfFieldBeingModifed
                            listOfFieldBeingUsedAsParameterInThisStage = listOfFieldBeingUsedAsParameterInThisStage + listOfFieldBeingUsed
                            act = self.getActionByName(a)
                            print("\t "+str(actionIndex)+" Action Nanme: "+act.name)
                            print("\t Primitives used in action are: ")
                            for prim in act.primitives:
                                print("\t\t *) "+str(prim.source_info))
                            for f in listOfFieldBeingModifed:
                                totalnumberofFieldsBeingModified  = totalnumberofFieldsBeingModified + 1
                                # print("Header name is "+f)
                                hdrBitCount = self.getHeaderBitCount(f)
                                totalBitWidthOfTheAction = totalBitWidthOfTheAction + hdrBitCount
                                headerBitWidthOfFieldsBeingModified = headerBitWidthOfFieldsBeingModified + hdrBitCount
                            for f in listOfFieldBeingUsed:
                                # print("Header name is "+f)
                                totalNumberOfFieldsUsedAsParameter = totalNumberOfFieldsUsedAsParameter + 1
                                hdrBitCount = self.getHeaderBitCount(f)
                                totalBitWidthOfFieldsUsedAsParameter = totalBitWidthOfFieldsUsedAsParameter + hdrBitCount
                                totalBitWidthOfTheAction = totalBitWidthOfTheAction + hdrBitCount
                            if(totalBitWidthOfTheAction > maxBitWidthOfAction):
                                maxBitWidthOfAction = totalBitWidthOfTheAction
                            # print("action name "+str(a))
                            # print("maxBitWidthOfAction is "+str(maxBitWidthOfAction))
                    elif m.processedData.nodeType == P4ProgramNodeType.CONDITIONAL_NODE:

                        totalBitWidthOfTheAction=0
                        p4teConditionalNode = m.processedData
                        print("MAT node: "+p4teConditionalNode.name)

                        # print("conditional node for stage: "+str(k)+" is "+p4teConditionalNode.name)
                        listOfFieldBeingUsed = p4teConditionalNode.exprNode.getAllFieldList()
                        listOfFieldBeingUsedAsParameterInThisStage = listOfFieldBeingUsedAsParameterInThisStage + listOfFieldBeingUsed
                        print("Match Keys are: ")
                        if(m.addExtraBitInMatchKey):
                            matKeyLength = matKeyLength + 1
                            matKeyBitWidth = matKeyBitWidth+ 8
                            m.addExtraBitInMatchKey = False # Only one time adding a field for conditioanl of previsou stage  enough. Because, the TDG is basically uniqie path from top to bottom. so
                            #if there is a consitioanl in previous stage. only one bit is enogh in this stage
                            print("\t\t *) "+"8 bit key for handling conditional of previous stage")
                        for f in listOfFieldBeingUsed:
                                # print("Header name is "+f)
                                totalNumberOfFieldsUsedAsParameter = totalNumberOfFieldsUsedAsParameter + 1
                                hdrBitCount = self.getHeaderBitCount(f)
                                totalBitWidthOfFieldsUsedAsParameter = totalBitWidthOfFieldsUsedAsParameter + 2*  hdrBitCount
                        totalBitWidthOfTheAction = totalBitWidthOfFieldsUsedAsParameter
                        if(totalBitWidthOfTheAction > maxBitWidthOfAction):
                            maxBitWidthOfAction = totalBitWidthOfTheAction
                        # print("maxBitWidthOfAction is "+str(maxBitWidthOfAction))
                        print("Actions are: ")
                        print("\t\t *) "+str(p4teConditionalNode.oriiginalP4node.source_info))

                    else:
                        logger.error("In printStageWiseHWRequirements function found a unknow type node ")
                else:
                    logger.info("This is either dummy start or dummy end. They do not have any processed data")
            # print("Statistics for stage "+str(k))
            # print("totalnumberofFieldsBeingModified = "+str(totalnumberofFieldsBeingModified)+ " headerBitWidthOfFieldsBeingModified = "+str(headerBitWidthOfFieldsBeingModified))
            # print("totalNumberOfFieldsUsedAsParameter = "+str(totalNumberOfFieldsUsedAsParameter)+ " totalBitWidthOfFieldsUsedAsParameter = "+str(totalBitWidthOfFieldsUsedAsParameter))
            # print("maxBitWidthOfAction = "+str(maxBitWidthOfAction))
            # print("Total number of fields used as key in MAT is "+str(matKeyLength))
            # print("Key width is "+str(matKeyBitWidth))
            perStageHwRequirementsForThePipeline[k] = (totalnumberofFieldsBeingModified,headerBitWidthOfFieldsBeingModified, totalNumberOfFieldsUsedAsParameter,totalBitWidthOfFieldsUsedAsParameter, listOfFieldBeingModifedInThisStage, listOfFieldBeingUsedAsParameterInThisStage,maxBitWidthOfAction, matKeyLength, matKeyBitWidth)
            #perStageHwRequirementsForThePipeline[k] = (totalnumberofFieldsBeingModified,headerBitWidthOfFieldsBeingModified, totalNumberOfFieldsUsedAsParameter,maxBitWidthOfAction, listOfFieldBeingModifedInThisStage, listOfFieldBeingUsedAsParameterInThisStage)

        return perStageHwRequirementsForThePipeline

    def loadGraph(self):
        logger.info("Loading pipelines")
        if (len(self.parsedP4Program.pipelines) <= 0):
            logger.info("There is no pipelines found in the parsed Json representation. Exiting")
            exit(0)

        stageWiseMatMapForIngressPiepline = None
        perStageHwRequirementsForIngressPiepline = None
        stageWiseMatMapForEgressPiepline = None
        perStageHwRequirementsForEgressPiepline = None
        for pipeline in self.parsedP4Program.pipelines:
            if(pipeline.name == PipelineID.INGRESS_PIPELINE.value):
                newPipelineGraph = PipelineGraph(pipelineID=PipelineID.INGRESS_PIPELINE, pipeline = pipeline, actions= self.parsedP4Program.actions)
                self.pipelineIdToPipelineGraphMap[PipelineID.INGRESS_PIPELINE] = newPipelineGraph
                self.pipelineIdToPipelineMap[PipelineID.INGRESS_PIPELINE] = pipeline
                newPipelineGraph.loadNodes()
                # newPipelineGraph.populateGraph(self.pipelineIdToPipelineMap.get(PipelineID.INGRESS_PIPELINE).init_table, newPipelineGraph.dummystart )
                newPipelineGraph.populateDependencyGraphAsSimplePathGraph(self.pipelineIdToPipelineMap.get(PipelineID.INGRESS_PIPELINE).init_table, newPipelineGraph.dummyStart, newPipelineGraph.p4Graph,newPipelineGraph.dummyEnd,PipelineID.INGRESS_PIPELINE)
                # plt.subplot(111)
                # nx.draw_spring(newPipelineGraph.p4Graph, with_labels=False, font_weight='bold')
                # plt.show()
                print("Longest path legnth for Ingress pipeline is "+str(nx.dag_longest_path_length(newPipelineGraph.p4Graph)-2))

                # nx.nx_agraph.write_dot(newPipelineGraph.p4Graph,'test.dot')
                #
                # # same layout using matplotlib with no labels
                # plt.title('draw_networkx')
                # pos=graphviz_layout(newPipelineGraph.p4Graph, prog='dot')
                # nx.draw(newPipelineGraph.p4Graph, pos, with_labels=True, arrows=False)
                # plt.savefig('nx_test.png')
                # logger.info("Loaded Ingress pipeline")
                # newPipelineGraph.p4Graph = dfs_tree(newPipelineGraph.p4Graph, newPipelineGraph.dummyStart)
                A = to_agraph(newPipelineGraph.p4Graph)

                # print(A)
                for node in newPipelineGraph.p4Graph.nodes():
                    n=A.get_node(node)
                    n.attr['shape']='box'
                    n.attr['style']='filled'
                    n.attr['fillcolor']='turquoise'
                    # n.attr['node_size']=1
                # A.layout(prog="neato", args="-Nshape=circle -Efontsize=20")
                A.layout('dot',args="-Nshape=circle -Efontsize=20")
                A.draw('ingress.png')
                logger.info("Loaded Ingress pipeline")
                # print("Topological sort of the ingress graoph is ")
                stageWiseMatMapForIngressPiepline,perStageHwRequirementsForIngressPiepline,registerNameToStageMapForIngress = self.stageWiseMATEorSinglePipelineForP4TE(piepelineId= PipelineID.INGRESS_PIPELINE)
                print("total nodes in graph are "+str(len(list(newPipelineGraph.p4Graph.nodes))-2)) # -2 for skipping the dummy start and end node
                count = 0
                for k in stageWiseMatMapForIngressPiepline.keys():
                    count = count + len(stageWiseMatMapForIngressPiepline.get(k))
                print("total nodes in stageWiseMatMap are "+str(count))
            if(pipeline.name == PipelineID.EGRESS_PIPELINE.value):
                newPipelineGraph = PipelineGraph(pipelineID=PipelineID.EGRESS_PIPELINE, pipeline = pipeline, actions= self.parsedP4Program.actions)
                self.pipelineIdToPipelineGraphMap[PipelineID.EGRESS_PIPELINE] = newPipelineGraph
                self.pipelineIdToPipelineMap[PipelineID.EGRESS_PIPELINE] = pipeline
                newPipelineGraph.loadNodes()
                # newPipelineGraph.populateGraph(self.pipelineIdToPipelineMap.get(PipelineID.EGRESS_PIPELINE).init_table, newPipelineGraph.dummystart )
                newPipelineGraph.populateDependencyGraphAsSimplePathGraph(self.pipelineIdToPipelineMap.get(PipelineID.EGRESS_PIPELINE).init_table, newPipelineGraph.dummyStart, newPipelineGraph.p4Graph,newPipelineGraph.dummyEnd,PipelineID.EGRESS_PIPELINE)
                # plt.subplot(111)
                # nx.draw_spring(newPipelineGraph.p4Graph, with_labels=False, font_weight='bold')
                # plt.show()
                print("Longest path legnth for Egress pipeline is "+str(nx.dag_longest_path_length(newPipelineGraph.p4Graph)-2))

                # logger.info("Loaded Egress pipeline")
                # nx.nx_agraph.write_dot(newPipelineGraph.p4Graph,'test.dot')
                # # same layout using matplotlib with no labels
                # plt.title('draw_networkx')
                # pos=graphviz_layout(newPipelineGraph.p4Graph, prog='dot')
                # nx.draw(newPipelineGraph.p4Graph, pos, with_labels=False, arrows=True,node_size=60,font_size=8)
                # plt.savefig('nx_test.png')

                A = to_agraph(newPipelineGraph.p4Graph)
                for node in newPipelineGraph.p4Graph.nodes():
                    n=A.get_node(node)
                    n.attr['shape']='box'
                    n.attr['style']='filled'
                    n.attr['fillcolor']='turquoise'
                # print(A)
                A.layout('dot')
                A.draw('egress.png')
                logger.info("Loaded Egress pipeline")
                stageWiseMatMapForEgressPiepline,perStageHwRequirementsForEgressPiepline,registerNameToStageMapForEgress = self.stageWiseMATEorSinglePipelineForP4TE(piepelineId= PipelineID.EGRESS_PIPELINE)
                print("total nodes in graph are "+str(len(list(newPipelineGraph.p4Graph.nodes))))
                count = 0
                for k in stageWiseMatMapForEgressPiepline.keys():
                    count = count + len(stageWiseMatMapForEgressPiepline.get(k))
                print("total nodes in stageWiseMatMap are "+str(count))
        print("\n\n\n\n\n\n\n\n\n\n\n")
        for stageIndex in range(0,32):
            if (perStageHwRequirementsForIngressPiepline.get(stageIndex) != None):
                totalnumberofFieldsBeingModifiedInIngress,headerBitWidthOfFieldsBeingModifiedInIngress, totalNumberOfFieldsUsedAsParameterInIngress, \
                totalBitWidthOfFieldsUsedAsParameterInIngress, listOfFieldBeingModifedInThisIngressStage, listOfFieldBeingUsedAsParameterInThisIngressStage,\
                maxBitWidthOfActionInIngress, matKeyLengthForIngressStage, matKeyBitWidthForIngressStage = perStageHwRequirementsForIngressPiepline.get(stageIndex)
            else:
                totalnumberofFieldsBeingModifiedInIngress,headerBitWidthOfFieldsBeingModifiedInIngress, totalNumberOfFieldsUsedAsParameterInIngress, \
                totalBitWidthOfFieldsUsedAsParameterInIngress,  listOfFieldBeingModifedInThisIngressStage, listOfFieldBeingUsedAsParameterInThisIngressStage, \
                maxBitWidthOfActionInIngress, matKeyLengthForIngressStage, matKeyBitWidthForIngressStage = 0,0,0,0, [], [],0, 0,0
            if (perStageHwRequirementsForEgressPiepline.get(stageIndex) != None):
                totalnumberofFieldsBeingModifiedInEgress,headerBitWidthOfFieldsBeingModifiedInEgress, totalNumberOfFieldsUsedAsParameterEgress, \
                totalBitWidthOfFieldsUsedAsParameterEgress,listOfFieldBeingModifedInThisEgressStage, listOfFieldBeingUsedAsParameterInThisEgressStage,\
                maxBitWidthOfActionInEgress,matKeyLengthForEgressStage, matKeyBitWidthForEgressStage = perStageHwRequirementsForEgressPiepline.get(stageIndex)
            else:
                totalnumberofFieldsBeingModifiedInEgress,headerBitWidthOfFieldsBeingModifiedInEgress, totalNumberOfFieldsUsedAsParameterEgress, \
                totalBitWidthOfFieldsUsedAsParameterEgress,listOfFieldBeingModifedInThisEgressStage, listOfFieldBeingUsedAsParameterInThisEgressStage,\
                maxBitWidthOfActionInEgress,matKeyLengthForEgressStage, matKeyBitWidthForEgressStage  = 0,0,0,0, [] , [],0,0,0
            print("\n \n \n Total Resource usage in stage -- "+str(stageIndex+1)+" is follwoing ")
            print("Total number of fileds used as key for MAT = "+str(matKeyLengthForIngressStage + matKeyLengthForEgressStage))
            print("Total bit width of the MAT Keys for ingress stage = "+str((matKeyBitWidthForIngressStage )))
            print("Total bit width of the MAT Keys for egress stage = "+str(( matKeyBitWidthForEgressStage)))
            print("Total ununsed MAT Key bitwidth = "+str(( 1280- matKeyBitWidthForIngressStage - matKeyBitWidthForEgressStage)))
            print("Mat key statistics Values for graph drawing "+str(stageIndex+1)+ "   "+str(matKeyBitWidthForIngressStage)+ "  "+str(matKeyBitWidthForEgressStage)+"   "+str(( 1280- matKeyBitWidthForIngressStage - matKeyBitWidthForEgressStage)))
            print("totalnumberofFieldsBeingModified = "+str(totalnumberofFieldsBeingModifiedInIngress + totalnumberofFieldsBeingModifiedInEgress)+ " headerBitWidthOfFieldsBeingModified = "+str(headerBitWidthOfFieldsBeingModifiedInIngress + headerBitWidthOfFieldsBeingModifiedInEgress))
            print("totalNumberOfFieldsUsedAsParameter = "+str(totalNumberOfFieldsUsedAsParameterInIngress+totalNumberOfFieldsUsedAsParameterEgress)+ " totalBitWidthOfFieldsUsedAsParameter = "+str(totalBitWidthOfFieldsUsedAsParameterInIngress + totalBitWidthOfFieldsUsedAsParameterEgress))
            print("Maximum bitwdth of the actions used for Ingress Stage = "+str(maxBitWidthOfActionInIngress ))
            print("Maximum bitwdth of the actions used for Egress Stage = "+str( maxBitWidthOfActionInEgress))
            print("Total unused action key bitwidth = "+str( 1280- (maxBitWidthOfActionInIngress+maxBitWidthOfActionInEgress)))
            print("Action Key field statistics for graph drawing "+str(stageIndex+1)+ "   "+str(maxBitWidthOfActionInIngress)+ "  "+str(maxBitWidthOfActionInEgress)+"   "+str((  1280- (maxBitWidthOfActionInIngress+maxBitWidthOfActionInEgress))))
            print("Common elements modified by ingress and egress in this stage is "+str(list(set(listOfFieldBeingModifedInThisIngressStage) & set(listOfFieldBeingModifedInThisEgressStage))))
            print("Common elements used as parameter by ingress and egress in this stage is "+str(list(set(listOfFieldBeingUsedAsParameterInThisIngressStage) & set(listOfFieldBeingUsedAsParameterInThisEgressStage))))

            if stageIndex in registerNameToStageMapForIngress.values():
                for k,v in registerNameToStageMapForIngress.items():
                    if v==stageIndex:
                        print("Following Register Array from ingress portion of pipeline is mapped to this stage ")
                        print("\t\t Register Array name:"+str(k))
            # else:
            #     print("None")

            if stageIndex in registerNameToStageMapForEgress.values():
                for k,v in registerNameToStageMapForEgress.items():
                    if v==stageIndex:
                        print("Following Register Array from egress portion of pipeline is mapped to this stage ")
                        print("Register Array name:"+str(k))
            # else:
            #     print("None")


        # print("All graph loadig completed")




    #
    # def loadPipelineGraph(self, pipelineID, pipelineGraph):
    #     pipeline = self.pipelineIdToPipelineGraphMap[pipelineID]
    #     if(pipeline == None):
    #         logger.info("Pipeline not found in the parsed program representation. Exiting")
    #         exit(1)
    #     for tbl in pipeline.tables:
    #         print(tbl.name + " -- "+ str(tbl.type)+ "--"+str(tbl.match_type))
    #         # print(tbl)




#             iterate over all the table. if a table has key null and match exact then it is action. In that case the action name and table name will be same
#             a piepeline can start with either table or conditional
#
#
#         # load actions into some data structure in porder . keep them in a map with key from name and also id.
#         # then build the graph.
#         # then do the dependency analysis
#
# for each pipeline build a dummy start node.
#     traverse the table and actions . if a node has no dependency it's predecesor will be the dummy start.
#
#
# need to implement 4 functions to check nodes dependency.
#
# trouble can happen in building the graph in the case: a - b - c - d. assume d habe no immediate dependency on c. bt d has a dependency with a.
# so what we can do is, maintaining a name wise map for all the nodes already inserted. so when we are processing d this map will contain
#     a,b,c . so we need to check with whom d has a dependenacy. so we will add edge with it. whenever add an edge. add a type propert with it.
#
#         pass

# make a function that will iterate over all the table in the pipeline. O(n^2 loop) This will
# check for all types of depenedency. And It wil Keep 4 maps with dependency types.
#
#
#     make 4 supplimentaty function that will take 2 nodes and find their dependency tyoe
# (node 1 , node 2)
#
# node1 types == action and node 2 type == table
#
# both action
#
# both talbe
# one action one confitional
