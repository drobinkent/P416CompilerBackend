
from DependencyAnlyzer.DefinitionConstants import P4ProgramNodeType, PipelineID, DependencyType
from P4ProgramParser.P416JsonParser import PrimitiveOpblock, Expression, PrimitiveField, RegisterArrayPrimitive, HexStr, \
    PrimitiveHeader, BoolPrimitive, Table, Key, MatchType, TableType, GraphColor, HeaderField, \
    ActionResourceConsumptionStatistics

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
        # self.stageIndex = None
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
        self.matchKeyFields = None
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
        self.levelForStatefulMemoryAssignmentStep=-1
        self.finalLevel = -1
        self.selfStatefulMemoryNameToLevelMap={}
        self.bifurcationCounter = 0
        self.inDegree= 0
        self.actionNameToResourceConsumptionStatisticsMap={}
        self.totalKeysTobeMatched = 0
        self.matKeyBitWidth =0
        self.headerFieldWiseBitwidthOfMatKeys = {}
        # self.neighbourAssignedStatefulMemoryNameToLevelMap={}  # TODO : this may not be necessary even . on that tcase we will remove it
        return

    # listOfFieldBeingModifed, listOfFieldBeingUsed,listOfStatefulMemoryBeingAccessed, actionCrossbarBitwidth

    def getTotalAmountOfActionMemoryRequiredInBits(self):
        '''
        Key point to remeber: here we are assuming that, all action will need all action parameter. But in reality different action will need different number of parmaters.
        Hence their action memory requirement will be different
        :return:
        '''
        return self.originalP4node.max_size * self.getMaxBitwidthOfActionParameter()

    def getTotalMatEntries(self):
        return self.originalP4node.max_size

    def getMaxBitwidthOfActionParameter(self):
        maxValue = -1
        for actionName in self.actionNameToResourceConsumptionStatisticsMap.keys():
            actionResourceConsumptionStatistics = self.actionNameToResourceConsumptionStatisticsMap.get(actionName)
            if(actionResourceConsumptionStatistics.allActionParameterSizeInBits >maxValue ):
                maxValue = actionResourceConsumptionStatistics.allActionParameterSizeInBits
        return  maxValue

    def getMaxNumberOfFieldsUsedAndModifedByAnyAction(self):
        '''
        This function returns the maxinum number of fields  used by any action.
        :return:
        '''
        maxValue = -1
        for actionName in self.actionNameToResourceConsumptionStatisticsMap.keys():
            actionResourceConsumptionStatistics = self.actionNameToResourceConsumptionStatisticsMap.get(actionName)
            if(len(actionResourceConsumptionStatistics.listOfFieldBeingUsed) + len(actionResourceConsumptionStatistics.listOfFieldBeingModifed) >maxValue ):
                maxValue = len(actionResourceConsumptionStatistics.listOfFieldBeingUsed) + len(actionResourceConsumptionStatistics.listOfFieldBeingModifed)
        return  maxValue
    def getMaxActionCrossbarBitwidthRequiredByAnyAction(self):
        '''
        This function returns the maxinum number of fields  used by any action.
        :return:
        '''
        maxValue = -1
        for actionName in self.actionNameToResourceConsumptionStatisticsMap.keys():
            # actionResourceConsumptionStatistics = ActionResourceConsumptionStatistics()
            actionResourceConsumptionStatistics = self.actionNameToResourceConsumptionStatisticsMap.get(actionName)
            if(actionResourceConsumptionStatistics.actionCrossbarBitwidth >maxValue ):
                maxValue = actionResourceConsumptionStatistics.actionCrossbarBitwidth
        return  maxValue

    def bifurcateNodeBasedOnStatefulMemeory(self, statefulMemoryNameList, newMatPrefix,pipelineGraph,pipelineID,parsedP4Program ):
        oldLevel = self.getMaxLevelOfAllStatefulMemories()
        confConst.MAT_DIVIDER_KEY_COUNTER = confConst.MAT_DIVIDER_KEY_COUNTER + 1
        newMatPrefix= newMatPrefix+"_"+str(confConst.MAT_DIVIDER_KEY_COUNTER)
        combinedStatefulMemName = ""
        for m in statefulMemoryNameList:
            combinedStatefulMemName = combinedStatefulMemName + "_"+m
        for actionObject in self.actions:
            statefulMemoeryBeingUsed = actionObject.getListOfStatefulMemoriesBeingUsed()
            for statefulMem in statefulMemoeryBeingUsed:
                if ((self.name in pipelineGraph.registerNameToTableMap.get(statefulMem))):
                    pipelineGraph.registerNameToTableMap.get(statefulMem).remove(self.name)

        originalMatNodeActions=[]
        newMatNodeActions=[]
        newAction = None
        for a in self.actions:
            newAction = a.bifurcateActionBasedOnStatefulMemeory(statefulMemoryNameList,newActionNamePrefix= newMatPrefix)
            originalMatNodeActions.append(a)
            newMatNodeActions.append(newAction)
            parsedP4Program.actions.append(newAction)
        actionNames = []
        for a in newMatNodeActions:
            actionNames.append(a.name)
        #TODO: if any one action is NO-action then the bifurated action pair will also contain another NO-ACTION action. Though it is not really important from
        #TODO check whther we are adding the new actions into parsedP4Program.actions list
        #resource reservation perspective, but if we want to generate actual hardware instrutions we have to handle this.


        newP4Node = None
        newTableName = ""
        newKey = None
        if(pipelineID == PipelineID.INGRESS_PIPELINE):
            newKey = Key.from_dict(confConst.SPECIAL_KEY_FOR_DIVIDING_MAT_IN_INGRESS)
            newTableName = newMatPrefix+self.name+"_"+str(confConst.MAT_DIVIDER_KEY_COUNTER)
            keyName = confConst.SPECIAL_KEY_FOR_DIVIDING_MAT_IN_INGRESS_NAME+"_"+str(confConst.MAT_DIVIDER_KEY_COUNTER)
            newKey.name = keyName
            newKey.target[1] = newKey.target[1] +"_"+str(confConst.MAT_DIVIDER_KEY_COUNTER)
            parsedP4Program.nameToHeaderTypeObjectMap[keyName] = HeaderField(name = keyName,bitWidth=confConst.SPECIAL_KEY_FOR_DIVIDING_MAT_IN_INGRESS_BIT_WIDTH, isSigned=True, \
                                                                             mutlipleOf8Bitwidth= confConst.SPECIAL_KEY_FOR_CARRYING_CODNDITIONAL_RESULT_IN_INGRESS_BIT_WIDTH, \
                                                                             mappedPhyscialHeaderVectorFieldBitwdith=confConst.SPECIAL_KEY_FOR_CARRYING_CODNDITIONAL_RESULT_IN_INGRESS_BIT_WIDTH)
            #If we want to add the spcial key for at divider then add this. other wise the next version where key is null
            # newP4Node = Table(name = newTableName, id=self.originalP4node.id, source_info=self.originalP4node.source_info,
            #                   key=[newKey], match_type=MatchType.EXACT, type=TableType, max_size=confConst.DIVIDED_MAT_MAX_ENTRIES,
            #                   with_counters=True, support_timeout=True, action_ids=[], actions=actionNames,
            #                   next_tables=self.originalP4node.next_tables, is_visited_for_conditional_preprocessing=False,
            #                   is_visited_for_stateful_memory_preprocessing=False,is_visited_for_graph_drawing=GraphColor.WHITE,
            #                   is_visited_for_TDG_processing=GraphColor.WHITE, direct_meters=[], base_default_next=None, default_entry=None, action_profile=None)
            newP4Node = Table(name = newTableName, id=self.originalP4node.id, source_info=self.originalP4node.source_info,
                              key=[], match_type=MatchType.EXACT, type=TableType, max_size=confConst.DIVIDED_MAT_MAX_ENTRIES,
                              with_counters=True, support_timeout=True, action_ids=[], actions=actionNames,
                              next_tables=self.originalP4node.next_tables, is_visited_for_conditional_preprocessing=False,
                              is_visited_for_stateful_memory_preprocessing=False,is_visited_for_graph_drawing=GraphColor.WHITE,
                              is_visited_for_TDG_processing=GraphColor.WHITE, direct_meters=[], base_default_next=None, default_entry=None, action_profile=None)
        elif(pipelineID == PipelineID.EGRESS_PIPELINE):
            newTableName = newMatPrefix+self.name+"_"+str(confConst.MAT_DIVIDER_KEY_COUNTER)
            newKey = Key.from_dict(confConst.SPECIAL_KEY_FOR_DIVIDING_MAT_IN_EGRESS)
            keyName = confConst.SPECIAL_KEY_FOR_DIVIDING_MAT_IN_EGRESS_NAME+"_"+str(confConst.MAT_DIVIDER_KEY_COUNTER)
            newKey.name = keyName
            newKey.target[1] = newKey.target[1] +"_"+str(confConst.MAT_DIVIDER_KEY_COUNTER)
            parsedP4Program.nameToHeaderTypeObjectMap[keyName] = HeaderField(name = keyName,bitWidth=confConst.SPECIAL_KEY_FOR_DIVIDING_MAT_IN_EGRESS_BIT_WIDTH, isSigned=True, \
                    mutlipleOf8Bitwidth= confConst.SPECIAL_KEY_FOR_DIVIDING_MAT_IN_EGRESS_BIT_WIDTH, \
                                         mappedPhyscialHeaderVectorFieldBitwdith=confConst.SPECIAL_KEY_FOR_DIVIDING_MAT_IN_EGRESS_BIT_WIDTH)
            #If we want to add the spcial key for at divider then add this. other wise the next version where key is null
            # newP4Node = Table(name = newTableName, id=self.originalP4node.id, source_info=self.originalP4node.source_info,
            #                   key=[newKey], match_type=MatchType.EXACT, type=TableType, max_size=confConst.DIVIDED_MAT_MAX_ENTRIES,
            #                   with_counters=True, support_timeout=True, action_ids=[], actions=actionNames,
            #                   next_tables=self.originalP4node.next_tables, is_visited_for_conditional_preprocessing=False,
            #                   is_visited_for_stateful_memory_preprocessing=False,is_visited_for_graph_drawing=GraphColor.WHITE,
            #                   is_visited_for_TDG_processing=GraphColor.WHITE, direct_meters=[], base_default_next=None, default_entry=None, action_profile=None)
            newP4Node = Table(name = newTableName, id=self.originalP4node.id, source_info=self.originalP4node.source_info,
                              key=[], match_type=MatchType.EXACT, type=TableType, max_size=confConst.DIVIDED_MAT_MAX_ENTRIES,
                              with_counters=True, support_timeout=True, action_ids=[], actions=actionNames,
                              next_tables=self.originalP4node.next_tables, is_visited_for_conditional_preprocessing=False,
                              is_visited_for_stateful_memory_preprocessing=False,is_visited_for_graph_drawing=GraphColor.WHITE,
                              is_visited_for_TDG_processing=GraphColor.WHITE, direct_meters=[], base_default_next=None, default_entry=None, action_profile=None)
        self.next_tables=[newP4Node.name]
        newMatNode = MATNode(nodeType= P4ProgramNodeType.TABLE_NODE, name= newP4Node.name, originalP4node= newP4Node)
        # newMatNode.matchKeyFields = [newKey.name] #If we want to use the new special key as a key field
        newMatNode.matchKeyFields = []
        pipelineGraph.pipeline.tables.append(newP4Node)
        newMatNode.actions = newMatNodeActions
        newMatNode.ancestors = self.ancestors
        pipelineGraph.allTDGNode[newMatNode.name] = newMatNode
        self.ancestors = {}
        self.ancestors[newMatNode.name] = newMatNode
        newMatNode.dependencies = self.dependencies
        self.dependencies = {}
        self.dependencies[newMatNode.name] = Dependency(dependencyType = DependencyType.MATCH_DEPENDENCY, src = self, dst = newMatNode )
        tempActions = self.actions
        self.actions=newMatNodeActions
        newMatNode.actions=tempActions
        # for sfName in statefulMemoryNameList:
        #     if(self.selfStatefulMemoryNameToLevelMap.get(sfName)!= None):
        #         self.selfStatefulMemoryNameToLevelMap.pop(sfName)
        for actionObject in newMatNode.actions:
            statefulMemoeryBeingUsed = actionObject.getListOfStatefulMemoriesBeingUsed()
            for statefulMem in statefulMemoeryBeingUsed:
                if(pipelineGraph.registerNameToTableMap.get(statefulMem) == None):
                    pipelineGraph.registerNameToTableMap[statefulMem] = []
                if (not(newMatNode.name in pipelineGraph.registerNameToTableMap.get(statefulMem))):
                    pipelineGraph.registerNameToTableMap.get(statefulMem).append(newMatNode.name)
        for actionObject in self.actions:
            statefulMemoeryBeingUsed = actionObject.getListOfStatefulMemoriesBeingUsed()
            for statefulMem in statefulMemoeryBeingUsed:
                if(pipelineGraph.registerNameToTableMap.get(statefulMem) == None):
                    pipelineGraph.registerNameToTableMap[statefulMem] = []
                if (not(self.name in pipelineGraph.registerNameToTableMap.get(statefulMem))):
                    pipelineGraph.registerNameToTableMap.get(statefulMem).append(self.name)

        # graphTobedrawn = nx.MultiDiGraph()
        # pipelineGraph.pipeline.resetAllIsVisitedVariableForGraph()
        # pipelineGraph.getTDGGraphWithAllDepenedencyAndMatNode(curNode = pipelineGraph.allTDGNode.get(confConst.DUMMY_START_NODE), predNode=None, dependencyBetweenCurAndPred=None, tdgGraph=graphTobedrawn)
        # pipelineGraph.drawPipeline(nxGraph = graphTobedrawn, filePath="tempGraph"+str(pipelineGraph.pipelineID)+".jpg")
        newMatNode.setLevelOfAllStatefulMemories(oldLevel)
        removedLevelMap = self.keepStatefulMemoryLevelsAndDeleteRests(regNameList=statefulMemoryNameList)
        newMatNode.selfStatefulMemoryNameToLevelMap = removedLevelMap
        return newMatNode





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

    # def setNeighbourAssignedLevelForStatefulMemeory(self, statefulMemeoryName, level):
    #     if(self.neighbourAssignedStatefulMemoryNameToLevelMap.get(statefulMemeoryName) == None):
    #         self.neighbourAssignedStatefulMemoryNameToLevelMap[statefulMemeoryName] = level
    #         return level
    #     else:
    #         oldLevel =self.neighbourAssignedStatefulMemoryNameToLevelMap.get(statefulMemeoryName)
    #         if(oldLevel > level):
    #             return oldLevel
    #         else:
    #             self.neighbourAssignedStatefulMemoryNameToLevelMap[statefulMemeoryName] = level
    #             return level

    def getStatefulMemoryNameToLevelMap(self):
        return self.selfStatefulMemoryNameToLevelMap
    def getMaxLevelOfAllStatefulMemories(self):
        maxVal = -1

        for k in self.selfStatefulMemoryNameToLevelMap.keys():
            val = self.selfStatefulMemoryNameToLevelMap.get(k)
            if val>maxVal:
                maxVal = val
        return max(maxVal, self.levelForStatefulMemoryAssignmentStep)
    def keepStatefulMemoryLevelsAndDeleteRests(self, regNameList):
        '''
        This fuinction only keeps the register name to level for the registers provided in regnameList. and remove the other mappings. and also return the deleted mappings
        :param regNameList:
        :return:
        '''
        listOfRegNameTobeDeleted= []
        for k in self.selfStatefulMemoryNameToLevelMap.keys():
            if k not in regNameList:
                listOfRegNameTobeDeleted.append(k)
        deletedLevelMap = {}
        for regNameTobeDeleted in listOfRegNameTobeDeleted:
            poppedelemenet = self.selfStatefulMemoryNameToLevelMap.pop(regNameTobeDeleted)
            deletedLevelMap[regNameTobeDeleted] = poppedelemenet
        return deletedLevelMap

    # def getMaxLevelOfSelfStatefulMemoriesAssignedByNeighbours(self):
    #     max = -1
    #     for k in self.neighbourAssignedStatefulMemoryNameToLevelMap.keys():
    #         val = self.neighbourAssignedStatefulMemoryNameToLevelMap.get(k)
    #         if val>max:
    #             max = val
    #     return max
    # def getMaxLevelOfSelfStatefulMemoryAssignedByNeighbours(self, statefulMemoeryName):
    #     if(self.neighbourAssignedStatefulMemoryNameToLevelMap.get(statefulMemoeryName) == None):
    #         return -1
    #     else:
    #         return self.neighbourAssignedStatefulMemoryNameToLevelMap.get(statefulMemoeryName)

    # def getMaxLevelOfSelfStatefulMemoryAssignedBySelf(self, statefulMemoeryName):
    #     if(self.selfStatefulMemoryNameToLevelMap.get(statefulMemoeryName) == None):
    #         return -1
    #     else:
    #         return self.selfStatefulMemoryNameToLevelMap.get(statefulMemoeryName)

    # def getMaxLevelOfAllStatefulMemories(self):
    #     val1 = self.getMaxLevelOfSelfStatefulMemories()
    #
    #     return val1
    def setLevelOfAllStatefulMemories(self,level):
        for k in self.statefulMemoryDependencies.keys():
            self.selfStatefulMemoryNameToLevelMap[k] = level
        self.levelForStatefulMemoryAssignmentStep = level

    def getStatefulMemoeryNamesInConcatenatedString(self):
        returnValue = ""
        for k in self.statefulMemoryDependencies.keys():
            returnValue = returnValue + "_" + k
        return returnValue
    def getStatefulMemoeryNamesAsSet(self):
        returnValue = []
        for k in self.statefulMemoryDependencies.keys():
            returnValue.append(k)
        return set(returnValue)

    def getListOfStatefulMemoriesBeingUsedByMatNodeAsSet(self):
        # if type(self.originalP4node) == Table:
        #     for a in self.actions
        # else:
        #     return set([])
        stafeulMemorySet= set()
        for a in self.actions:
            stafeulMemorySet = stafeulMemorySet.union(set(a.getListOfStatefulMemoriesBeingUsed()))
        return stafeulMemorySet



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
        if(self.matchKeyFields == None) and (self.nodeType == P4ProgramNodeType.TABLE_NODE):
            return  self.originalP4node.getAllMatchFieldsOfRawP4Table()
        elif(self.matchKeyFields == None) and (self.nodeType == P4ProgramNodeType.CONDITIONAL_NODE):
            self.matchKeyFields = []
        return self.matchKeyFields

    def getListOfFieldsModifedAndUsed(self, parsedP4Program):
        listOfFieldBeingModifed = []
        listOfFieldBeingUsed = []
        for a in self.actions:
            filedsModifiedInAction, fieldsdUsedInAction , listOfStatefulMemoryBeingAccessed= a.getListOfFieldsModifedAndUsedByTheAction(parsedP4Program)
            listOfFieldBeingModifed = listOfFieldBeingModifed + filedsModifiedInAction
            listOfFieldBeingUsed = listOfFieldBeingUsed + fieldsdUsedInAction
        listOfFieldBeingModifed = set(listOfFieldBeingModifed)
        listOfFieldBeingModifed = list(listOfFieldBeingModifed)
        listOfFieldBeingUsed = set(listOfFieldBeingUsed)
        listOfFieldBeingUsed = list(listOfFieldBeingUsed)
        return listOfFieldBeingModifed, listOfFieldBeingUsed




class Dependency:

    def __init__(self,dependencyType, src, dst ):
        self.dependencyType = dependencyType
        self.src = src
        self.dst = dst



