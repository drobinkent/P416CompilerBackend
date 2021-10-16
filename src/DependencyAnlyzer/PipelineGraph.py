import json
import logging
from enum import Enum
import sys

from DependencyAnlyzer.DefinitionConstants import P4ProgramNodeType, PipelineID
from DependencyAnlyzer.P4ProgramNode import ExpressionNode, MATNode
from P416JsonParser import Key

sys.path.append("..")
import ConfigurationConstants as confConst



import networkx as nx
logger = logging.getLogger('PipelineGraph')
hdlr = logging.FileHandler(confConst.LOG_FILE_PATH )
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)

class PipelineGraph:
    def __init__(self, pipelineID,pipeline, actions):
        self.pipelineID = pipelineID
        self.dummyStart = None
        self.dummyEnd = None
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
        self.matchActionNodes= {}


    def headeranalyzerForSinglePipeline(self):
        '''
        This function analyze which headers are used in a pipeline. and find what is their total length so that we can split the header fields in 2 different sets
        :param piepelineId:
        :return:
        '''
        #At first analyzig the match action table of the  pipeline
        pipelineObject = self.pipeline
        allHeaderFieldUsedInMatchPartAllMAT = []
        allHeaderFieldUsedInActionsOfAllMAT = []
        for tbl in pipelineObject.tables:
            allHeaderFieldUsedInOneMAT = tbl.getAllMatchFields()
            allHeaderFieldUsedInActionsOfOneMAT = self.getAllFieldsModifedInActionsOfTheTable(tbl.name)
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
        for conditionalObj in pipelineObject.conditionals:
            exprNode = ExpressionNode(parsedP4Node = conditionalObj.expression, name =conditionalObj.name,  parsedP4NodeType = P4ProgramNodeType.CONDITIONAL_NODE, pipelineID=self.pipelineID)
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

    def getActionByName(self, actName):
        for act in self.actions:
            if(act.name == actName):
                return act
        return None

    def preProcessPipelineGraph(self):
        self.preprocessConditionalNodes()
        self.preprocessMATAccessingStatefuleMemmories()

    def preprocessMATAccessingStatefuleMemmories(self):
        # if a node iteslef is one of the table mapped by any one of the reigister then renamme it.  (This is necessary if any node iteslf )
        #         also renam the refernce in the raference to table in pipeline.tables with the super mat
        # if next of any mat or conditional is one of the table mapped by any one of the reigister then renamme the reference to next nodes only.
        #     the rest of the part will be handled through the previous if part
        self.recursivelyPreprocessMATAccessingStatefuleMemmories(self.pipeline.init_table)
        return

    def recursivelyPreprocessMATAccessingStatefuleMemmories(self, nodeName):
        flag = False
        for k in self.registerNameToTableMap:
            tableList = self.registerNameToTableMap.get(k)
            if(nodeName in tableList):
                flag = True
        node = self.getNodeWithActionsForConditionalPreProcessing(nodeName)
        if(flag==True):
            pass
        if(node == None):
            logger.info("No relevant node is found in the pipeline for : " + nodeName)
            return
        else:
            if (len(node.nextNodes)<=0):
                return
            else:
                for nxtNodeName in node.nextNodes:
                    self.preprocessConditionalNodeRecursively(nxtNodeName)  #inside this function call we have add the headerfield for carrying if-else result
        pass

    def getNodeWithActionsForStatefulMemoryBasedPreprocessing(self, name):
        if(name==None):
            logger.info("Name is None in getNodeWithActionsForStatefulMemoryBasedPreprocessing. returning None")
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
                nodeList = self.getNextNodeForP4TEAnalysis(a,self.pipelineID)
                p4teTableNode.nextNodes = p4teTableNode.nextNodes + nodeList
            return p4teTableNode
        elif(conditional != None):
            # print("conditional name is "+name)
            p4teConditionalNode =MATNode(nodeType= P4ProgramNodeType.CONDITIONAL_NODE , name = name, oriiginalP4node = conditional)
            p4teConditionalNode.exprNode = ExpressionNode(parsedP4Node = conditional.expression, name= name,  parsedP4NodeType = P4ProgramNodeType.CONDITIONAL_NODE, pipelineID=self.pipelineID)
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


    def preprocessConditionalNodes(self):
        self.preprocessConditionalNodeRecursively(self.pipeline.init_table)
        return


    def preprocessConditionalNodeRecursively(self, nodeName):
        node = self.getNodeWithActionsForConditionalPreProcessing(nodeName)
        if(node == None):
            logger.info("No relevant node is found in the pipeline for : " + nodeName)
            return
        else:
            if (len(node.nextNodes)<=0):
                return
            else:
                for nxtNodeName in node.nextNodes:
                    self.preprocessConditionalNodeRecursively(nxtNodeName)  #inside this function call we have add the headerfield for carrying if-else result
        pass

    def getNodeWithActionsForConditionalPreProcessing(self, name):
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
                nodeList = self.getNextNodeForP4TEAnalysis(a,self.pipelineID)
                p4teTableNode.nextNodes = p4teTableNode.nextNodes + nodeList
            return p4teTableNode
        elif(conditional != None):
            # print("conditional name is "+name)
            p4teConditionalNode =MATNode(nodeType= P4ProgramNodeType.CONDITIONAL_NODE , name = name, oriiginalP4node = conditional)
            p4teConditionalNode.exprNode = ExpressionNode(parsedP4Node = conditional.expression, name= name,  parsedP4NodeType = P4ProgramNodeType.CONDITIONAL_NODE, pipelineID=self.pipelineID)
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
        for matchTable in self.pipeline.tables:
            if matchTable.name  == nodeName:
                if(self.pipeline.name == PipelineID.INGRESS_PIPELINE.value) and (isArrivingFromConditional == True):
                    # json_object = json.loads(confConst.SPECIAL_KEY_FOR_CARRYING_CODNDITIONAL_RESULT_IN_INGRESS)
                    obj = Key.from_dict(confConst.SPECIAL_KEY_FOR_CARRYING_CODNDITIONAL_RESULT_IN_INGRESS)
                    matchTable.key.append(obj)
                elif (self.pipeline.name == PipelineID.EGRESS_PIPELINE.value)  and (isArrivingFromConditional == True):
                    # json_object = json.loads(confConst.SPECIAL_KEY_FOR_CARRYING_CODNDITIONAL_RESULT_IN_EGRESS)
                    obj = Key.from_dict(confConst.SPECIAL_KEY_FOR_CARRYING_CODNDITIONAL_RESULT_IN_EGRESS)
                    matchTable.key.append(obj)
                nextNodeList.append(nodeName)
        for cond in self.pipeline.conditionals:
            if cond.name  == nodeName:
                nextNodeList.append(nodeName)
        return nextNodeList
