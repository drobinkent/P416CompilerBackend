import logging
from enum import Enum
import sys

from DependencyAnlyzer.DefinitionConstants import P4ProgramNodeType
from DependencyAnlyzer.P4ProgramNode import ExpressionNode

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
        self.matchlessActionNodes = {}
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
