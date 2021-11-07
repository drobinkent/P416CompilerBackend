
from DependencyAnlyzer.DefinitionConstants import P4ProgramNodeType
from P4ProgramParser.P416JsonParser import PrimitiveOpblock, Expression, PrimitiveField, RegisterArrayPrimitive, HexStr, \
    PrimitiveHeader, BoolPrimitive, Table

import networkx as nx
import logging
import ConfigurationConstants as confConst
logger = logging.getLogger('P4ProgramNode')
hdlr = logging.FileHandler(confConst.LOG_FILE_PATH )
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)

class P4ProgramNode:

    def __init__(self, parsedP4Node, name, parsedP4NodeType, pipelineID):
        self.parsedP4Node = parsedP4Node
        self.parsedP4NodeType = parsedP4NodeType
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


    def expressionToSubgraph(self):
        # if (e == None):
        #     return
        e = self.parsedP4Node
        op = e.type
        left = e.value.left
        right = e.value.right
        newGraph= nx.DiGraph()
        newGraph.add_node(self.parsedP4Node)

        if((left==None) and (right==None)):
            return None
        elif(type(self.parsedP4Node) == PrimitiveOpblock):
            return self.parsedP4Node, newGraph
        # header_Stack and stack_field are not supported  in parsing. If they are supported in parsing we can handle them here also


        # print("left type is "+str(type(left)))
        # print("right type is "+str(type(right)))
        if((left==None) or (type(left) == HexStr) or (type(left) == PrimitiveField) or (type(left) == PrimitiveHeader) or (type(left) == BoolPrimitive) or \
           (type(left) == RegisterArrayPrimitive) ) \
                and ((right==None) or (type(right) == HexStr) or (type(right) == PrimitiveField) or (type(right) == PrimitiveHeader) or (type(right) == BoolPrimitive) or \
                     (type(right) == RegisterArrayPrimitive)   ):
            #make a single node and add to the graph
            primOpNode = PrimitiveOpblock(primitiveOP = op, left = left, right=right)
            newP4Node = P4ProgramNode(parsedP4Node = primOpNode, name = self.name+"left"+"right", parsedP4NodeType= P4ProgramNodeType.PRIMITIVE_OP_NODE, pipelineID=self.pipelineID)
            newGraph.add_node(newP4Node)
            newGraph.add_edge(self.parsedP4Node, newP4Node)
        if (type(left) == PrimitiveOpblock):
            newP4Node = P4ProgramNode(parsedP4Node = left, name = self.name+"left"+"_primitive_op_block",  parsedP4NodeType= P4ProgramNodeType.PRIMITIVE_OP_NODE, pipelineID=self.pipelineID)
            newGraph.add_node(newP4Node)
            newGraph.add_edge(self.parsedP4Node, newP4Node)
        if (type(right) == PrimitiveOpblock):
            newP4Node = P4ProgramNode(parsedP4Node = right, name = self.name+"right_primitive_op_block", parsedP4NodeType= P4ProgramNodeType.PRIMITIVE_OP_NODE, pipelineID=self.pipelineID)
            newGraph.add_node(newP4Node)
            newGraph.add_edge(self.parsedP4Node, newP4Node)
        if (type(left) == Expression):
            eNode = ExpressionNode(parsedP4Node = left, name = self.name+"left_expression",  parsedP4NodeType = P4ProgramNodeType.EXPRESSION_NODE, pipelineID=self.pipelineID)
            newRoot, subGraph = eNode.expressionToSubgraph()
            newGraph1= nx.DiGraph()
            newGraph1.add_edges_from(newGraph.edges())
            newGraph1.add_edges_from(subGraph.edges())
            newGraph1.add_nodes_from(newGraph.nodes())
            newGraph1.add_nodes_from(subGraph.nodes())
            newGraph1.add_edge(self.parsedP4Node, newRoot)
            newGraph = newGraph1
        if (type(right) == Expression):
            eNode = ExpressionNode(parsedP4Node = right, name = self.name+"right_expression", parsedP4NodeType = P4ProgramNodeType.EXPRESSION_NODE, pipelineID=self.pipelineID)
            newRoot, subGraph = eNode.expressionToSubgraph()
            newGraph1= nx.DiGraph()
            newGraph1.add_edges_from(newGraph.edges())
            newGraph1.add_edges_from(subGraph.edges())
            newGraph1.add_nodes_from(newGraph.nodes())
            newGraph1.add_nodes_from(subGraph.nodes())
            newGraph1.add_edge(self.parsedP4Node, newRoot)
            newGraph = newGraph1
        return self.parsedP4Node, newGraph


    def getAllFieldList(self):
        root, exprGraph = self.expressionToSubgraph()
        nodesWithfiledList = [x for x in exprGraph.nodes() if exprGraph.out_degree(x)==0 and exprGraph.in_degree(x)==1]
        fieldList = []
        for n in nodesWithfiledList:
            lvalue = n.parsedP4Node.left
            if((lvalue != None ) and (type(lvalue)== PrimitiveField)):
                fieldName = lvalue.header_name + "."+ lvalue.field_memeber_name
                fieldList.append(fieldName)
            elif((lvalue != None ) and (type(lvalue)== PrimitiveField)):
                logger.info("A node in expession found which is not PrimitiveField. Check It!!!")
            rvalue = n.parsedP4Node.right
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
        also implement the operator (architecture specific) wise analysis. But so far no line rate hardware supporting these things. so safely skiping them
        :return:
        '''
        root, exprGraph = self.expressionToSubgraph()
        nodesWithfiledList = [x for x in exprGraph.nodes() if exprGraph.out_degree(x)==0 and exprGraph.in_degree(x)==1]
        fieldList = []
        for n in nodesWithfiledList:
            lvalue = n.parsedP4Node.value.left
            if((lvalue != None ) and (type(lvalue)== PrimitiveField)):
                fieldName = lvalue.header_name + "."+ lvalue.field_memeber_name
                fieldList.append(fieldName)
            elif((lvalue != None ) and (type(lvalue)== PrimitiveField)):
                logger.info("A node in expession found which is not PrimitiveField. Check It!!!")
        return fieldList




class MATNode:
    nodeType = None

    def __init__(self, nodeType, name, originalP4node):
        self.nodeType = nodeType
        self.nextNodes= []
        self.name = name
        self.matchKeyFields = []
        self.actions= []
        self.originalP4node = originalP4node
        self.isVisitedForDraw=False
        self.actionObjectList  = []
        self.isVisitedForTDGProcessing=False
        self.subTableMatNodes = []
        self.predecessors = {}
        self.ancestors = {}
        self.dependencies = {}
        self.statefulMemoryDependencies = {}
        self.levelForStatefulMemory=-1
        self.finalLevel = -1
        self.selfStatefulMemoryNameToLevelMap={}
        self.neighbourAssignedStatefulMemoryNameToLevelMap={}  # TODO : this may not be necessary even . on that tcase we will remove it
        return

    def setLevelForStatefulMemeoryBySelf(self, statefulMemeoryName, level):
        if(self.selfStatefulMemoryNameToLevelMap.get(statefulMemeoryName) == None):
            self.selfStatefulMemoryNameToLevelMap[statefulMemeoryName] = level
            return level
        else:
            oldLevel =self.selfStatefulMemoryNameToLevelMap.get(statefulMemeoryName)
            if(oldLevel > level):
                return oldLevel
            else:
                self.selfStatefulMemoryNameToLevelMap[statefulMemeoryName] = level
                return level

    def setNeighbourAssignedLevelForStatefulMemeory(self, statefulMemeoryName, level):
        if(self.neighbourAssignedStatefulMemoryNameToLevelMap.get(statefulMemeoryName) == None):
            self.neighbourAssignedStatefulMemoryNameToLevelMap[statefulMemeoryName] = level
            return level
        else:
            oldLevel =self.neighbourAssignedStatefulMemoryNameToLevelMap.get(statefulMemeoryName)
            if(oldLevel > level):
                return oldLevel
            else:
                self.neighbourAssignedStatefulMemoryNameToLevelMap[statefulMemeoryName] = level
                return level

    def getMaxLevelOfSelfStatefulMemories(self):
        max = -1
        for k in self.selfStatefulMemoryNameToLevelMap.keys():
            val = self.selfStatefulMemoryNameToLevelMap.get(k)
            if val>max:
                max = val
        return max
    def getMaxLevelOfSelfStatefulMemoriesAssignedByNeighbours(self):
        max = -1
        for k in self.neighbourAssignedStatefulMemoryNameToLevelMap.keys():
            val = self.neighbourAssignedStatefulMemoryNameToLevelMap.get(k)
            if val>max:
                max = val
        return max
    def getMaxLevelOfSelfStatefulMemoryAssignedByNeighbours(self, statefulMemoeryName):
        if(self.neighbourAssignedStatefulMemoryNameToLevelMap.get(statefulMemoeryName) == None):
            return -1
        else:
            return self.neighbourAssignedStatefulMemoryNameToLevelMap.get(statefulMemoeryName)

    def getMaxLevelOfSelfStatefulMemoryAssignedBySelf(self, statefulMemoeryName):
        if(self.selfStatefulMemoryNameToLevelMap.get(statefulMemoeryName) == None):
            return -1
        else:
            return self.selfStatefulMemoryNameToLevelMap.get(statefulMemoeryName)

    def getMaxLevelOfAllStatefulMemories(self):
        val1 = self.getMaxLevelOfSelfStatefulMemories()
        val2 = self.getMaxLevelOfSelfStatefulMemoriesAssignedByNeighbours()
        return max(val1, val2)
    def setLevelOfAllStatefulMemories(self,level):
        for k in self.selfStatefulMemoryNameToLevelMap.keys():
            self.selfStatefulMemoryNameToLevelMap[k] = level


    def addStatefulMemoryDependency(self, statefulMemoryName, matNode):
        flag = False
        # for k in self.statefulMemoryDependencies.keys():
        #     if (self.statefulMemoryDependencies.get(k).name == matNode.name ):
        #         flag = True
        if(self.statefulMemoryDependencies.get(statefulMemoryName) == None):
            self.statefulMemoryDependencies[statefulMemoryName] = []
        for depList in self.statefulMemoryDependencies.values():
            for dep in depList:
                if dep.name == matNode.name:
                    flag = True
        if(flag == False):
            depList = self.statefulMemoryDependencies.get(statefulMemoryName)
            depList.append(matNode)
            self.statefulMemoryDependencies[statefulMemoryName] = depList

    def getAllMatchFields(self):
        # if(type(self.originalP4node)== Table):
        #     self.matchKeyFields = self.originalP4node.getAllMatchfields()
        '''
        Maek sure  the mathod is called after a node is propoerly loaded up with its originial P4 node
        :return:
        '''
        return self.matchKeyFields

    def getListOfFieldsModifedAndUsed(self):
        listOfFieldBeingModifed = []
        listOfFieldBeingUsed = []
        for a in self.actions:
            filedsModifiedInAction, fieldsdUsedInAction = a.getListOfFieldsModifedAndUsed()
            listOfFieldBeingModifed = listOfFieldBeingModifed + filedsModifiedInAction
            listOfFieldBeingUsed = listOfFieldBeingUsed + fieldsdUsedInAction
        return listOfFieldBeingModifed, listOfFieldBeingUsed




class Dependency:

    def __init__(self,dependencyType, src, dst ):
        self.dependencyType = dependencyType
        self.src = src
        self.dst = dst



