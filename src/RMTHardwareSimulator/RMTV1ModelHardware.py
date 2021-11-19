

from ortools.linear_solver import pywraplp

from DependencyAnlyzer.DefinitionConstants import PipelineID
from P416JsonParser import MatchType
from RMTHardwareSimulator.RMTV1HardwareConfigurationParser import RMTV1HardwareConfiguration
from RMTHardwareSimulator.RMTV1InstrctionSetParser import RMTV1InstrctionSet
from RMTHardwareSimulator.StageWiseResources import StageWiseResource
from utils import JsonParserUtil

import logging
import ConfigurationConstants as confConst
logger = logging.getLogger('PipelineGraph')
hdlr = logging.FileHandler(confConst.LOG_FILE_PATH )
hdlr.setLevel(logging.INFO)
# formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
formatter = logging.Formatter('%(message)s','%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)

class RMTV1ModelHardware:

    def __init__(self, name, instructionSetConfigurationJsonFile, hardwareSpecConfigurationJsonFile):
        self.name = name
        self.instructionSetConfigurationRawJsonObjects = RMTV1InstrctionSet.from_dict(JsonParserUtil.loadRowJsonAsDictFromFile(instructionSetConfigurationJsonFile))
        self.hardwareSpecRawJsonObjects = RMTV1HardwareConfiguration.from_dict(JsonParserUtil.loadRowJsonAsDictFromFile(hardwareSpecConfigurationJsonFile))
        self.pakcetHeaderVectorFieldSizeVsCountMap = {}
        self.totalStages = -1
        self.stageWiseResources= {}
        self.nameToAluInstructionMap={}
        self.nameToExternInstructionMap={}

        self.initResourcesFromRawJsonConfigurations()
        print("Loading device configuration for " + self.name+ " completed" )

    def initResourcesFromRawJsonConfigurations(self):
        self.totalStages = self.hardwareSpecRawJsonObjects.total_stages

        for rawPhvSpecsList in self.hardwareSpecRawJsonObjects.header_vector_specs:
            self.pakcetHeaderVectorFieldSizeVsCountMap[rawPhvSpecsList.bit_width] = rawPhvSpecsList.count
        print(self.hardwareSpecRawJsonObjects)
        self.loadInstructionSet()
        self.loadStageWiseResource()
        # for i in range(0, self.totalStages):
        #     self.stageWiseResources[i] = self.loadStageResource(i)

    def loadInstructionSet(self):
        print(self.instructionSetConfigurationRawJsonObjects)

        for instruction in self.instructionSetConfigurationRawJsonObjects.alu_instructions:
            self.nameToAluInstructionMap[instruction.name] = instruction

        for instruction in self.instructionSetConfigurationRawJsonObjects.extern_instructions:
            self.nameToExternInstructionMap[instruction.name] = instruction

    def loadStageWiseResource(self):
        print("Loading stage wise reousrces")
        for stageResourceDescription in self.hardwareSpecRawJsonObjects.stage_description:
            indexStrings  = stageResourceDescription.index.strip().split("-")
            print(indexStrings)
            if(len(indexStrings) <2):
                logger.info("The stage index in the stage wise reosurce description must be in the format \"start_index-\"end_index")
                print("The stage index in the stage wise reosurce description must be in the format \"start_index-\"end_index")
                exit(1)
            stageIndexStart = int(indexStrings[0])
            stageIndexEnd = int(indexStrings[1])
            for stageIndex in range(stageIndexStart, stageIndexEnd):
                self.stageWiseResources[stageIndex] = self.loadSingleStageResource(stageIndex, stageResourceDescription)
                # print(self.stageWiseResources[stageIndex])

        pass

    def loadSingleStageResource(self, stageIndex, stageResourceDescription):
        # print("Loaidng  Reourses for stage "+str(stageIndex))
        stageResource = StageWiseResource(stageIndex,stageResourceDescription, self)
        return stageResource

    def getPakcetHeaderVectorFieldSizeVsCountMap(self, p4ProgramHeaderFieldSpecs):
        return self.pakcetHeaderVectorFieldSizeVsCountMap

    def createDataModelForHeaderMapping(self, p4ProgramHeaderFieldSpecs): # Here we are doing a reverse multile knapsack. we want to pack the
        data = {}
        weights = []
        values = []
        for k in self.pakcetHeaderVectorFieldSizeVsCountMap:
            headerWidth = k
            count = self.pakcetHeaderVectorFieldSizeVsCountMap.get(k)
            for i in range(0,count):
                weights.append(headerWidth)
                values.append(headerWidth)
        data['weights'] = weights
        data['values'] = values
        data['items'] = list(range(len(weights)))
        data['num_items'] = len(weights)

        bin_capacities = []  # these are filled with the programs header fields specs
        for k in p4ProgramHeaderFieldSpecs:
            headerWidth = k
            count = p4ProgramHeaderFieldSpecs.get(k)
            for i in range(0,count):
                bin_capacities.append(headerWidth)
        num_bins = len(bin_capacities)
        data['bins'] = list(range(num_bins))
        data['bin_capacities'] = bin_capacities
        print("Data model is "+str(data))
        return data

    def convertP4PRogramHeaderFieldSizetoPHVFieldSize(self,p4ProgramHeaderFieldSpecs):
        # This function in ununsed at this moment
        # In the buildHeaderVector function we converted the header fields of the p4 orogram to multiple pf 8 bits. so this functions is not necessary.
        phvFieldsSizes = list(self.pakcetHeaderVectorFieldSizeVsCountMap.keys())
        phvFieldsSizes.sort()
        p4ProgramHeaderFieldSpecsConvertedToPHVSpecs = {}
        p4ProgramHeaderFieldSpecsbitWidthInSortedOrder = list(p4ProgramHeaderFieldSpecs.keys())
        p4ProgramHeaderFieldSpecsbitWidthInSortedOrder.sort()
        for bitwidth in p4ProgramHeaderFieldSpecsbitWidthInSortedOrder:
            count = p4ProgramHeaderFieldSpecs.get(bitwidth)
            p4ProgramFieldBitWidth = bitwidth
            phvFieldSizeForP4Programfield = 0
            while(p4ProgramFieldBitWidth >0):
                for phvFieldSize in phvFieldsSizes:
                    p4ProgramFieldBitWidth = p4ProgramFieldBitWidth - phvFieldSize
                    phvFieldSizeForP4Programfield = phvFieldSizeForP4Programfield +  phvFieldSize
                    if (p4ProgramFieldBitWidth <=0):
                        break
            if(p4ProgramHeaderFieldSpecsConvertedToPHVSpecs.get(phvFieldSizeForP4Programfield) == None):
                p4ProgramHeaderFieldSpecsConvertedToPHVSpecs[phvFieldSizeForP4Programfield] = count
            else:
                oldCount = p4ProgramHeaderFieldSpecsConvertedToPHVSpecs.get(phvFieldSizeForP4Programfield)
                p4ProgramHeaderFieldSpecsConvertedToPHVSpecs[phvFieldSizeForP4Programfield] = count+oldCount
        return p4ProgramHeaderFieldSpecsConvertedToPHVSpecs

    def mapHeaderFields(self, p4ProgramHeaderFieldSpecs):
        #TODO at first convert the p4 programs header fields size
        # p4ProgramHeaderFieldSpecs= self.convertP4PRogramHeaderFieldSizetoPHVFieldSize(p4ProgramHeaderFieldSpecs)
        # print("The converted header specs of the givne P4 program is ",p4ProgramHeaderFieldSpecs)
        data = self.createDataModelForHeaderMapping(p4ProgramHeaderFieldSpecs)
        # Create the mip solver with the SCIP backend.
        solver = pywraplp.Solver.CreateSolver('BOP_INTEGER_PROGRAMMING')
        # Variables
        # x[i, j] = 1 if item i is packed in bin j.
        x = {}
        for i in data['items']:
            for j in data['bins']:
                x[(i, j)] = solver.IntVar(0, 1, 'x_%i_%i' % (i, j))

        # Constraints
        # Each item can be in at most one bin.
        for i in data['items']:
            solver.Add(sum(x[i, j] for j in data['bins']) <= 1)
        # The amount packed in each bin cannot exceed its capacity.
        for j in data['bins']:
            solver.Add(
                sum(x[(i, j)] * data['weights'][i]
                    for i in data['items']) <= data['bin_capacities'][j])

        # Objective
        objective = solver.Objective()

        for i in data['items']:
            for j in data['bins']:
                objective.SetCoefficient(x[(i, j)], data['values'][i])
        objective.SetMaximization()

        status = solver.Solve()
        totalHeaderWidthRequiredByP4Program = 0
        for k in p4ProgramHeaderFieldSpecs:
            headerWidth = k
            count = p4ProgramHeaderFieldSpecs.get(k)
            totalHeaderWidthRequiredByP4Program = totalHeaderWidthRequiredByP4Program + headerWidth*count

        mappedacketHeaderVector = {}
        if status == pywraplp.Solver.OPTIMAL:
            print('Total packed value:', objective.Value())
            total_weight = 0
            for j in data['bins']:
                bin_weight = 0
                bin_value = 0
                # print('Bin ', j, '\n')
                binFiller = {}
                for i in data['items']:
                    if x[i, j].solution_value() > 0:
                        # print('Item', i, '- weight:', data['weights'][i], ' value:',
                        #       data['values'][i])
                        bin_weight += data['weights'][i]
                        bin_value += data['values'][i]

                        if mappedacketHeaderVector.get(data['bin_capacities'][j]) == None:
                            mappedacketHeaderVector[data['bin_capacities'][j]] = [data['weights'][i]]
                        else:
                            mappedacketHeaderVector.get(data['bin_capacities'][j]).append(data['weights'][i])
                            # mappedacketHeaderVector[data['bin_capacities'][j]]  =
                # print('Packed bin weight:', bin_weight)
                # print('Packed bin value:', bin_value)
                # print()

                total_weight += bin_weight
            print('Total packed weight:', total_weight)
            if(total_weight != totalHeaderWidthRequiredByP4Program):
                print("The optimized header mapping find process is able to map only: "+str(total_weight)+" bits in the packet header vector of the hardware. whereas the program requires "+str(totalHeaderWidthRequiredByP4Program)+" bits. Hence it is failed. ")
                print("Stopping further execution and exiting")
                exit(1)
            else:
                print("The program's header fields can be mapped to the RMT hardware using following mappine")
                print("For each X-bit wide header field this output lists all the hardwared header fields used. So assume in a P4 program you need 2 32 bit field. If it shows 8 x8 bit wide header fields. that means to fill"
                      "the 2x 32 bit header fields of the program we can use 8x8 bit wide header fields available in the hardware")
                print(str(mappedacketHeaderVector))
                return mappedacketHeaderVector
        else:
            print('The problem does not have an optimal solution.')
            pass


    #================================================= The menthods for mebedding starts here

    def sanityCheckingOfTheLogicalMats(self,logicalStageNumbersAsList,pipelineGraph):
        #The first element in this list will be the logical stage number for the dummy start node.
        # And the last number will be the logical stage number for the dummy end node. The logical stage number  must should be -1
        if(len(pipelineGraph.levelWiseLogicalMatList.get(logicalStageNumbersAsList[0]))>1):
            logger.info("The largest logical stage should only contain the dummy Start node. hence only one node can exist in this stage. But we have more than one MAT node in ths list.So there are some problem. Please DEBUG> Exiting")
            print("The largest logical stage should only contain the dummy Start node. hence only one node can exist in this stage. But we have more than one MAT node in ths list.So there are some problem. Please DEBUG> Exiting")
            (1)
        if(len(pipelineGraph.levelWiseLogicalMatList.get(logicalStageNumbersAsList[len(logicalStageNumbersAsList) - 1]))>1):
            logger.info("The smallest logical stage should only contain the dummy END node. hence only one node can exist in this stage. But we have more than one MAT node in ths list.So there are some problem. Please DEBUG> Exiting")
            print("The smallest logical stage should only contain the dummy END node. hence only one node can exist in this stage. But we have more than one MAT node in ths list.So there are some problem. Please DEBUG> Exiting")
            (1)
        if(len(logicalStageNumbersAsList) == 1):
            print("there is only one level required for the nodes in piepieline : " + str(pipelineGraph.pipelineID) + " The name of the node is " + pipelineGraph.levelWiseLogicalMatList.get(logicalStageNumbersAsList[len(logicalStageNumbersAsList) - 1])[0].name)
            print("The pipeline have no element to embedd. So returning.")
            return
        if(pipelineGraph.levelWiseLogicalMatList.get(logicalStageNumbersAsList[len(logicalStageNumbersAsList) - 1])[0].name != confConst.DUMMY_END_NODE):
            print("The MAT node: " + pipelineGraph.levelWiseLogicalMatList.get(logicalStageNumbersAsList[len(logicalStageNumbersAsList) - 1])[0].name + " with smallest logical stage number :" + str(logicalStageNumbersAsList[len(logicalStageNumbersAsList) - 1]) + " must have to be DUMMY End node. Debug please Exiting")
            exit(1)
        if(pipelineGraph.levelWiseLogicalMatList.get(logicalStageNumbersAsList[0])[0].name != confConst.DUMMY_START_NODE):
            print("The MAT node: " + pipelineGraph.levelWiseLogicalMatList.get(logicalStageNumbersAsList[0])[0].name + " with highest logical stage number :" + str(logicalStageNumbersAsList[0]) + " must have to be DUMMY End node. Debug please Exiting")
        return

    def embedP4ProgramAccordingToSingleMatrix(self, p4ProgramGraph,pipelineID,hardware):
        print("Starting embedding the P4 Program graph on to the hardware")
        pipelineGraph = p4ProgramGraph.pipelineIdToPipelineGraphMap.get(pipelineID)
        logicalStageNumbersAsList = list(pipelineGraph.levelWiseLogicalMatList.keys())
        logicalStageNumbersAsList.sort(reverse=True) # We are sorting the logical stage numbers in descending order. Because we have calculated the levels in reverse order due to use of DFS
        self.sanityCheckingOfTheLogicalMats(logicalStageNumbersAsList, pipelineGraph)
        startingPhyicalStage = min(self.stageWiseResources.keys())

        #TODO: make a check here to understand how many stages does this program need. if it needs more than available stages then we can halt earlier.
        for logicalStageIndex in logicalStageNumbersAsList:
            if(pipelineGraph.levelWiseLogicalMatList.get(logicalStageIndex)[0].name == confConst.DUMMY_END_NODE) \
                or (pipelineGraph.levelWiseLogicalMatList.get(logicalStageIndex)[0].name == confConst.DUMMY_START_NODE):
                continue
            else:
                logicalMatList = pipelineGraph.levelWiseLogicalMatList.get(logicalStageIndex)
                statefulMemoryNameToUserMatListMap, matListNotUsingStatefulMem, usedStatefulMemSet = self.divideMatNodeListInStatefulMemoryUserAndNonUser(p4ProgramGraph, logicalMatList)
                # Now check whther all the table in each stateful memories list can satisfy memory requirement.
                # At this moment we will write a menthod that will consider all the stateful memories in one stage.
                # later we will add support for mat bifurcation.
                #     Add this note to todo list. we can deep copy a matnode and bifurcate it
                print(hardware)
                deepCopiedResourcesOfStage = hardware.stageWiseResources.get(startingPhyicalStage)
                if(deepCopiedResourcesOfStage == None):
                    print("The deepcopied resrurces for stage "+str(startingPhyicalStage)+" of the hardware is Empty. Severe error. Exiting")
                    exit(1)
                if(self.isStatefulMemorySetAccomodatableInStage(p4ProgramGraph, pipelineID, statefulMemoryNameToUserMatListMap.keys(), hardware, deepCopiedResourcesOfStage)):
                    #the Stateul memories can be embedded on this stage. Now we need to find can we embed all the MAtnodes of statefulMemoryNameToUserMatListMap on this same stage
                    # Now all the MAt nodes in same level matches on differnt fields. But they are from different paths of the TDG. Hence they will never match together.
                    #It implies only one of the matnodes will find a matching entry. Hence onyl one of their action will be executed. Therefore the resource requirement of the
                    #Actions will be the highest of the actions from all the tables. Means, we have to reserve the maximum bitwidth of action for the crossbar,
                    #maximum bitwidth for memory port.
                    #But we have to reserve the full amount of space for TCAM/SRAM based mat entries and their actions.
                    matNodeListThatusesStatefulMemory = []
                    for k in statefulMemoryNameToUserMatListMap:
                        for matNode in statefulMemoryNameToUserMatListMap.get(k):
                            matNodeListThatusesStatefulMemory.append(matNode)
                    matNodeListThatusesStatefulMemory = self.sortNodesBasedOnMatchType(matNodeListThatusesStatefulMemory) # sorted the matnodes according to their matching type. Exact matching got least priority so that they are embedded at last and TCAM's are used at first
                    self.isMatNodesEmbeddableOnThisStage(p4ProgramGraph,pipelineID, matNodeListThatusesStatefulMemory,hardware, deepCopiedResourcesOfStage)

                else:
                    print("The resource requirement for the indirect stateful memories can not be fulfilled by the availalbe resources of stage: "+str(deepCopiedResourcesOfStage.index))
                    print("Halintg the embedding process here")

    def sortNodesBasedOnMatchType(self, matNodeList):
        '''We give highest priority to matchtype that is not exact, so that TCAM's are at first used for non-exact matching '''
        sortedMatNodeList = []
        for matNode in matNodeList:
            if (matNode.originalP4node.match_type.value == MatchType.EXACT):
                sortedMatNodeList.append(matNode)
            else:
                sortedMatNodeList = [matNode] + sortedMatNodeList
        return sortedMatNodeList

    def isMatNodesEmbeddableOnThisStage(self, p4ProgramGraph,pipelineID, matNodeList,hardware, stageHardwareResource):
        '''This node returns true if all the MAt nodes in matNodeList is embaddable over the stageHardwareResource. If true it also allocates resources in stageHardwareResource.
        Else it returns False.'''
        isEmbeddable = True
        #The follwoing loop claculates Each mat node's resource requirement and saves in the same object.
        maxActionMemoryBitwidth = 0
        maxActionCrossbarBitwidth = 0
        for matNode in matNodeList:
            #Calculate individual resource consumption of rach mat node
            p4ProgramGraph.parsedP4Program.getMatchActionResourceRequirementForMatNode(matNode, p4ProgramGraph, pipelineID)
            # calculate max action memory bitwidth and action crossbar bitwidth-- they are maximum of any table. Because at any time a packet will go through one path in our system.
            # so we only need to accomodate about the maximum action memory bitwidth anc crossbarr
            if (matNode.getMaxBitwidthOfActionParameter() > maxActionMemoryBitwidth):
                print("Old maxActionMemoryBitwidth = "+str(maxActionMemoryBitwidth))
                maxActionMemoryBitwidth = matNode.getMaxBitwidthOfActionParameter()
                print("New maxActionMemoryBitwidth = "+str(maxActionMemoryBitwidth))
            if (matNode.getMaxActionCrossbarBitwidthRequiredByAnyAction() > maxActionCrossbarBitwidth):
                print("Old maxActionCrossbarBitwidth = "+str(maxActionCrossbarBitwidth))
                maxActionCrossbarBitwidth = matNode.getMaxActionCrossbarBitwidthRequiredByAnyAction()
                print("new maxActionCrossbarBitwidth = "+str(maxActionCrossbarBitwidth))

        if (stageHardwareResource.getAvailableActionMemoryBitwidth() >= maxActionMemoryBitwidth) and \
            (stageHardwareResource.getAvailableActionCrossbarBitwidth() > maxActionCrossbarBitwidth):
            stageHardwareResource.allocateActionMemoryBitwidth(maxActionMemoryBitwidth)
            stageHardwareResource.allocateActionCrossbarBitwidth(maxActionCrossbarBitwidth)
            for matNode in matNodeList:
                print("pass")
                if(matNode.originalP4node.match_type.value != MatchType.EXACT):
                    #try to embed the matnode in tcam
                    if(stageHardwareResource.isMatNodeEmbeddableOnTCAMMats(matNode)):
                        stageHardwareResource.allocateMatNodeOverTCAMMat(matNode)
                    else:
                        isEmbeddable = False
                else:
                    if(stageHardwareResource.isMatNodeEmbeddableOnSRAMMats(matNode)):
                        stageHardwareResource.allocateMatNodeOverSRAMMat(matNode)
                    elif(stageHardwareResource.isMatNodeEmbeddableOnTCAMMats(matNode)):
                        stageHardwareResource.allocateMatNodeOverTCAMMat(matNode)
                    else:
                        isEmbeddable = False

            # mat key bidwidth , mat key count, mat entries -- are these things embeddable?
            # then action field count, action crossbar bitwidth, then action memory -- are these thing feasible

        # if total mat entriy rewuirement is okay, if total mat entry fields count and crossbar bitwidth requirement is okay ,
        # total sram requiree dby actions is okay , the action crossbar bitwidth is okay
        #
        # then the set of nodes are embeddable. otherwise not.
        #
        # writre a seperate function for each one of them and that will return true . then write a predicate combining all of them.
        # then do the actual allocations.



    def isStatefulMemorySetAccomodatableInStage(self, p4ProgramGraph,pipelineID, statefulMemSet,hardware, stageHardwareResource):
        print("Test")
        pipelineGraph= p4ProgramGraph.pipelineIdToPipelineGraphMap.get(pipelineID)
        totalSramRequirement=0
        totalBitWidth = 0
        isEmbeddable = True
        for regName in statefulMemSet:
            totalSramRequirementForOneReg, totalBitWidthForOneReg = p4ProgramGraph.parsedP4Program.getRegisterArraysResourceRequirment(regName)
            totalSramRequirement = totalSramRequirement + totalSramRequirementForOneReg
            totalBitWidth = totalBitWidth + totalBitWidthForOneReg
            totalSramBlockRequired = stageHardwareResource.sramRequirementToBlockSizeConversion(totalSramRequirement)
            if(stageHardwareResource.allocateSramBlockForIndirectStatefulMemory( totalSramBlockRequired = totalSramBlockRequired,
                            totalSramPortWidthRequired = totalBitWidthForOneReg, indirectStatefulMemoryName=regName) == True):
                isEmbeddable = True
            else:
                isEmbeddable = False
                print("The resource requirement for the indirect stateful memory: "+regName + " can not be fulfilled with the available resources in stage  "+str(stageHardwareResource.stageIndex))
                return  isEmbeddable
        return  isEmbeddable

# deep copy a hardware stage resource. then from starting stage check whether each of the stateful memoryu is embeddable in one stage or not. if it
#     can not be embedded on the remaining part of a stage, go to next stage

    def divideMatNodeListInStatefulMemoryUserAndNonUser(self,p4ProgramGraph, matNodeList):
        '''
        This function divides the given matNodelist into two subsets. First set contains all the nodes that uses a stateful memoery. Second set contains the MAtnodes that do not uses a stateful memeory in its action
        :param p4ProgramGraph:
        :param matNodeList:
        :return:
        '''
        usedStatefulMemSet = set()
        matListNotUsingStatefulMem= []
        matListUsingStatefulMem= []
        statefulMemoryNameToUserMatListMap={}
        for matNode in matNodeList:
            if(len(matNode.getStatefulMemoeryNamesAsSet()) >0):
                usedStatefulMemSet = usedStatefulMemSet.union(matNode.getListOfStatefulMemoriesBeingUsedByMatNodeAsSet())
                for sfMemName in usedStatefulMemSet:
                    if(statefulMemoryNameToUserMatListMap.get(sfMemName) == None):
                        statefulMemoryNameToUserMatListMap[sfMemName] = []
                    matList = statefulMemoryNameToUserMatListMap.get(sfMemName)
                    matList.append(matNode)
                    statefulMemoryNameToUserMatListMap[sfMemName] = matList
            else:
                matListNotUsingStatefulMem.append(matNode)
        return  statefulMemoryNameToUserMatListMap, matListNotUsingStatefulMem, usedStatefulMemSet
    # logicalmatlist er protita element kon stateful element use korche seta pacchi. okhan theke dui set a vag korte pari.
    # tarpo okhan theke jara stateful memoery use korche, sei element gulor set nibo. tahole unique stateful memoery gulor name pacchi.
    # tarpor sei unique element gulor level list ta niye setar set bananbo. setate ekta e level thaka uchit.



    #
    # Assume that previous part already converted the indirect register based nodes and bifurcated them.
    # If we want to handle direct register or counter or meter, then we do not need to
    # bifurcate them. When we want to handle them in our system keep it in mind.
    #
    # precondition: find the levels of each stateful memory and store it in some place. while finding this, make a crosscheck of whether a statefuyl
    # mem is getting assigned to multiple
    #     level or not
    #
    # algo
    # 1) divide the set of Mat in 2 part. one part deals with indirect stateful mem. another part does not need stateful mem.
    # 2) if the register array requiment of the tables are not accomdatable in one stage then halt (we will show some good halping messages here).
    # Because the p4 program is not embedable in hardware.
    # Now, there may be a case, when we are assginigng two indirect statefl mem in one stage, but practically they need resource more than one stage and they
    # can be assigned in two separate stages. we need to handl ethis in our stategul memory based bifurcation part. To handle this, we can calculate
    # the list of stateful memory accessed in each level. Now assume a level is accessing two stateful memories, then from the statefulMemoryToLevepMap, we can find
    # which stateful memories are mapped to this level. If we find more than one levels are mapped here, then we can divide them over multiple stages. done.
    # now there remains a question what if the order of access of these stateful memories are conflicting, we assume that this is alreadychecked by the syntax analysis part.
    # we will also do a anlysis in our embedding scheme.
    # 3) after the stateful mem based tables are embedded in one stage, we can embed the rest of the mat's (2nd set of mat which do not need any stateful mem)
    # in one or more than mat according to necessity.
    # 4) while embedding a table, if a table's resource requirement need to be expanded over multiple stages (given that it does not need indirect stateful mem),
    # we will spread it over multiple stages.
    # 5) keep track of the stages where the levels are assigned.


    #TODO we will implement this later. 
    # write a function to find the order of stateful memory access of different mat.
    #
    # for each mat, find its order of stateful mem access, reuse the code of  the fubnction which finbds the stateful memory access of a mat.
    # that function, only find the stateful memory uses, here we need to keep them in exact order.
    # for next table, pass that order and if it not maintains same order then there is a problem. show error message. simple,