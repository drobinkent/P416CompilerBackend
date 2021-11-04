import json
import logging
from enum import Enum
import sys

from networkx.drawing.nx_agraph import to_agraph

from DependencyAnlyzer.DefinitionConstants import P4ProgramNodeType, PipelineID, DependencyType
from DependencyAnlyzer.P4ProgramNode import ExpressionNode, MATNode, Dependency
from P4ProgramParser.P416JsonParser import Key, Table, GraphColor

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


    def __init__(self, pipelineID,pipeline, actions):
        self.pipelineID = pipelineID
        self.dummyStart = MATNode(nodeType = P4ProgramNodeType.DUMMY_NODE, name = confConst.DUMMY_START_NODE, originalP4node= None)
        self.dummyEnd = MATNode(nodeType = P4ProgramNodeType.DUMMY_NODE, name = confConst.DUMMY_END_NODE, originalP4node=None)
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
        self.preprocessConditionalNodeRecursively(self.pipeline.init_table, confConst.DUMMY_START_NODE)
        self.loadTDG(self.pipeline.init_table, self.dummyStart)

        pass



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
            p4teConditionalNode.matchKey = None
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

    def drawPipeline(self,filePath= "./before-conditional"):
        self.pipeline.resetIsVisitedVariableForGraphDrawing()
        nxGraph = nx.DiGraph()
        alreadyVisitedNodesMap = {}
        self.getNxGraph(self.pipeline.init_table, nxGraph, pred = confConst.DUMMY_START_NODE,indenter = "", alreadyVisitedNodesMap=alreadyVisitedNodesMap)
        print("\n\n\n printing all nodes int he graph ")
        print(nxGraph.nodes())
        A = to_agraph(nxGraph)

        # print(A)
        for node in nxGraph.nodes():
            n=A.get_node(node)
            n.attr['shape']='box'
            n.attr['style']='filled'
            n.attr['fillcolor']='turquoise'
            # n.attr['node_size']=1
        # A.layout(prog="neato", args="-Nshape=circle -Efontsize=20")
        A.layout('dot',args="-Nshape=circle -Efontsize=20")
        A.draw(filePath)
        pass


    def getNxGraph(self, nodeName, nxGraph, pred, indenter = "\t", alreadyVisitedNodesMap={}):
        # if(nodeName!=None):
        #     print("Adding node in graph"+ nodeName)
        flag = False
        if(nodeName!=None):
            nxGraph.add_nodes_from([(nodeName, {"label" : nodeName,"color": "red"})])
        if(nodeName!=None):
            nxGraph.add_edges_from([(pred, nodeName)], label="")
        tbl = self.pipeline.getTblByName(nodeName)
        conditional = self.pipeline.getConditionalByName(nodeName)
        if ( tbl != None):
            if(tbl.is_visited_for_graph_drawing== GraphColor.BLACK):
                return
            if(tbl.is_visited_for_graph_drawing== GraphColor.GREY):
                logger.info("Cycle found in the TDG graph for node "+nodeName+" Exiting")
                print("Cycle found in the TDG graph for node "+nodeName+" Exiting")
                exit(1)
            tbl.is_visited_for_graph_drawing= GraphColor.GREY
            for a in list(tbl.next_tables.values()):
                if(a!=None):
                    self.getNxGraph(a, nxGraph, nodeName,indenter+"\t")
            tbl.is_visited_for_graph_drawing= GraphColor.BLACK
        elif(conditional != None):
            if(conditional.is_visited_for_graph_drawing== GraphColor.BLACK):
                return
            if(conditional.is_visited_for_graph_drawing== GraphColor.GREY):
                logger.info("Cycle found in the TDG graph for node "+nodeName+" Exiting")
                print("Cycle found in the TDG graph for node "+nodeName+" Exiting")
                exit(1)
            next_tables = [conditional.true_next, conditional.false_next]
            conditional.is_visited_for_graph_drawing= GraphColor.GREY
            for a in next_tables:
                if(a!=None):
                    self.getNxGraph(a, nxGraph, nodeName, indenter+"\t")
            conditional.is_visited_for_graph_drawing= GraphColor.BLACK
    #====================================== Functions related to drawing the TDG ENDS Here ==================================================



    #====================================== Functions related to loading the TDG STARTS here ==================================================

    def loadTDG(self, name, predMatNode):
        p4MatNode = self.getMatNodeForTDGProcessing(name,predMatNode)
        if(p4MatNode == None):
            if(name == confConst.DUMMY_END_NODE):
                return self.dummyEnd
            else:
                logger.info("relevant Matnode is not found for  the child of :"+predMatNode.name+" and the name of node to be searched is "+name+". Severer Error. Debug Exiting ")
                print("relevant Matnode is not found for  the child of :"+predMatNode.name+" and the name of node to be searched is "+name+". Severer Error. Debug Exiting ")
                exit(1)
        self.allTDGNode[name] = p4MatNode
        if(p4MatNode.originalP4node.is_visited_for_TDG_processing == GraphColor.BLACK):
            return
        print("Graph node being processed is :"+name)
        if(p4MatNode.originalP4node.is_visited_for_TDG_processing == GraphColor.GREY):
            logger.info("A cycle found in the TDG. The relevant edge is : "+predMatNode.name+"<-- to -->"+p4MatNode.name+". Exiting from the program abruptly without further try")
            print("A cycle found in the TDG. The relevant edge is : "+predMatNode.name+"<-- to -->"+p4MatNode.name+". Exiting from the program abruptly without further try")
            exit(1)
        p4MatNode.originalP4node.is_visited_for_TDG_processing = GraphColor.GREY
        for nxtNodeName in p4MatNode.nextNodes:
            if(nxtNodeName == None):
                self.loadTDG(name = confConst.DUMMY_END_NODE, predMatNode = p4MatNode, nameOfPredOfSubTable= None)
            elif(nxtNodeName != None):
                self.loadTDG(name = nxtNodeName.name, predMatNode = p4MatNode, nameOfPredOfSubTable = None)
        p4MatNode.originalP4node.is_visited_for_TDG_processing = GraphColor.BLACK
        return

    def getMatNodeForTDGProcessing(self, name, predecessorMatNode):
        if(name==None):
            logger.info("Name is None in getNodeWithActionsForTDGProcessing. returning None")
            return None
        tbl = self.pipeline.getTblByName(name)
        conditional = self.pipeline.getConditionalByName(name)
        if(tbl != None) and (type(tbl) != Table):
            # print("Table name is "+name)
            p4TableNode = MATNode(nodeType= P4ProgramNodeType.TABLE_NODE, name = name, originalP4node = tbl )
            p4TableNode.matchKey = tbl.getAllMatchFields()
            p4TableNode.actions = tbl.actions
            # p4teTableNode.actionObjectList = []
            for a in p4TableNode.actions:
                actionObject = self.getActionByName(a)
                p4TableNode.actionObjectList.append(actionObject)
            for a in list(tbl.next_tables.values()):
                nodeList = self.getNextNodeForTDG(a)
                p4TableNode.nextNodes = p4TableNode.nextNodes + nodeList
            p4TableNode.predecessors[predecessorMatNode.name] = predecessorMatNode
            predecessorMatNode.ancestors[p4TableNode.name] = p4TableNode
            p4TableNode.dependencies[predecessorMatNode.name] = self.matToMatDependnecyAnalysis(predecessorMatNode, p4TableNode)
            return p4TableNode
        elif(conditional != None):
            # print("conditional name is "+name)
            p4teConditionalNode =MATNode(nodeType= P4ProgramNodeType.CONDITIONAL_NODE , name = name, originalP4node = conditional)
            # An action has an op and parameters. Whereas a conditional expression has type = expression, op is a conditioanl op and values are left and right.
            # which are the parameters. So currently we are assuming ou r hardware can support a> a+b or a+b > c format expression.
            # so we will use a static methord here which will convert a conditional to predicate then write a field format.
            # but in future there will be a a new preprocessor function that will actually pre process the action primitives and convert to every hardware specific primitive
            p4teConditionalNode.actions = conditional.convertToAction()
            p4teConditionalNode.next_tables = [conditional.true_next, conditional.false_next]
            for a in p4teConditionalNode.next_tables:
                nodeList = self.getNextNodeForTDG(a)
                p4teConditionalNode.nextNodes = p4teConditionalNode.nextNodes + nodeList
            p4teConditionalNode.predecessors[predecessorMatNode.name] = predecessorMatNode
            predecessorMatNode.ancestors[p4teConditionalNode.name] = p4teConditionalNode
            p4teConditionalNode.dependencies[predecessorMatNode.name] = self.matToMatDependnecyAnalysis(predecessorMatNode, p4teConditionalNode)
            return p4teConditionalNode
        else: # This branch only works for the cases where the init_table of a pipeline is a supertable
            logger.info("There is no relevent node found for nodename: "+name+" Debig please. Exiting.")
            print("There is no relevent node found for nodename: "+name+" Debig please. Exiting.")
            exit(1)



    def getNextNodeForTDG(self, nodeName):
        nextNodeList = []
        if(nodeName == confConst.DUMMY_START_NODE):
            return self.dummyStart
        if(nodeName == confConst.DUMMY_END_NODE):
            return self.dummyEnd
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
            return DependencyType.MATCH_DEPENDENCY # highest priority
        elif (common_member(filedsModifiedByMat1Actions, filedsModifiedByMat2Actions)):
            return DependencyType.ACTION_DEPENDENCY
        elif (common_member(mat1MatchKeyList, filedsModifiedByMat2Actions)):
            return DependencyType.REVERSE_MATCH_DEPENDENCY
        elif(matNode1.next_tables.get("__HIT__") != None) and (matNode1.next_tables.get("__HIT__") == matNode2.name) :
            return DependencyType.SUCCESOR_DEPENDENCY
        elif(matNode1.next_tables.get("__MISS__") != None) and (matNode1.next_tables.get("__MISS__") == matNode2.name) :
            return DependencyType.SUCCESOR_DEPENDENCY
        elif(matNode1.nodeType== P4ProgramNodeType.CONDITIONAL_NODE):
            if(matNode1.originalP4node.true_next == matNode2.name) or (matNode1.originalP4node.false_next == matNode2.name):
                return DependencyType.SUCCESOR_DEPENDENCY
        else:
            return DependencyType.DEFAULT_DEPNDENCY

    def matToMatStatefulMemoryDependnecyAnalysis(self, matNode1, matNode2):
        for k in self.registerNameToTableMap:
            tblList = self.registerNameToTableMap.get(k)
            if (matNode1.name in tblList) and (matNode2.name in tblList):
                return True
        return False

    def addStatefulMemoryDependencies(self):
        for name1 in self.allTDGNode.keys():
            for name2 in self.allTDGNode.keys():
                if(name1!= name2):
                    node1 = self.allTDGNode.get(name1)
                    node2 = self.allTDGNode.get(name2)
                    if (self.matToMatStatefulMemoryDependnecyAnalysis(node1,node2) == True):
                        node1.addStatefulMemoryDependency(node2)
                        node2.addStatefulMemoryDependency(node1)
        return















