import copy
import json
import logging
from enum import Enum
import sys
import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import to_agraph

from DependencyAnlyzer.DefinitionConstants import P4ProgramNodeType, PipelineID, DependencyType
from DependencyAnlyzer.P4ProgramNode import ExpressionNode, MATNode, Dependency
from P4ProgramParser.P416JsonParser import Key, Table, GraphColor, Conditional

sys.path.append("..")
import ConfigurationConstants as confConst



import networkx as nx
logger = logging.getLogger('PipelineGraph')
hdlr = logging.FileHandler(confConst.LOG_FILE_PATH )
hdlr.setLevel(logging.INFO)
# formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
formatter = logging.Formatter('%(message)s','%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)

def common_member(a, b):
    a_set = set(a)
    b_set = set(b)

    if (a_set & b_set):
        return(a_set & b_set)
    else:
        return None


class PipelineGraph:


    def __init__(self, pipelineID,pipeline, actions,parsedP4Program):
        self.pipelineID = pipelineID
        self.parsedP4Program = parsedP4Program
        self.dummyStart = MATNode(nodeType = P4ProgramNodeType.DUMMY_NODE, name = confConst.DUMMY_START_NODE, \
                                  originalP4node= Table(confConst.DUMMY_START_NODE, confConst.DUMMY_START_NODE, None, [], None, None, 0, False,
                                                        False, [], [], [], False, False,GraphColor.WHITE, GraphColor.WHITE, [], [], [], []))
        self.dummyEnd = MATNode(nodeType = P4ProgramNodeType.DUMMY_NODE, name = confConst.DUMMY_END_NODE, \
                                 originalP4node= Table(confConst.DUMMY_END_NODE, confConst.DUMMY_END_NODE, None, [], None, None, 0, False,
                                                       False, [], [], [], False, False,GraphColor.WHITE, GraphColor.WHITE, [], [], [], []))

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
        self.superTableNameToSubTableListMap= {}
        self.registerNameToSuperMatNameMap= {}
        self.conditionalNodes = {}
        self.matchActionNodes= {}
        self.swappedTableMapForStatefulMemoryBasedPreprocessing = {}
        self.allTDGNode = {}
        self.allTDGNode[confConst.DUMMY_START_NODE] = self.dummyStart
        self.stageWiseLogicalMatList = {}


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
            if(type(tbl) == Table):
                # print("In header analyzer table name is "+tbl.name)
                allHeaderFieldUsedInOneMAT = tbl.getAllMatchFields()
                allHeaderFieldUsedInActionsOfOneMAT = self.getAllFieldsModifedInActionsOfTheTable(tbl.name)
                if len(allHeaderFieldUsedInOneMAT)>0:
                    for e in allHeaderFieldUsedInOneMAT:
                        allHeaderFieldUsedInMatchPartAllMAT.append(e)
                if len(allHeaderFieldUsedInActionsOfOneMAT)>0:
                    for e in allHeaderFieldUsedInActionsOfOneMAT:
                        allHeaderFieldUsedInActionsOfAllMAT.append(e)
            else:
                print("For node "+tbl.name+" The node type is not table. This can not happen. Exiting. Debug Pleaase ")
                exit(1)

        print("Before removing duplicate member of match fields "+str(len(allHeaderFieldUsedInMatchPartAllMAT)))
        allHeaderFieldUsedInMatchPartAllMAT = set(allHeaderFieldUsedInMatchPartAllMAT) # removing duplicate through set operations. Becuase multiple MAT can use same header fileds.
        print("After removing duplicate member  of match fields "+str(len(allHeaderFieldUsedInMatchPartAllMAT)))
        # print(allHeaderFieldUsedInMatchPartAllMAT)
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

    def traverseTDG(self):
        nodeList = []
        self.traverseTDGRecursivelyBeforeCreatingSuperMat(self.pipeline.init_table, nodeList)
        pass


    def traverseTDGRecursivelyBeforeCreatingSuperMat(self, name, nodeList):
        tbl = self.pipeline.getTblByName(name)
        conditional = self.pipeline.getConditionalByName(name)
        nodeList.append(name)
        if(tbl != None):
            if(tbl.is_visited_for_conditional_preprocessing == True):
                return
            if(len(tbl.next_tables.keys())<=0):
                print(nodeList)
            for tblKey in list(tbl.next_tables.keys()):
                nxtNode = tbl.next_tables.get(tblKey)
                newNodeList = [n for n in nodeList]
                self.traverseTDGRecursivelyBeforeCreatingSuperMat(nxtNode, newNodeList)
            tbl.is_visited_for_conditional_preprocessing = True
            return
        elif(conditional != None):
            next_tables = [conditional.true_next, conditional.false_next]
            if(len(next_tables)<=0):
                print(nodeList)
            for nxtNode in next_tables:
                newNodeList = [n for n in nodeList]
                self.traverseTDGRecursivelyBeforeCreatingSuperMat(nxtNode, newNodeList)
            conditional.is_visited_for_conditional_preprocessing = True
            return

    def preProcessPipelineGraph(self):
        nxGraph = nx.MultiDiGraph()
        alreadyVisitedNodesMap = {}
        self.getTDGGraphBeforeDependencyAnlaysis(self.pipeline.init_table, nxGraph, pred = confConst.DUMMY_START_NODE, indenter ="", alreadyVisitedNodesMap=alreadyVisitedNodesMap)
        self.drawPipeline(nxGraph = nxGraph, filePath="before-conditional-processing"+str(self.pipelineID)+".jpg")
        self.preprocessConditionalNodeRecursively(self.pipeline.init_table, confConst.DUMMY_START_NODE)
        self.loadTDG(self.pipeline.init_table, self.dummyStart)
        self.addStatefulMemoryDependencies()
        # for n in self.allTDGNode.keys():
        #     p4Node = self.allTDGNode.get(n)
        #     print("Node name : "+p4Node.name)
        #     print("Depnedines are following: ")
        #     for dp in p4Node.dependencies.keys():
        #         print("\t"+p4Node.dependencies.get(dp).dst.name)

        graphTobedrawn = nx.MultiDiGraph()
        self.pipeline.resetAllIsVisitedVariableForGraph()
        self.getTDGGraphWithAllDepenedencyAndMatNode(curNode = self.allTDGNode.get(confConst.DUMMY_START_NODE), predNode=None, dependencyBetweenCurAndPred=None, tdgGraph=graphTobedrawn)
        self.drawPipeline(nxGraph = graphTobedrawn, filePath="after-loading-with-all-dependency"+str(self.pipelineID)+".jpg")
        self.pipeline.resetAllIsVisitedVariableForGraph()
        self.assignLevelsToStatefulMemories(curMatNode=self.allTDGNode[confConst.DUMMY_START_NODE], predMatNode=None)
        self.addStatefulMemoryDependencies()
        graphTobedrawn = nx.MultiDiGraph()
        self.pipeline.resetAllIsVisitedVariableForGraph()
        if(self.allTDGNode.get(confConst.DUMMY_START_NODE) != None):
            self.allTDGNode.get(confConst.DUMMY_START_NODE).originalP4node.is_visited_for_graph_drawing = GraphColor.WHITE
        if(self.allTDGNode.get(confConst.DUMMY_END_NODE) != None):
            self.allTDGNode.get(confConst.DUMMY_END_NODE).originalP4node.is_visited_for_graph_drawing = GraphColor.WHITE
        self.getTDGGraphWithAllDepenedencyAndMatNode(curNode = self.allTDGNode.get(confConst.DUMMY_START_NODE), predNode=None, dependencyBetweenCurAndPred=None, tdgGraph=graphTobedrawn, printLevel=True)
        self.drawPipeline(nxGraph = graphTobedrawn, filePath="level-graph"+str(self.pipelineID)+".jpg")
        print("For piepline"+str(self.pipelineID)+" total Graph nodes  after conditional processing "+str(len(nxGraph.nodes())))
        # for n in nxGraph.nodes():
        #     print(n)
        print("For piepline"+str(self.pipelineID)+" total Graph nodes  after TDG processing "+str(len(graphTobedrawn.nodes())))
        # for n in graphTobedrawn.nodes():
        #     if(type(n) == str):
        #         print(n)
        #     else:
        #         print(n.name)
        self.addStatefulMemoryDependencies()
        self.calculateNodeInDegrees()
        self.calculateLevels( self.allTDGNode.get(confConst.DUMMY_START_NODE))
        graphTobedrawn = nx.MultiDiGraph()
        self.pipeline.resetAllIsVisitedVariableForGraph()
        if(self.allTDGNode.get(confConst.DUMMY_START_NODE) != None):
            self.allTDGNode.get(confConst.DUMMY_START_NODE).originalP4node.is_visited_for_graph_drawing = GraphColor.WHITE
        if(self.allTDGNode.get(confConst.DUMMY_END_NODE) != None):
            self.allTDGNode.get(confConst.DUMMY_END_NODE).originalP4node.is_visited_for_graph_drawing = GraphColor.WHITE
        self.getTDGGraphWithAllDepenedencyAndMatNode(curNode = self.allTDGNode.get(confConst.DUMMY_START_NODE), predNode=None, dependencyBetweenCurAndPred=None, tdgGraph=graphTobedrawn, printLevel=True)
        self.drawPipeline(nxGraph = graphTobedrawn, filePath="final-graph"+str(self.pipelineID)+".jpg")
        self.stageWiseLogicalMatList = self.calculateStageWiseMatNodes()
        # self.calculateStageWiseTotalReousrceRequirements(stageWiseMatList)
        pass


    def calculateNodeInDegrees(self):
        for matNodeName1 in self.allTDGNode.keys():
            matNode1 = self.allTDGNode.get(matNodeName1)
            for matNodeName2 in self.allTDGNode.keys():
                matNode2 = self.allTDGNode.get(matNodeName2)
                if(matNode1.dependencies.keys().__contains__(matNode2.name)):
                    matNode2.inDegree = matNode2.inDegree+1
                for sfMem in matNode1.statefulMemoryDependencies.keys():
                    depList = matNode1.statefulMemoryDependencies.get(sfMem)
                    for dep in depList:
                        if dep.name == matNode2.name:
                            matNode2.inDegree = matNode2.inDegree+1
        for matNodeName in self.allTDGNode.keys():
            matNode = self.allTDGNode.get(matNodeName)
            # print("Indegress of node "+matNode.name+" is : "+str(matNode.inDegree))
    #====================================== Functions related to conditional processing STARTS Here ==================================================
    def preprocessConditionalNodeRecursively(self, nodeName, callernode, toPrint= True ):
        node = self.getNodeWithActionsForConditionalPreProcessing(nodeName)
        prevNode = self.getNodeWithActionsForConditionalPreProcessing(callernode)
        if(node == None):
            # logger.info("No relevant node is found in the pipeline for : " + nodeName)
            return
        if(node.originalP4node.is_visited_for_conditional_preprocessing == True):
            return
        else:
            if (len(node.nextNodes)<=0):
                return
            else:
                for nxtNodeName in node.nextNodes:
                    self.preprocessConditionalNodeRecursively(nodeName = nxtNodeName, callernode = nodeName)

                node.originalP4node.is_visited_for_conditional_preprocessing =True
        return


    def getNodeWithActionsForConditionalPreProcessing(self, name):
        if(name==None):
            logger.info("Name is None in getNode. returning None")
            return None
        tbl = self.pipeline.getTblByName(name)
        conditional = self.pipeline.getConditionalByName(name)

        if(tbl != None):
            # print("Table name is "+name)
            p4teTableNode =MATNode(nodeType= P4ProgramNodeType.TABLE_NODE, name = name, originalP4node = tbl )
            p4teTableNode.matchKeyFields = tbl.getAllMatchFields()
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
                if(a!=None):
                    nodeList = self.getNextNodeForconditionalPreprocessing(a, self.pipelineID)
                    p4teTableNode.nextNodes = p4teTableNode.nextNodes + nodeList
            return p4teTableNode
        elif(conditional != None):
            # print("conditional name is "+name)
            p4teConditionalNode =MATNode(nodeType= P4ProgramNodeType.CONDITIONAL_NODE , name = name, originalP4node = conditional)
            p4teConditionalNode.exprNode = ExpressionNode(parsedP4Node = conditional.expression, name= name,  parsedP4NodeType = P4ProgramNodeType.CONDITIONAL_NODE, pipelineID=self.pipelineID)
            #p4teConditionalNode.actions = self actions  # A conditional is itself an action so its actions are itself own
            # store the action used in the conditional
            p4teConditionalNode.matchKeyFields = None
            # p4teConditionalNode.actions =
            p4teConditionalNode.next_tables = [conditional.true_next, conditional.false_next]
            for a in p4teConditionalNode.next_tables:
                if(a!=None):
                    nodeList = self.getNextNodeForconditionalPreprocessing(a, isArrivingFromConditional=True)
                    p4teConditionalNode.nextNodes = p4teConditionalNode.nextNodes + nodeList
            return p4teConditionalNode
        pass


    def getNextNodeForconditionalPreprocessing(self, nodeName, isArrivingFromConditional=False):
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
        # for nameSwappedTableName in self.swappedTableMapForStatefulMemoryBasedPreprocessing.keys():
        #     if(nameSwappedTableName == nodeName):
        #         for matchTable in self.pipeline.tables:
        #             if matchTable.name  == nameSwappedTableName:
        #                 nextNodeList.append(matchTable.name)
        return nextNodeList


    #====================================== Functions related to conditional processing ENDS Here ==================================================


    #====================================== Functions related to drawing the TDG STARTS Here ==================================================

    def drawPipeline(self,nxGraph, filePath= "./before-conditional"):
        self.pipeline.resetIsVisitedVariableForGraphDrawing()

        # print("\n\n\n printing all nodes int he graph ")
        # print(nxGraph.nodes())
        # nxGraph = nx.planar_layout(nxGraph)
        A = to_agraph(nxGraph)

        # print(A)
        for node in nxGraph.nodes():
            n=A.get_node(node)
            # print("GRaph node is "+n)
            n.attr['shape']='box'
            n.attr['style']='filled'
            n.attr['fillcolor']='turquoise'
            # n.attr['node_size']=1
        # A.layout(prog="neato", args="-Nshape=circle -Efontsize=20")
        A.layout('dot',args="-Nshape=circle -Efontsize=20")

        A.draw(filePath)

        # n = A.get_node(confConst.DUMMY_START_NODE)
        # print("My spoeaicla node is "+str(n))
        # nx.draw(nxGraph)
        # plt.savefig(filePath)
        pass


    def getTDGGraphBeforeDependencyAnlaysis(self, nodeName, nxGraph, pred, indenter ="\t", alreadyVisitedNodesMap={}):
        # if(nodeName!=None):
        #     print("Adding node in graph"+ nodeName)
        if(nodeName==None):
            nxGraph.add_nodes_from([(confConst.DUMMY_END_NODE, {"label" : confConst.DUMMY_END_NODE,"color": "red"})])
            nxGraph.add_edge(pred, confConst.DUMMY_END_NODE)
            return

        tbl = self.pipeline.getTblByName(nodeName)
        conditional = self.pipeline.getConditionalByName(nodeName)
        if ( tbl != None):
            if(tbl.is_visited_for_graph_drawing== GraphColor.BLACK):
                # nxGraph.add_edges_from([(pred, nodeName), {"label" : "","color": "red"}])
                nxGraph.add_edge(pred, nodeName)
                return
            if(nodeName!=None):
                # nxGraph.add_nodes_from([(nodeName, {"label" : nodeName,"color": "red"})])
                # nxGraph.add_edges_from([(pred, nodeName), {"label" : "","color": "red"}])
                nxGraph.add_nodes_from([(nodeName)])
                nxGraph.add_edge(pred, nodeName)
            if(tbl.is_visited_for_graph_drawing== GraphColor.GREY):
                logger.info("Cycle found in the TDG graph for node "+nodeName+" Exiting")
                print("Cycle found in the TDG graph for node "+nodeName+" Exiting")
                exit(1)
            tbl.is_visited_for_graph_drawing= GraphColor.GREY
            for a in list(tbl.next_tables.values()):
                # if(a!=None):
                self.getTDGGraphBeforeDependencyAnlaysis(a, nxGraph, nodeName, indenter + "\t")
            tbl.is_visited_for_graph_drawing= GraphColor.BLACK
        elif(conditional != None):
            if(conditional.is_visited_for_graph_drawing== GraphColor.BLACK):
                # nxGraph.add_edges_from([(pred, nodeName), {"label" : "","color": "red"}])
                nxGraph.add_edge(pred, nodeName)
                return
            if(nodeName!=None):
                # nxGraph.add_nodes_from([(nodeName, {"label" : nodeName,"color": "red"})])
                # nxGraph.add_edges_from([(pred, nodeName), {"label" : "","color": "red"}])
                nxGraph.add_node(nodeName)
                nxGraph.add_edge(pred, nodeName)
            if(conditional.is_visited_for_graph_drawing== GraphColor.GREY):
                logger.info("Cycle found in the TDG graph for node "+nodeName+" Exiting")
                print("Cycle found in the TDG graph for node "+nodeName+" Exiting")
                exit(1)
            next_tables = [conditional.true_next, conditional.false_next]
            conditional.is_visited_for_graph_drawing= GraphColor.GREY
            for a in next_tables:
                # if(a!=None):
                self.getTDGGraphBeforeDependencyAnlaysis(a, nxGraph, nodeName, indenter + "\t")
            conditional.is_visited_for_graph_drawing= GraphColor.BLACK
    #====================================== Functions related to drawing the TDG ENDS Here ==================================================



    #====================================== Functions related to loading the TDG STARTS here ==================================================

    def loadTDG(self, name, predMatNode):
        p4MatNode = self.getMatNodeForTDGProcessing(name,predMatNode)
        if(p4MatNode == None):
            if(name == confConst.DUMMY_END_NODE):
                return self.dummyEnd
            else:
                if(name == None):
                    logger.info("Namee for the node is Null. Returning")
                    return
                else:
                    logger.info("relevant Matnode is not found for  the child of :"+predMatNode.name+" and the name of node to be searched is "+name+". Severer Error. Debug Exiting ")
                    print("relevant Matnode is not found for  the child of :"+predMatNode.name+" and the name of node to be searched is "+name+". Severer Error. Debug Exiting ")
                    exit(1)
        self.allTDGNode[name] = p4MatNode
        if(p4MatNode.originalP4node.is_visited_for_TDG_processing == GraphColor.BLACK):
            return
        # print("Graph node being processed is :"+name)
        if(p4MatNode.originalP4node.is_visited_for_TDG_processing == GraphColor.GREY):
            logger.info("A cycle found in the TDG. The relevant edge is : "+predMatNode.name+"<-- to -->"+p4MatNode.name+". Exiting from the program abruptly without further try")
            print("A cycle found in the TDG. The relevant edge is : "+predMatNode.name+"<-- to -->"+p4MatNode.name+". Exiting from the program abruptly without further try")
            exit(1)
        p4MatNode.originalP4node.is_visited_for_TDG_processing = GraphColor.GREY
        for nxtNodeName in p4MatNode.nextNodes:
            if(nxtNodeName == None):
                self.loadTDG(name = confConst.DUMMY_END_NODE, predMatNode = p4MatNode)
            elif(nxtNodeName != None):
                self.loadTDG(name = nxtNodeName.name, predMatNode = p4MatNode)
        p4MatNode.originalP4node.is_visited_for_TDG_processing = GraphColor.BLACK
        return

    def getAllActionsOfTable(self,tblObject):
        actionList = []
        for a in tblObject.actions:
            actionList.append(self.getActionByName(a))
        return actionList

    def getMatNodeForTDGProcessing(self, name, predecessorMatNode):
        if(name==None):
            logger.info("Name is None in getNodeWithActionsForTDGProcessing. returning None")
            return None
        tbl = None
        conditional = None
        if (self.allTDGNode.get(name)!=None):
            # print("rSeving node from alltdg node is "+name)
            p4TableNode = self.allTDGNode.get(name)
            p4TableNode.predecessors[predecessorMatNode.name] = predecessorMatNode
            predecessorMatNode.ancestors[p4TableNode.name] = p4TableNode
            if(self.matToMatDependnecyAnalysis(predecessorMatNode, p4TableNode) != None):
                predecessorMatNode.dependencies[p4TableNode.name] = self.matToMatDependnecyAnalysis(predecessorMatNode, p4TableNode)
            return p4TableNode

        else:
            tbl = self.pipeline.getTblByName(name)
            conditional = self.pipeline.getConditionalByName(name)
        if(tbl != None) and (type(tbl) == Table):
            # print("Table name is "+name)
            p4TableNode = MATNode(nodeType= P4ProgramNodeType.TABLE_NODE, name = name, originalP4node = tbl )
            p4TableNode.matchKeyFields = tbl.getAllMatchFields()
            p4TableNode.actions = self.getAllActionsOfTable(tbl)
            # p4teTableNode.actionObjectList = []
            for a in p4TableNode.actions:
                actionObject = self.getActionByName(a)
                p4TableNode.actionObjectList.append(actionObject)
            for a in list(tbl.next_tables.values()):
                nodeList = self.getNextNodeForTDG(a)
                p4TableNode.nextNodes = p4TableNode.nextNodes + nodeList
            p4TableNode.predecessors[predecessorMatNode.name] = predecessorMatNode
            predecessorMatNode.ancestors[p4TableNode.name] = p4TableNode
            if(self.matToMatDependnecyAnalysis(predecessorMatNode, p4TableNode) != None):
                predecessorMatNode.dependencies[p4TableNode.name] = self.matToMatDependnecyAnalysis(predecessorMatNode, p4TableNode)
                # if(predecessorMatNode.name == "node_11"):
                #     print("found node_11 and depednecy list size is  "+str(len(predecessorMatNode.dependencies.keys())))
            else:
                logger.info("severer error. dependy between "+predecessorMatNode.name +" and "+p4TableNode.name +" is none. it can not be. debug.exiting")
                print("severer error. dependy between "+predecessorMatNode.name +" and "+p4TableNode.name +" is none. it can not be. debug.exiting")
                exit(1)
            return p4TableNode
        elif(conditional != None):
            # print("conditional name is "+name)
            p4teConditionalNode =MATNode(nodeType= P4ProgramNodeType.CONDITIONAL_NODE , name = name, originalP4node = conditional)
            # An action has an op and parameters. Whereas a conditional expression has type = expression, op is a conditioanl op and values are left and right.
            # which are the parameters. So currently we are assuming ou r hardware can support a> a+b or a+b > c format expression.
            # so we will use a static methord here which will convert a conditional to predicate then write a field format.
            # but in future there will be a a new preprocessor function that will actually pre process the action primitives and convert to every hardware specific primitive
            p4teConditionalNode.actions = conditional.convertToAction(self.pipelineID)
            p4teConditionalNode.next_tables = [conditional.true_next, conditional.false_next]
            for a in p4teConditionalNode.next_tables:
                nodeList = self.getNextNodeForTDG(a)
                p4teConditionalNode.nextNodes = p4teConditionalNode.nextNodes + nodeList
            p4teConditionalNode.predecessors[predecessorMatNode.name] = predecessorMatNode
            predecessorMatNode.ancestors[p4teConditionalNode.name] = p4teConditionalNode
            if(self.matToMatDependnecyAnalysis(predecessorMatNode, p4teConditionalNode) != None):
                predecessorMatNode.dependencies[p4teConditionalNode.name] = self.matToMatDependnecyAnalysis(predecessorMatNode, p4teConditionalNode)
            else:
                logger.info("severer error. dependy between "+predecessorMatNode.name +" and "+p4teConditionalNode.name +" is none. it can not be. debug.exiting")
                print("severer error. dependy between "+predecessorMatNode.name +" and "+p4teConditionalNode.name +" is none. it can not be. debug.exiting")
                exit(1)
            return p4teConditionalNode
        else:
            if(name == confConst.DUMMY_END_NODE):
                return self.dummyEnd
            else:
                logger.info("There is no relevent node found for nodename: "+name+" Debig please. Exiting.")
                print("There is no relevent node found for nodename: "+name+" Debig please. Exiting.")
                exit(1)



    def getNextNodeForTDG(self, nodeName):
        nextNodeList = []
        if(nodeName == None):
            nextNodeList.append(self.dummyEnd.originalP4node)
        if(nodeName == confConst.DUMMY_START_NODE):
            nextNodeList.append(self.dummyStart.originalP4node)
        if(nodeName == confConst.DUMMY_END_NODE):
            nextNodeList.append(self.dummyEnd.originalP4node)
        for actionEntry in self.actions:
            if actionEntry.name  == nodeName:
                nextNodeList.append(actionEntry)
        for tbl in self.pipeline.tables:
            if tbl.name  == nodeName:
                if(type(tbl) == Table):
                    nextNodeList.append(tbl)
        for cond in self.pipeline.conditionals:
            if cond.name  == nodeName:
                nextNodeList.append(cond)
        return nextNodeList

    def matToMatDependnecyAnalysis(self, matNode1, matNode2):
        # This function will work for both action nodes (which is actually represented by table node in the json prepresentation) and
        # table nodes (real range, exact, lpm, ternary matches)
        if(matNode1 == None ) or (matNode2 == None):
            logger.info("Cannot calculate depndency between null nodes. EXITING!!!!! Please Debug")
            exit(1)
        if(type(matNode1) != MATNode) or (type(matNode2) != MATNode):
            logger.info("Type of matnode 1 is "+str((type(matNode1) )) + " and type of MAtnode2 is "+str((type(matNode2)))+" They are not same. and can there dependency can not be computed")
            print("Type of matnode 1 is "+str((type(matNode1) )) + " and type of MAtnode2 is "+str((type(matNode2)))+" They are not same. and can there dependency can not be computed")
            exit(1)
        if(type(matNode1) == MATNode) and (matNode1.name == confConst.DUMMY_START_NODE):
            dependencyType = Dependency(dependencyType = DependencyType.DUMMY_DEPENDENCY_FROM_START, src = matNode1, dst = matNode2 )
            return dependencyType
        if(type(matNode2) == MATNode) and (matNode2.name == confConst.DUMMY_END_NODE):
            dependencyType = Dependency(dependencyType = DependencyType.DUMMY_DEPENDENCY_TO_END, src = matNode1, dst = matNode2 )
            return dependencyType
        mat1MatchKeyList = matNode1.getAllMatchFields()
        mat2MatchKeyList = matNode2.getAllMatchFields()
        filedsModifiedByMat1Actions, filedsUsedByMat1Actions = matNode1.getListOfFieldsModifedAndUsed()
        filedsModifiedByMat2Actions, filedsUsedByMat2Actions = matNode2.getListOfFieldsModifedAndUsed()
        if (common_member(filedsModifiedByMat1Actions, mat2MatchKeyList)):
            return Dependency(dependencyType = DependencyType.MATCH_DEPENDENCY, src = matNode1, dst = matNode2 )
        elif (common_member(filedsModifiedByMat1Actions, filedsModifiedByMat2Actions)):
            return Dependency(dependencyType = DependencyType.ACTION_DEPENDENCY, src = matNode1, dst = matNode2 )
        elif (common_member(mat1MatchKeyList, filedsModifiedByMat2Actions)):
            return Dependency(dependencyType = DependencyType.REVERSE_MATCH_DEPENDENCY, src = matNode1, dst = matNode2 )
        if(matNode1.nodeType== P4ProgramNodeType.TABLE_NODE):
            if(matNode1.originalP4node.next_tables.get("__HIT__") != None) and (matNode1.originalP4node.next_tables.get("__HIT__") == matNode2.name) :
                return Dependency(dependencyType = DependencyType.SUCCESOR_DEPENDENCY, src = matNode1, dst = matNode2 )
            elif(matNode1.originalP4node.next_tables.get("__MISS__") != None) and (matNode1.originalP4node.next_tables.get("__MISS__") == matNode2.name) :
                return Dependency(dependencyType = DependencyType.SUCCESOR_DEPENDENCY, src = matNode1, dst = matNode2 )
            else:
                return Dependency(dependencyType = DependencyType.NO_DEPNDENCY, src = matNode1, dst = matNode2 )
        elif(matNode1.nodeType== P4ProgramNodeType.CONDITIONAL_NODE):
            if(matNode1.originalP4node.true_next == matNode2.name) or (matNode1.originalP4node.false_next == matNode2.name):
                return Dependency(dependencyType = DependencyType.SUCCESOR_DEPENDENCY, src = matNode1, dst = matNode2 )
            else:
                return Dependency(dependencyType = DependencyType.NO_DEPNDENCY, src = matNode1, dst = matNode2 )
        else:
            return Dependency(dependencyType = DependencyType.NO_DEPNDENCY, src = matNode1, dst = matNode2 )

    def matToMatStatefulMemoryDependnecyAnalysis(self, matNode1, matNode2):

        for k in self.registerNameToTableMap:
            tblList = self.registerNameToTableMap.get(k)
            if (matNode1.name in tblList) and (matNode2.name in tblList):
                # print("Stateful memory dependency between "+matNode1.name +" and "+matNode2.name +" is "+str(k))
                return k
        # print("Stateful memory dependency between "+matNode1.name +" and "+matNode2.name +" is None")
        return None

    def addStatefulMemoryDependencies(self):
        for name1 in self.allTDGNode.keys():
            node1 = self.allTDGNode.get(name1)
            node1.statefulMemoryDependencies.clear()
        for name1 in self.allTDGNode.keys():
            for name2 in self.allTDGNode.keys():
                if(name1!= name2):
                    node1 = self.allTDGNode.get(name1)
                    node2 = self.allTDGNode.get(name2)
                    commonStatefulMemoery = self.matToMatStatefulMemoryDependnecyAnalysis(node1,node2)
                    if (commonStatefulMemoery != None):
                        node1.addStatefulMemoryDependency(commonStatefulMemoery,node2)
                        node2.addStatefulMemoryDependency(commonStatefulMemoery, node1)
                        # print("Stateful memory dependency added from -- "+node1.name + " to "+node2.name)
        return
    #====================================== Functions related to loading the TDG ENDS here ==================================================

    #====================================== Functions related to drawing the TDG STARTS here ==================================================
    def getTDGGraphWithAllDepenedencyAndMatNode(self, curNode, predNode, dependencyBetweenCurAndPred, tdgGraph, arrivedFromStatefulMemoryDependency = False, printLevel=False):
        if(curNode == None):
            return
        # print("Current node name is :"+curNode.name)
        #
        # print("Node name : "+curNode.name)
        # print("Depnedines are following: ")
        # for dp in curNode.dependencies.keys():
        #     print("\t"+curNode.dependencies.get(dp).dst.name)
        if(curNode.originalP4node.is_visited_for_graph_drawing== GraphColor.WHITE):
            # val = tdgGraph.add_node((curNode, {"label" : curNode.name,"color": "red"}))

            val = tdgGraph.add_node(curNode)
            if(printLevel == True):
                tdgGraph.nodes[curNode]["label"] = curNode.name+" Level "+str(curNode.getMaxLevelOfAllStatefulMemories()) + curNode.getStatefulMemoeryNamesInConcatenatedString()
            else:
                tdgGraph.nodes[curNode]["label"] = curNode.name
            # val = tdgGraph.add_nodes_from([(curNode)])
            # print("Added node ")
        if(predNode!=None):
            # tdgGraph.add_edges_from([(predNode, curNode)], label=str(dependencyBetweenCurAndPred))
            if( tdgGraph.has_edge(predNode, curNode)):
                logger.info("duplicate edge exists between "+predNode.name +" and "+curNode.name)
                logger.info("Depnedines of predNode are following: ")
                logger.info("Depnedines of predNode are following: ")
                for dp in predNode.dependencies.keys():
                    logger.info("\t"+str(predNode.dependencies.get(dp).dst.name))
                pass
            else:
                if(dependencyBetweenCurAndPred == DependencyType.STAEFUL_MEMORY_DEPENDENCY):
                    # tdgGraph.add_edge(predNode, curNode, label=str(dependencyBetweenCurAndPred), style = 'dashed', width = .9)
                    tdgGraph.add_edge(predNode, curNode, style = 'dashed', width = 5, color  = 'red')
                else:
                    tdgGraph.add_edge(predNode, curNode, style = 'solid', width = .9, color  = 'black')

            # print("Edge added between : "+predNode.name+" and "+curNode.name)
        if(arrivedFromStatefulMemoryDependency == True):
            if(curNode.originalP4node.is_visited_for_graph_drawing != GraphColor.WHITE):
                return
        else:
            if(curNode.originalP4node.is_visited_for_graph_drawing== GraphColor.BLACK):
                return
        curNode.originalP4node.is_visited_for_graph_drawing= GraphColor.GREY
        # if(curNode.name == "node_11"):
        #     print("Found node_11 in graph load . depndency size is "+str(len(curNode.dependencies.keys())))
        for depndentNodeName in curNode.dependencies.keys():
            dpndncy= curNode.dependencies.get(depndentNodeName)
            if(dpndncy != None ):
                self.getTDGGraphWithAllDepenedencyAndMatNode(curNode = dpndncy.dst, predNode = curNode, dependencyBetweenCurAndPred=dpndncy.dependencyType,tdgGraph = tdgGraph, printLevel=printLevel)
            else:
                print("Dependency is None in dependency map. severe error.exiting. Please DEBUG!!!")
                exit(1)
        if(printLevel != True):
            for sfMemName in curNode.statefulMemoryDependencies.keys():
                sfDepList = curNode.statefulMemoryDependencies.get(sfMemName)
                for neighbourNode in sfDepList:
                    self.getTDGGraphWithAllDepenedencyAndMatNode(curNode = neighbourNode, predNode = curNode, \
                                                             dependencyBetweenCurAndPred=DependencyType.STAEFUL_MEMORY_DEPENDENCY,tdgGraph = tdgGraph, arrivedFromStatefulMemoryDependency = True, printLevel=printLevel)
            # neighbourNode.is_visited_for_graph_drawing= GraphColor.GREY
        curNode.originalP4node.is_visited_for_graph_drawing= GraphColor.BLACK
    #====================================== Functions related to drawing the TDG ENDS here ==================================================

    #====================================== Functions related to Stateful Memory related node processing ==================================================

    def assignLevelsToStatefulMemories(self, curMatNode, predMatNode):
        if(curMatNode == None):
            logger.info("Severe error. Mat node can not be None in assignLevelsToStatefulMemories. Debug. exiting. ")
            print("Severe error. Mat node can not be None in assignLevelsToStatefulMemories. Debug. exiting. ")
            exit(1)
        # print("CurMAtnode name is "+curMatNode.name)
        if curMatNode.name == confConst.DUMMY_END_NODE:
            return -1

        if(curMatNode.originalP4node.is_visited_for_TDG_processing == GraphColor.BLACK):
            return curMatNode.getMaxLevelOfAllStatefulMemories()

        curMatNode.originalP4node.is_visited_for_TDG_processing = GraphColor.GREY
        childLevelList=[]
        for depKey in curMatNode.dependencies.keys():
            dep = curMatNode.dependencies.get(depKey)
            nxtMatNode = dep.dst
            levelOfChild = self.assignLevelsToStatefulMemories(nxtMatNode, curMatNode)
            childLevelList.append(levelOfChild)
        childLevelList.sort()
        maxLevel = -1
        if(len(childLevelList)>0):
            maxLevel = childLevelList[len(childLevelList)-1] +1
        else:
            maxLevel = maxLevel + 1
        maxLevel = max(maxLevel, curMatNode.getMaxLevelOfAllStatefulMemories())
        curMatNode.setLevelOfAllStatefulMemories(maxLevel)
        sfMemNameToMaxLevelMap = {}

        # now the main issue is we are modifying the dictionalry inside the oterationl how to avoid this???
        sfMemNameList =[]
        for k in curMatNode.statefulMemoryDependencies.keys():
            sfMemNameList.append(k)

        # for sfMemName in curMatNode.statefulMemoryDependencies.keys():
        for sfMemName in sfMemNameList:
            sfMemDepList = curMatNode.statefulMemoryDependencies.get(sfMemName)
            if(sfMemDepList == None):
                continue
            else:
                for sfMemDep in sfMemDepList:
                    if (sfMemDep.getMaxLevelOfAllStatefulMemories() <= -1): #This is special case. This indicates the sfMemDep is no explored ever before. This is first time some one isassginign level to it. So no need to break it
                        sfMemDep.setLevelOfAllStatefulMemories( maxLevel)
                    elif (sfMemDep.getMaxLevelOfAllStatefulMemories() < maxLevel): # Need to check whether the sfmem's curNode level contradicts with exisintgf levels of sfMemDep.
                        # Then divide the sfMemdep
                        # Here all stateful memories used by this mat is of same level. Now we only need to take out all those primitives used by
                        #the sfMemdep which are also used by curMAtNode. and dvidde the node.
                        #if both node have same set up stateful mem then we do not need to bofrcate. WE just need to update the level. Else bifurcate the node
                        if(len(sfMemDep.getStatefulMemoeryNamesAsSet().difference(curMatNode.getStatefulMemoeryNamesAsSet())) >0):
                            oldMatNode, newMatNode = self.biFurcateNodes(sfMemDep, curMatNode)
                            oldMatNode.setLevelForStatefulMemeoryBySelf( sfMemName,maxLevel)
                        else:
                            curMatNode.setLevelForStatefulMemeoryBySelf( sfMemName,maxLevel)
                            sfMemDep.setLevelForStatefulMemeoryBySelf( sfMemName,maxLevel)

                        #Here we have to set for which stateful memory we are setting the level

                        # print("Temp")
                    elif (sfMemDep.getMaxLevelOfAllStatefulMemories() == maxLevel):
                        logger.info("Nothing to do. ")
                    else:
                        logger.info("This case never happen. Because If some other node has assigned a higher level for the stateful memory it is already updated to "
                                    "other tabels that used the stateful memory. DEBUG> EXIT")
                        print("This case never happen. Because If some other node has assigned a higher level for the stateful memory it is already updated to "
                              "other tabels that used the stateful memory. DEBUG> EXIT")
                        exit(1)


        curMatNode.originalP4node.is_visited_for_TDG_processing = GraphColor.BLACK

        return maxLevel


    def biFurcateNodes(self, matNodeTobeBifurcated, baseMatNode):
        statefulMemoryListOfBaseNode = list(baseMatNode.statefulMemoryDependencies.keys())
        # for regName in statefulMemoryListOfBaseNode:
        #     print(regName)
        newMatNode = matNodeTobeBifurcated.bifurcateNodeBasedOnStatefulMemeory(statefulMemoryListOfBaseNode,
                newMatPrefix=confConst.BIFURCATED_MAT_NAME_PREFIX, pipelineGraph= self, pipelineID = self.pipelineID, parsedP4Program=self.parsedP4Program)
        self.addStatefulMemoryDependencies()
        return (matNodeTobeBifurcated, newMatNode)


    def calculateLevels(self, curMatNode):
        if(curMatNode == None):
            logger.info("Severe error. Mat node can not be None in calculateLevels. Debug. exiting. ")
            print("Severe error. Mat node can not be None in calculateLevels. Debug. exiting. ")
            exit(1)
        # print("CurMAtnode name is "+curMatNode.name)
        if curMatNode.name == confConst.DUMMY_END_NODE:
            return -1
        if(curMatNode.name != confConst.DUMMY_START_NODE) and (curMatNode.inDegree <=0):
            return curMatNode.getMaxLevelOfAllStatefulMemories()
        curMatNode.inDegree = curMatNode.inDegree -1


        childLevelList=[]
        for depKey in curMatNode.dependencies.keys():
            dep = curMatNode.dependencies.get(depKey)
            nxtMatNode = dep.dst
            levelOfChild = self.calculateLevels(nxtMatNode) + 1
            childLevelList.append(levelOfChild)

        for sfMemName in curMatNode.statefulMemoryDependencies.keys():
            sfMemDepList = curMatNode.statefulMemoryDependencies.get(sfMemName)
            if(sfMemDepList == None):
                continue
            else:
                for sfMemDep in sfMemDepList:
                    levelOfChild = self.calculateLevels(sfMemDep)
                    childLevelList.append(levelOfChild)
        childLevelList.sort()
        maxLevel = -1
        if(len(childLevelList)>0):
            maxLevel = childLevelList[len(childLevelList)-1]

        curMatNode.setLevelOfAllStatefulMemories(maxLevel)

        return maxLevel

    def calculateStageWiseMatNodes(self):
        levelWiseMatList = {}
        for nodeName in self.allTDGNode.keys():
            matNode = self.allTDGNode.get(nodeName)
            level = matNode.getMaxLevelOfAllStatefulMemories()
            if(levelWiseMatList.get(level) == None):
                levelWiseMatList[level] = []
            levelMatList = levelWiseMatList.get(level)
            levelMatList.append(matNode)
        return levelWiseMatList

    def calculateStageWiseTotalReousrceRequirements(self, stageWiseMatMap):
        # TODO This function should not be here. IT should be in the hardware class iteself. Because resources are not part of the parsedP3program. They are part of
        # the hardware itself. So we should movie it to there.
        perStageHwRequirementsForThePipeline = {}
        for k in stageWiseMatMap.keys():
            print("===============================================================================================================================")
            print("Stage:------------------"+str(k))
            if(k==-1):
                print("This is a dummy stage to handle a dummy node in the TDG. Not really mapped to the hardware. So please skip it. ")
            stageMatList = stageWiseMatMap.get(k)
            totalnumberofFieldsBeingModified = 0
            headerBitWidthOfFieldsBeingModified = 0
            totalNumberOfFieldsUsedAsParameter = 0
            totalBitWidthOfFieldsUsedAsParameter = 0
            totalBitWidthOfTheAction=0
            maxBitWidthOfAction =0
            matKeyBitWidth = 0
            matKeyLength = 0
            for m in stageMatList:
                listOfFieldBeingModifedInThisStage = []
                listOfFieldBeingUsedAsParameterInThisStage = []
                print("MAT node: "+m.name)
                print("Match Keys are: ")
                actionIndex = 0
                for f in m.originalP4node.key:
                    matKeyBitWidth =  matKeyBitWidth + self.parsedP4Program.getHeaderBitCount(f.getHeaderName())
                    print("\t\t *) "+str(f))
                    matKeyLength = matKeyLength + len(m.originalP4node.key)
                print("Actions are: ")
                for a in m.actions:
                    actionIndex= actionIndex+1
                    listOfFieldBeingModifed, listOfFieldBeingUsed = a.getListOfFieldsModifedAndUsed()
                    listOfFieldBeingModifedInThisStage= listOfFieldBeingModifedInThisStage + listOfFieldBeingModifed
                    listOfFieldBeingUsedAsParameterInThisStage = listOfFieldBeingUsedAsParameterInThisStage + listOfFieldBeingUsed
                    print("\t "+str(actionIndex)+" Action Nanme: "+a.name)
                    print("\t Primitives used in action are: ")
                    for prim in a.primitives:
                        print("\t\t *) "+str(prim.source_info))
                    for f in listOfFieldBeingModifed:
                        totalnumberofFieldsBeingModified  = totalnumberofFieldsBeingModified + 1
                        # print("Header name is "+f)
                        hdrBitCount = self.parsedP4Program.getHeaderBitCount(f)
                        totalBitWidthOfTheAction = totalBitWidthOfTheAction + hdrBitCount
                        headerBitWidthOfFieldsBeingModified = headerBitWidthOfFieldsBeingModified + hdrBitCount
                    for f in listOfFieldBeingUsed:
                        # print("Header name is "+f)
                        totalNumberOfFieldsUsedAsParameter = totalNumberOfFieldsUsedAsParameter + 1
                        hdrBitCount = self.parsedP4Program.getHeaderBitCount(f)
                        totalBitWidthOfFieldsUsedAsParameter = totalBitWidthOfFieldsUsedAsParameter + hdrBitCount
                        totalBitWidthOfTheAction = totalBitWidthOfTheAction + hdrBitCount
                    if(totalBitWidthOfTheAction > maxBitWidthOfAction):
                        maxBitWidthOfAction = totalBitWidthOfTheAction
            perStageHwRequirementsForThePipeline[k] = (totalnumberofFieldsBeingModified,headerBitWidthOfFieldsBeingModified, totalNumberOfFieldsUsedAsParameter,totalBitWidthOfFieldsUsedAsParameter, listOfFieldBeingModifedInThisStage, listOfFieldBeingUsedAsParameterInThisStage,maxBitWidthOfAction, matKeyLength, matKeyBitWidth)



