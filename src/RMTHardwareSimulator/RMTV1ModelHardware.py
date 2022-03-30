import copy

import sys
sys.path.append("..") # Adds higher directory to python modules path.
from ortools.linear_solver import pywraplp

from DependencyAnlyzer.DefinitionConstants import PipelineID, DependencyType
from P4ProgramParser.P416JsonParser import MatchType
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
        self.pakcetHeaderVectorFieldSizeVsCountMap = {}
        self.totalStages = -1
        self.stageWiseResources= {}
        self.nameToAluInstructionMap={}
        self.nameToExternInstructionMap={}
        self.parserSpecs = None
        self.instructionSetConfigurationRawJsonObjects = RMTV1InstrctionSet.from_dict(JsonParserUtil.loadRowJsonAsDictFromFile(instructionSetConfigurationJsonFile))
        self.hardwareSpecRawJsonObjects = RMTV1HardwareConfiguration.from_dict(JsonParserUtil.loadRowJsonAsDictFromFile(hardwareSpecConfigurationJsonFile))
        self.initResourcesFromRawJsonConfigurations()

        print("Loading device configuration for " + self.name+ " completed" )

    #We need this method to handle the action memory bitwidth and count issue. Because for a single pipeline when we embed multiple node in a physical stage,
    #It implies that only one of the action will succeed once. But when we have multiple pipeline thread, that means,
    # two action can succeed simulanaourly. In the allocate resources for action bitwidth we have always allocated the possible maximum (by checking if
    # the used resource of a this stage is more than of the current node or not) of the
    # action bitiwdith of all the actions. But when we have multiple pipeline wehave to check for more than one pipeline.
    #So this method, just sets the used action  crossbar field count and bitwodth
    def reinitializeResourcesForNewPiepeline(self):
        for stageIndex in self.stageWiseResources.keys():
            stageResource = self.stageWiseResources.get(stageIndex)
            stageResource.usedActionCrossbarBitWidth=0

    def printAvailableResourceStatistics(self):
        stageIndexes = list(self.stageWiseResources.keys()).sort()
        for stageIndex in stageIndexes:
            stageResource = self.stageWiseResources.get(stageIndex)
            stageResource.printAvailableResourceStatistics()

    def printStageHardwareAvailableResourceStatistics(self,stageIndex):
        stageResource = self.stageWiseResources.get(stageIndex)
        if(stageResource == None):
            print("Stage reousrce found None for stage index "+str(stageIndex)+" Severe errror . eXiting ")
            exit(1)
        else:
            stageResource.printAvailableResourceStatistics()


    def initResourcesFromRawJsonConfigurations(self):
        self.totalStages = self.hardwareSpecRawJsonObjects.total_stages
        self.loadPHVSpecs()
        # print(self.hardwareSpecRawJsonObjects)
        self.loadInstructionSet()
        self.loadStageWiseResource()
        self.loadParserSpecs()
        # for i in range(0, self.totalStages):
        #     self.stageWiseResources[i] = self.loadStageResource(i)
    def loadPHVSpecs(self):
        for rawPhvSpecsList in self.hardwareSpecRawJsonObjects.header_vector_specs:
            self.pakcetHeaderVectorFieldSizeVsCountMap[rawPhvSpecsList.bit_width] = rawPhvSpecsList.count
    def getMinBitwidthOfPHVFields(self):
        self.loadPHVSpecs()
        bitWidthList = list(self.pakcetHeaderVectorFieldSizeVsCountMap.keys())
        bitWidthList.sort()
        return bitWidthList[0]

    def  loadParserSpecs(self):
        print(self.hardwareSpecRawJsonObjects.parser_specs)
        self.parserSpecs = self.hardwareSpecRawJsonObjects.parser_specs

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
            for stageIndex in range(stageIndexStart, stageIndexEnd+1):
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

    def mapHeaderFieldsUsingGoogleOR(self, p4ProgramHeaderFieldSpecs):
        #TODO at first convert the p4 programs header fields size
        # p4ProgramHeaderFieldSpecs= self.convertP4PRogramHeaderFieldSizetoPHVFieldSize(p4ProgramHeaderFieldSpecs)
        # print("The converted header specs of the givne P4 program is ",p4ProgramHeaderFieldSpecs)
        data = self.createDataModelForHeaderMapping(p4ProgramHeaderFieldSpecs)
        # Create the mip solver with the SCIP backend.
        solver = pywraplp.Solver.CreateSolver('SAT_INTEGER_PROGRAMMING')
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

    def mapHeaderFields(self, p4ProgramHeaderFieldSpecs):
        # print("In mapHeaderFields")
        phvFieldSizeVsCountMap = copy.deepcopy(self.pakcetHeaderVectorFieldSizeVsCountMap)
        p4ProgramHeaderFieldsSizeInDecreasingOrder = list(p4ProgramHeaderFieldSpecs.keys())
        p4ProgramHeaderFieldsSizeInDecreasingOrder.sort(reverse=True)
        p4ProgramFieldSizeVsPHVFieldSizeMap = {}
        for bitWidth in p4ProgramHeaderFieldsSizeInDecreasingOrder:
            p4HeaderFieldCountForSelectedBitwidth = p4ProgramHeaderFieldSpecs.get(bitWidth)
            for i in range(0, p4HeaderFieldCountForSelectedBitwidth):
                phvFieldListForThisHeaderField = self.fillP4HeaderFieldWithPhvFields(bitWidth,phvFieldSizeVsCountMap)
                # print(phvFieldListForThisHeaderField)
                if(p4ProgramFieldSizeVsPHVFieldSizeMap.get(bitWidth) == None):
                    p4ProgramFieldSizeVsPHVFieldSizeMap[bitWidth] = []
                p4ProgramFieldSizeVsPHVFieldSizeMap[bitWidth]=p4ProgramFieldSizeVsPHVFieldSizeMap.get(bitWidth) + phvFieldListForThisHeaderField

        return p4ProgramFieldSizeVsPHVFieldSizeMap

    def getLargestPHVFieldsForGivenp4HeaderField(self,p4ProgramHeaderBitWidth,phvFieldSizeVsCountMap):
        phvfieldSizes =[]
        for pfSize in phvFieldSizeVsCountMap.keys():
            pfCount = phvFieldSizeVsCountMap.get(pfSize)
            for i in range (0, pfCount):
                phvfieldSizes.append(pfSize)
        phvfieldSizes.sort(reverse=True)
        for phvFieldSize in phvfieldSizes:
            if (phvFieldSize<=p4ProgramHeaderBitWidth) and (phvFieldSizeVsCountMap.get(phvFieldSize)>0):
                return phvFieldSize
        phvfieldSizes.sort()
        waste = 999999999
        selectedPhvFieldWidth = None
        for phvFieldSize in phvfieldSizes:
            if((phvFieldSize - p4ProgramHeaderBitWidth)<waste ):
                waste =phvFieldSize - p4ProgramHeaderBitWidth
                selectedPhvFieldWidth = phvFieldSize
        if(selectedPhvFieldWidth != None):
            return  selectedPhvFieldWidth
        return -1

    def  fillP4HeaderFieldWithPhvFields(self,p4ProgramHeaderBitWidth,phvFieldSizeVsCountMap):
        originalHeaderFieldWidth = p4ProgramHeaderBitWidth
        phvFieldListForThisHeaderField = []
        while(p4ProgramHeaderBitWidth>0):
            nearestSizePhVField = self.getLargestPHVFieldsForGivenp4HeaderField(p4ProgramHeaderBitWidth, phvFieldSizeVsCountMap)

            if(nearestSizePhVField == -1):
                print("A header field of bitwidth "+str(originalHeaderFieldWidth)+" can not be allocated PHV fields in this system. Hence The P4 program can not be mapped tothis hardware. Extiting!!")
                exit(1)
            else:
                phvFieldSizeVsCountMap[nearestSizePhVField]=phvFieldSizeVsCountMap.get(nearestSizePhVField) -1
                p4ProgramHeaderBitWidth = p4ProgramHeaderBitWidth-nearestSizePhVField
                phvFieldListForThisHeaderField.append(nearestSizePhVField)

        return phvFieldListForThisHeaderField


    #================================================= The menthods for embedding starts here

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
        print("Starting embedding the P4 pipeline:"+str(pipelineID)+" graph  on  the hardware")
        pipelineGraph = p4ProgramGraph.pipelineIdToPipelineGraphMap.get(pipelineID)
        logicalStageNumbersAsList = list(pipelineGraph.levelWiseLogicalMatList.keys())
        logicalStageNumbersAsList.sort(reverse=True) # We are sorting the logical stage numbers in descending order. Because we have calculated the levels in reverse order due to use of DFS
        self.sanityCheckingOfTheLogicalMats(logicalStageNumbersAsList, pipelineGraph)
        startingPhyicalStageIndex = min(self.stageWiseResources.keys())
        #TODO: make a check here to understand how many stages does this program need. if it needs more than available stages then we can halt earlier.
        for logicalStageIndex in logicalStageNumbersAsList:
            startingPhysicalStageListForLogicalStageIndex=[]
            endingPhysicalStageListForLogicalStageIndex = []
            if(pipelineGraph.levelWiseLogicalMatList.get(logicalStageIndex)[0].name == confConst.DUMMY_END_NODE) \
                or (pipelineGraph.levelWiseLogicalMatList.get(logicalStageIndex)[0].name == confConst.DUMMY_START_NODE):
                continue
            else:
                print("\n\n\nEmbedding logical stage "+str(logicalStageIndex)+" and the starting physcial stage index for this stage is "+str(startingPhyicalStageIndex))
                print("The hardware resource of physical stage "+str(startingPhyicalStageIndex)+" Before embedding is following")
                hardware.printStageHardwareAvailableResourceStatistics(startingPhyicalStageIndex)
                logicalMatList = pipelineGraph.levelWiseLogicalMatList.get(logicalStageIndex)
                # Currently only supporting register. If want to support counter and meter "in Action class there is a function "getListOfStatefulMemoriesBeingUsed" add read counter and meter supprt there
                statefulMemoryNameToUserMatListMap, matListNotUsingStatefulMem, usedIndirectStatefulMemSet = self.divideMatNodeListInIndirectStatefulMemoryUserAndNonUser(p4ProgramGraph, logicalMatList)
                if(len(statefulMemoryNameToUserMatListMap) >0):
                    physicalStageIndexForIndirectStatefulMemory, deepCopiedResourcesOfStage = self.embedIndirectStatefulMemoryAndDependentMatNodes(p4ProgramGraph,pipelineID, hardware, usedIndirectStatefulMemSet, statefulMemoryNameToUserMatListMap, startingPhyicalStageIndex)
                    if (physicalStageIndexForIndirectStatefulMemory != -1) and (deepCopiedResourcesOfStage != None):
                        hardware.stageWiseResources[physicalStageIndexForIndirectStatefulMemory]= deepCopiedResourcesOfStage
                        startingPhysicalStageListForLogicalStageIndex.append(physicalStageIndexForIndirectStatefulMemory)
                        endingPhysicalStageListForLogicalStageIndex.append(physicalStageIndexForIndirectStatefulMemory)

                matListNotUsingStatefulMem = self.sortNodesBasedOnMatchType(matListNotUsingStatefulMem) # sorting and prioritizing the tables that needs TCAM for matching
                # deepCopiedHW = copy.deepcopy(hardware)
                if(startingPhyicalStageIndex >= hardware.totalStages):
                    print("The matListNotUsingStatefulMem needs to be embedded from stage "+str(startingPhyicalStageIndex)+" Which is more than avilable stages. Can't map the P4 program. Exiting!!!")
                    exit(0)
                startingStageList=[]
                endingStageList = []
                # startingStageList.append(startingPhyicalStageIndex)
                # endingStageList.append(physicalStageIndexForIndirectStatefulMemory)
                #TODO need to sort the matnodes according to their order in original graph. Becuase, for speculative execution we need to make sure
                # the root node and the childs nodes are mebedded in correct order
                matListNotUsingStatefulMem = self.preProcessInterStageTableDependencies(matListNotUsingStatefulMem)
                tblList = []
                matListNotUsingStatefulMem = self.orderTablesAccordingToTheirPositionInTDG(matListNotUsingStatefulMem,tblList)
                matListNotUsingStatefulMem = tblList
                for matNode in matListNotUsingStatefulMem:
                    startingStageIndexForMAtNode, endingStageIndexForMatNode = self.embedMatNodeOverMultipleStage(p4ProgramGraph,pipelineID, matNode, hardware, startingPhyicalStageIndex)
                    if(startingStageIndexForMAtNode==-1) or (endingStageIndexForMatNode == -1):
                        print("The matnode "+matNode.name+" Can not be embedded on any hardware stage after "+str(startingPhyicalStageIndex))
                        print("Halting the embedding processs and exiting. ")
                        exit(1)
                    else:
                        startingStageList.append(startingStageIndexForMAtNode)
                        endingStageList.append(endingStageIndexForMatNode)
                print("The hardware resource of physical stage "+str(startingPhyicalStageIndex)+" after embedding is following")
                hardware.printStageHardwareAvailableResourceStatistics(startingPhyicalStageIndex)
                endingPhysicalStageListForLogicalStageIndex = endingPhysicalStageListForLogicalStageIndex + endingStageList
                endingPhysicalStageListForLogicalStageIndex.sort()
                startingPhyicalStageIndex = endingPhysicalStageListForLogicalStageIndex[len(endingPhysicalStageListForLogicalStageIndex)-1]+1

    def orderTablesAccordingToTheirPositionInTDG(self,matListNotUsingStatefulMem, tblList):
        for tbl in matListNotUsingStatefulMem:
            tblList.append(tbl)
            if(len(tbl.concurrentlyExecutableDependentTableList) >0):
                self.orderTablesAccordingToTheirPositionInTDG(tbl.concurrentlyExecutableDependentTableList, tblList)


    def embedIndirectStatefulMemoryAndDependentMatNodes(self, p4ProgramGraph, pipelineID, hardware, statefulMemorySet, statefulMemoryNameToUserMatListMap, startingStageIndex):
        '''This function finds the physcial stage which can accomodate the stateful memories and the tables use them in same stage and return the stage '''
        '''Moreover this algorithm maps an indirect stateful memory to only one stage. From personal communication with barefoot/intel we 
        learnt that indirect stateful memories are not allowed in multiple stages. so we adopted the notation of using only one stage for an indirect stateful memory'''
        uniqueMATFinderMap = {}
        for k in statefulMemoryNameToUserMatListMap.keys():
            for matNode in statefulMemoryNameToUserMatListMap.get(k):
                if(uniqueMATFinderMap.get(matNode.name) == None):
                    uniqueMATFinderMap[matNode.name] = matNode
        matNodeListThatusesStatefulMemory = self.sortNodesBasedOnMatchType(list(uniqueMATFinderMap.values())) # sorted the matnodes according to their matching type. Exact matching got least priority so that they are embedded at last and TCAM's are used at first
        startingPhyicalStageIndex = startingStageIndex
        deepCopiedResourcesOfStage = copy.deepcopy(hardware.stageWiseResources.get(startingPhyicalStageIndex))
        if(deepCopiedResourcesOfStage == None):
            print("In embedIndirectStatefulMemoryAndDependentMatNodes The deepcopied resrurces for stage "+str(startingPhyicalStageIndex)+" of the hardware is Empty. Severe error. Exiting")
            exit(1)

        flag = False
        while (flag == False ):
            val1 = deepCopiedResourcesOfStage.allocateStatefulMemoerySetOnStage(p4ProgramGraph, pipelineID, statefulMemorySet, hardware)
            val2= deepCopiedResourcesOfStage.isMatNodeListEmbeddableOnThisStage(p4ProgramGraph,pipelineID, matNodeListThatusesStatefulMemory,hardware)
            if(val1==True) and (val2 == True):
                flag= True
                # print("We may allocate resource for the matnoselist here")
            else:
                startingPhyicalStageIndex = startingPhyicalStageIndex + 1
                deepCopiedResourcesOfStage = copy.deepcopy(hardware.stageWiseResources.get(startingPhyicalStageIndex))
                if(deepCopiedResourcesOfStage == None):
                    print("In embedIndirectStatefulMemoryAndDependentMatNodes inside while loop The deepcopied resrurces for stage "+str(startingPhyicalStageIndex)+" of the hardware is Empty. Severe error. Exiting")
                    startingPhyicalStageIndex = -1
                    break
        return startingPhyicalStageIndex, deepCopiedResourcesOfStage





    def embedMatNodeOverMultipleStage(self,p4ProgramGraph,pipelineID, matNode, hardware, startingStageIndex):
        '''If embedding is successfull the function will return starting and ending stage index. if both index are equal then the node is embeddable over single stage.
        If both are -1 then the node is not embeddable. '''
        currentStageIndex = startingStageIndex
        p4ProgramGraph.parsedP4Program.computeMatchActionResourceRequirementForMatNode(matNode, p4ProgramGraph, pipelineID) # computes the resource requirement of the mat node
        remainingMatEntries = matNode.getRequiredNumberOfMatEntries()
        remainingActionEntries = matNode.getRequiredNumberOfActionEntries()
        startingStage = -1
        endginStage = -1
        if(remainingMatEntries != remainingActionEntries) :
            if  (matNode.getMatchType() != MatchType.EXACT):
                startingStage, endginStage = self.embedMatNodeOverTCAMMatInMultipleStageWithActionEntriesReplication(p4ProgramGraph,pipelineID, matNode, hardware, startingStageIndex)
            else:
                startingStage, endginStage = self.embedMatNodeOverSRAMMatInMultipleStageWithActionEntriesReplication(p4ProgramGraph,pipelineID, matNode, hardware, startingStageIndex)
                if(startingStage == - 1 and endginStage == -1 ):
                    startingStage, endginStage = self.embedMatNodeOverTCAMMatInMultipleStageWithActionEntriesReplication(p4ProgramGraph,pipelineID, matNode, hardware, startingStageIndex)
        else: # This case will most likely not happen. Becuase we are assigning fixed number of action entries. which is covered in the if segement. Even if we need
            #  n number of action entries where n is the number of mat entries required, we need to handle same thing. Therefore the functions for replication and distribution mode are same
            #However when we want to generate the configuration binary, we need to handle the index generation . on that case the details of these two functions become different
            if  (matNode.getMatchType() != MatchType.EXACT):
                startingStage, endginStage = self.embedMatNodeOverTCAMMatInMultipleStageWithActionEntriesDistribution(p4ProgramGraph,pipelineID, matNode, hardware, startingStageIndex)
            else:
                startingStage, endginStage = self.embedMatNodeOverSRAMMatInMultipleStageWithActionEntriesDistribution(p4ProgramGraph,pipelineID, matNode, hardware, startingStageIndex)
                if(startingStage == - 1 and endginStage == -1 ):
                    startingStage, endginStage = self.embedMatNodeOverTCAMMatInMultipleStageWithActionEntriesDistribution(p4ProgramGraph,pipelineID, matNode, hardware, startingStageIndex)
        return startingStage, endginStage

    def embedMatNodeOverTCAMMatInMultipleStageWithActionEntriesReplication(self,p4ProgramGraph,pipelineID, matNode, hardware, startingStageIndex):
        startingStage = endingStage = -1
        currentStageIndex = startingStageIndex
        currentStageHardwareResource = hardware.stageWiseResources.get(currentStageIndex)
        remainingMatEntries = matNode.getRequiredNumberOfMatEntries()
        remainingActionEntries = matNode.getRequiredNumberOfActionEntries()
        if(remainingMatEntries < remainingActionEntries):
            remainingActionEntries = remainingMatEntries
        if(remainingMatEntries == 0):
            startingStage, endingStage = startingStageIndex, startingStageIndex
        while(currentStageHardwareResource != None) and (remainingMatEntries > 0):
            accmodatableMatEntries = 0
            if(matNode.matKeyBitWidth == 0):
                accmodatableMatEntries = matNode.getRequiredNumberOfMatEntries()
            else:
                accmodatableMatEntries = currentStageHardwareResource.getTotalAccomodatableTCAMMatEntriesForGivenMatKeyBitwidth(matNode.matKeyBitWidth)
            accmodatableActionEntries = 0
            totalMemoryPortWidth = 0
            if(matNode.getMaxBitwidthOfActionParameter() == 0):
                accmodatableActionEntries = matNode.getRequiredNumberOfActionEntries()
            else:
                accmodatableActionEntries = currentStageHardwareResource.getTotalNumberOfAccomodatableEntriesForGivenBitWidth(bitWidth =  matNode.getMaxBitwidthOfActionParameter(),
                  memoryBlockBitwidth= currentStageHardwareResource.sramResource.perMemoryBlockBitwidth,memoryBlockRowCount=currentStageHardwareResource.sramResource.perMemoryBlockRowCount,hashingWay=1)
                memoryPortWidthList = currentStageHardwareResource.bitWidthToMemoryPortWidthConsumption(matNode.getMaxBitwidthOfActionParameter(), list(currentStageHardwareResource.externResource.bitWidthToRegisterExternMap.keys()))
                totalMemoryPortWidth = sum(memoryPortWidthList)
            if(currentStageHardwareResource.convertMatKeyBitWidthLengthToTCAMMatBlockCount(matNode.matKeyBitWidth) <= currentStageHardwareResource.getAvailableSRAMMatKeyBlockCount()) and \
                    (matNode.matKeyBitWidth <= currentStageHardwareResource.getAvailableTCAMMatKeyCrossbarBitwidth()) and \
                    (currentStageHardwareResource.sramResource.availableSramPortWidthForActionLoading >= totalMemoryPortWidth) and \
                    (currentStageHardwareResource.getAvailableActionCrossbarBitwidth() >= matNode.getMaxBitwidthOfActionParameter()) and \
                    (remainingActionEntries <= accmodatableActionEntries): # last checking is required if action entries are not accomodatable then need to go to next stage
                # Becuase this fucntion assumes a fixed and small number of action for every mat. and replicats these actions in every stages where the mat entries needed to be deivided.
                if(startingStage == -1):
                    startingStage = currentStageIndex
                endingStage = currentStageIndex
                currentStageHardwareResource.allocateMatNodeOverTCAMMat(matNode, min(accmodatableMatEntries, remainingMatEntries), remainingActionEntries,pipelineID)
                remainingMatEntries = remainingMatEntries - min(accmodatableMatEntries, remainingMatEntries)
                if(remainingMatEntries ==0): #Becuse if this matnode is a conditional node and have nothing to embed as mat entry it only need embed action entries.
                    break
                elif(remainingMatEntries>0):
                    currentStageIndex = currentStageIndex + 1
                    currentStageHardwareResource = hardware.stageWiseResources.get(currentStageIndex)
                    if(currentStageHardwareResource==None):
                        print("The mapping algorithm has reached to stage "+str(currentStageIndex)+" Which is invalid. Exiting!!")
            else:
                startingStage = endingStage = -1
                remainingMatEntries = matNode.getRequiredNumberOfMatEntries()
                remainingActionEntries = matNode.getRequiredNumberOfActionEntries()
                currentStageIndex = currentStageIndex + 1
                currentStageHardwareResource = hardware.stageWiseResources.get(currentStageIndex)
                if(currentStageHardwareResource==None):
                    print("The mapping algorithm has reached to stage "+str(currentStageIndex)+" Which is invalid. Exiting!!")

        return  startingStage, endingStage

    def embedMatNodeOverSRAMMatInMultipleStageWithActionEntriesReplication(self,p4ProgramGraph,pipelineID, matNode, hardware, startingStageIndex):
        startingStage = endingStage = -1
        currentStageIndex = startingStageIndex
        currentStageHardwareResource = hardware.stageWiseResources.get(currentStageIndex)
        remainingMatEntries = matNode.getRequiredNumberOfMatEntries()
        remainingActionEntries = matNode.getRequiredNumberOfActionEntries()
        if(remainingMatEntries < remainingActionEntries):
            remainingActionEntries = remainingMatEntries

        # if(remainingMatEntries == 0):
        #     startingStage, endingStage = startingStageIndex, startingStageIndex
        while(currentStageHardwareResource != None) and (remainingMatEntries >=0 ):
            accmodatableMatEntries = 0
            accmodatableActionEntries = 0
            totalMemoryPortWidth = 0
            # if(matNode.getMaxBitwidthOfActionParameter() == 0):
            #     accmodatableActionEntries = matNode.getRequiredNumberOfActionEntries()
            # else:
            accmodatableActionEntries = currentStageHardwareResource.getTotalNumberOfAccomodatableEntriesForGivenBitWidth(bitWidth =  matNode.getMaxBitwidthOfActionParameter(),
              memoryBlockBitwidth= currentStageHardwareResource.sramResource.perMemoryBlockBitwidth,memoryBlockRowCount=currentStageHardwareResource.sramResource.perMemoryBlockRowCount,hashingWay=1)
            memoryPortWidthList = currentStageHardwareResource.bitWidthToMemoryPortWidthConsumption(matNode.getMaxBitwidthOfActionParameter(), list(currentStageHardwareResource.externResource.bitWidthToRegisterExternMap.keys()))
            totalMemoryPortWidth = sum(memoryPortWidthList)
            if(currentStageHardwareResource.convertMatKeyBitWidthLengthToSRAMMatBlockCount(matNode.matKeyBitWidth) <= currentStageHardwareResource.getAvailableSRAMMatKeyBlockCount()) \
                    and (matNode.matKeyBitWidth <= currentStageHardwareResource.getAvailableSRAMMatKeyCrossbarBitwidth()) and \
                    (currentStageHardwareResource.sramResource.availableSramPortWidthForActionLoading >= totalMemoryPortWidth) and \
                    (currentStageHardwareResource.getAvailableActionCrossbarBitwidth() >= matNode.getMaxBitwidthOfActionParameter()) and \
                    (remainingActionEntries <= accmodatableActionEntries): # last checking is required if action entries are not accomodatable then need to go to next stage
                if(startingStage == -1):
                    startingStage = currentStageIndex
                copiedStageResource = copy.deepcopy(currentStageHardwareResource)
                if(matNode.matKeyBitWidth == 0):
                    accmodatableMatEntries = matNode.getRequiredNumberOfMatEntries()
                else:
                    copiedStageResource.allocateSramBlockForActionMemory(actionEntryBitwidth = matNode.getMaxBitwidthOfActionParameter(), numberOfActionEntries= remainingActionEntries)
                    accmodatableMatEntries = copiedStageResource.getTotalNumberOfAccomodatableEntriesForGivenBitWidth(bitWidth = matNode.matKeyBitWidth,
                       memoryBlockBitwidth= copiedStageResource.sramResource.perMemoryBlockBitwidth,memoryBlockRowCount=copiedStageResource.sramResource.perMemoryBlockRowCount,
                        hashingWay=copiedStageResource.sramMatResource.sramMatHashingWay)
                entriesAccomodatationPossible = min(accmodatableMatEntries, remainingMatEntries)

                endingStage = currentStageIndex
                currentStageHardwareResource.allocateMatNodeOverSRAMMat(matNode, entriesAccomodatationPossible, remainingActionEntries,pipelineID) # write a method with this signature.
                remainingMatEntries = remainingMatEntries - min(accmodatableMatEntries, remainingMatEntries)
                # currentStageIndex = currentStageIndex + 1
                currentStageHardwareResource = hardware.stageWiseResources.get(currentStageIndex)
                if(remainingMatEntries ==0): #Becuse if this matnode is a conditional node and have nothing to embed as mat entry it only need embed action entries.
                    break
                elif(remainingMatEntries>0):
                    currentStageIndex = currentStageIndex + 1
                    currentStageHardwareResource = hardware.stageWiseResources.get(currentStageIndex)
                    if(currentStageHardwareResource==None):
                        print("The mapping algorithm has reached to stage "+str(currentStageIndex)+" Which is invalid. Exiting!!")

            else:
                # startingStage = endingStage = -1
                # remainingMatEntries = matNode.getRequiredNumberOfMatEntries()
                # remainingActionEntries = matNode.getRequiredNumberOfActionEntries()
                currentStageIndex = currentStageIndex + 1
                currentStageHardwareResource = hardware.stageWiseResources.get(currentStageIndex)
                if(currentStageHardwareResource==None):
                    print("In embedMatNodeOverSRAMMatInMultipleStageWithActionEntriesReplication, The mapping algorithm has reached to stage "+str(currentStageIndex)+" Which is invalid. Exiting!!")
        return  startingStage, endingStage

    def embedMatNodeOverTCAMMatInMultipleStageWithActionEntriesDistribution(self,p4ProgramGraph,pipelineID, matNode, hardware, startingStageIndex):
        startingStage = endingStage = -1
        currentStageIndex = startingStageIndex
        currentStageHardwareResource = hardware.stageWiseResources.get(currentStageIndex)
        remainingMatEntries = matNode.getRequiredNumberOfMatEntries()
        remainingActionEntries = matNode.getRequiredNumberOfActionEntries()
        if(remainingMatEntries < remainingActionEntries):
            remainingActionEntries = remainingMatEntries
        # if(remainingMatEntries == 0):
        #     startingStage, endingStage = startingStageIndex, startingStageIndex
        while(currentStageHardwareResource != None) and (remainingMatEntries >= 0):
            accmodatableMatEntries = 0
            if(matNode.matKeyBitWidth == 0):
                accmodatableMatEntries = matNode.getRequiredNumberOfMatEntries()
            else:
                accmodatableMatEntries = currentStageHardwareResource.getTotalAccomodatableTCAMMatEntriesForGivenMatKeyBitwidth(matNode.matKeyBitWidth)
            accmodatableActionEntries = 0
            totalMemoryPortWidth = 0
            if(matNode.getMaxBitwidthOfActionParameter() == 0):
                accmodatableActionEntries = matNode.getRequiredNumberOfActionEntries()
            else:
                accmodatableActionEntries = currentStageHardwareResource.getTotalNumberOfAccomodatableEntriesForGivenBitWidth(bitWidth =  matNode.getMaxBitwidthOfActionParameter(),
                      memoryBlockBitwidth= currentStageHardwareResource.sramResource.perMemoryBlockBitwidth,memoryBlockRowCount=currentStageHardwareResource.sramResource.perMemoryBlockRowCount,hashingWay=1)
                memoryPortWidthList = currentStageHardwareResource.bitWidthToMemoryPortWidthConsumption(matNode.getMaxBitwidthOfActionParameter(), list(currentStageHardwareResource.externResource.bitWidthToRegisterExternMap.keys()))
                totalMemoryPortWidth = sum(memoryPortWidthList)
            if(currentStageHardwareResource.convertMatKeyBitWidthLengthToTCAMMatBlockCount(matNode.matKeyBitWidth) <= currentStageHardwareResource.getAvailableSRAMMatKeyBlockCount()) and \
                    (matNode.matKeyBitWidth <= currentStageHardwareResource.getAvailableTCAMMatKeyCrossbarBitwidth()) and \
                    (currentStageHardwareResource.sramResource.availableSramPortWidthForActionLoading >= totalMemoryPortWidth) and \
                    (currentStageHardwareResource.getAvailableActionCrossbarBitwidth() >= matNode.getMaxBitwidthOfActionParameter()) :
                if(startingStage == -1):
                    startingStage = currentStageIndex
                endingStage = currentStageIndex
                # Follwoing line is the main differenc between the replication and distribution method
                entriesToBePlacedInThisStage = min(accmodatableMatEntries, remainingMatEntries, accmodatableActionEntries, remainingActionEntries)
                remainingMatEntries = remainingMatEntries - entriesToBePlacedInThisStage
                remainingActionEntries = remainingActionEntries - entriesToBePlacedInThisStage
                print("We may allocate the resource here")
                currentStageHardwareResource.allocateMatNodeOverTCAMMat(matNode , numberOfMatEntriesToBeAllocated = entriesToBePlacedInThisStage, numberOfActionEntriesToBeAllocated = entriesToBePlacedInThisStage,pipelineID=pipelineID)
                if(remainingMatEntries ==0): #Becuse if this matnode is a conditional node and have nothing to embed as mat entry it only need embed action entries.
                    break
                elif(remainingMatEntries>0):
                    currentStageIndex = currentStageIndex + 1
                    currentStageHardwareResource = hardware.stageWiseResources.get(currentStageIndex)
                    if(currentStageHardwareResource==None):
                        print("In embedMatNodeOverTCAMMatInMultipleStageWithActionEntriesDistribution The mapping algorithm has reached to stage "+str(currentStageIndex)+" Which is invalid. Exiting!!")
            else:
                # startingStage = endingStage = -1
                # remainingMatEntries = matNode.getRequiredNumberOfMatEntries()
                # remainingActionEntries = matNode.getRequiredNumberOfActionEntries()
                currentStageIndex = currentStageIndex + 1
                currentStageHardwareResource = hardware.stageWiseResources.get(currentStageIndex)
                if(currentStageHardwareResource==None):
                    print("In embedMatNodeOverTCAMMatInMultipleStageWithActionEntriesDistribution The mapping algorithm has reached to stage "+str(currentStageIndex)+" Which is invalid. Exiting!!")

        return  startingStage, endingStage
    def embedMatNodeOverSRAMMatInMultipleStageWithActionEntriesDistribution(self,p4ProgramGraph,pipelineID, matNode, hardware, startingStageIndex):
        startingStage = endingStage = -1
        currentStageIndex = startingStageIndex
        currentStageHardwareResource = hardware.stageWiseResources.get(currentStageIndex)
        remainingMatEntries = matNode.getRequiredNumberOfMatEntries()
        remainingActionEntries = matNode.getRequiredNumberOfActionEntries()
        if(remainingMatEntries < remainingActionEntries):
            remainingActionEntries = remainingMatEntries
        if(remainingMatEntries == 0):
            startingStage, endingStage = startingStageIndex, startingStageIndex
        while(currentStageHardwareResource != None) and (remainingMatEntries > 0):
            accmodatableMatEntries = 0
            # if(matNode.matKeyBitWidth == 0):
            #     accmodatableMatEntries = matNode.getRequiredNumberOfMatEntries()
            # else:
            #     # accmodatableMatEntries = currentStageHardwareResource.getTotalAccomodatableSRAMMatEntriesForGivenMatKeyBitwidth(matNode.matKeyBitWidth)
            #     accmodatableMatEntries = currentStageHardwareResource.getTotalNumberOfAccomodatableEntriesForGivenBitWidth(bitWidth = matNode.matKeyBitWidth,
            #             memoryBlockBitwidth= currentStageHardwareResource.sramResource.perMemoryBlockBitwidth,memoryBlockRowCount=currentStageHardwareResource.sramResource.perMemoryBlockRowCount)
            accmodatableActionEntries = 0
            totalMemoryPortWidth = 0
            if(matNode.getMaxBitwidthOfActionParameter() == 0):
                accmodatableActionEntries = matNode.getRequiredNumberOfActionEntries()
            else:
                accmodatableActionEntries = currentStageHardwareResource.getTotalNumberOfAccomodatableEntriesForGivenBitWidth(bitWidth =  matNode.getMaxBitwidthOfActionParameter(),
                       memoryBlockBitwidth= currentStageHardwareResource.sramResource.perMemoryBlockBitwidth,memoryBlockRowCount=currentStageHardwareResource.sramResource.perMemoryBlockRowCount,hashingWay=1)
                memoryPortWidthList = currentStageHardwareResource.bitWidthToMemoryPortWidthConsumption(matNode.getMaxBitwidthOfActionParameter(), list(currentStageHardwareResource.externResource.bitWidthToRegisterExternMap.keys()))
                totalMemoryPortWidth = sum(memoryPortWidthList)

            if(currentStageHardwareResource.convertMatKeyBitWidthLengthToSRAMMatBlockCount(matNode.matKeyBitWidth) <= currentStageHardwareResource.getAvailableSRAMMatKeyBlockCount()) \
              and (matNode.matKeyBitWidth <= currentStageHardwareResource.getAvailableSRAMMatKeyCrossbarBitwidth()) and (currentStageHardwareResource.sramResource.availableSramPortWidthForActionLoading >= totalMemoryPortWidth) and \
                    (currentStageHardwareResource.getAvailableActionCrossbarBitwidth() >= matNode.getMaxBitwidthOfActionParameter()):
                if(startingStage == -1):
                    startingStage = currentStageIndex
                copiedStageResource = copy.deepcopy(currentStageHardwareResource)
                if(matNode.matKeyBitWidth == 0):
                    accmodatableMatEntries = matNode.getRequiredNumberOfMatEntries()
                else:
                    copiedStageResource.allocateSramBlockForActionMemory(actionEntryBitwidth = matNode.getMaxBitwidthOfActionParameter(), numberOfActionEntries= remainingActionEntries)
                    accmodatableMatEntries = copiedStageResource.getTotalNumberOfAccomodatableEntriesForGivenBitWidth(bitWidth = matNode.matKeyBitWidth,
                            memoryBlockBitwidth= copiedStageResource.sramResource.perMemoryBlockBitwidth,
                            memoryBlockRowCount=copiedStageResource.sramResource.perMemoryBlockRowCount,hashingWay=copiedStageResource.sramMatResource.sramMatHashingWay)
                # entriesAccomodatationPossible = min(accmodatableMatEntries, remainingMatEntries)
                endingStage = currentStageIndex
                entriesToBePlacedInThisStage = min(accmodatableMatEntries, remainingMatEntries, accmodatableActionEntries, remainingMatEntries)
                remainingMatEntries = remainingMatEntries - entriesToBePlacedInThisStage
                remainingActionEntries = remainingActionEntries - entriesToBePlacedInThisStage
                print("We may allocate the resource here")
                currentStageHardwareResource.allocateMatNodeOverSRAMMat(matNode, numberOfMatEntriesToBeAllocated = entriesToBePlacedInThisStage, numberOfActionEntriesToBeAllocated = entriesToBePlacedInThisStage, pipelineID=pipelineID)
                if(remainingMatEntries ==0): #Becuse if this matnode is a conditional node and have nothing to embed as mat entry it only need embed action entries.
                    break
                elif(remainingMatEntries>0):
                    currentStageIndex = currentStageIndex + 1
                    currentStageHardwareResource = hardware.stageWiseResources.get(currentStageIndex)
                    if(currentStageHardwareResource==None):
                        print("In embedMatNodeOverSRAMMatInMultipleStageWithActionEntriesDistribution The mapping algorithm has reached to stage "+str(currentStageIndex)+" Which is invalid. Exiting!!")
            else:
                # startingStage = endingStage = -1
                # remainingMatEntries = matNode.getRequiredNumberOfMatEntries()
                # remainingActionEntries = matNode.getRequiredNumberOfActionEntries()
                currentStageIndex = currentStageIndex + 1
                currentStageHardwareResource = hardware.stageWiseResources.get(currentStageIndex)
                if(currentStageHardwareResource==None):
                    print("In embedMatNodeOverSRAMMatInMultipleStageWithActionEntriesDistribution The mapping algorithm has reached to stage "+str(currentStageIndex)+" Which is invalid. Exiting!!")
        return  startingStage, endingStage



    def sortNodesBasedOnMatchType(self, matNodeList):
        '''We give highest priority to matchtype that is not exact, so that TCAM's are at first used for non-exact matching '''
        sortedMatNodeList = []
        for matNode in matNodeList:
            if (matNode.getMatchType() == MatchType.EXACT):
                sortedMatNodeList.append(matNode)
            else:
                sortedMatNodeList = [matNode] + sortedMatNodeList
        return sortedMatNodeList



    def divideMatNodeListInIndirectStatefulMemoryUserAndNonUser(self, p4ProgramGraph, matNodeList):
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
                usedStatefulMemSet = usedStatefulMemSet.union(matNode.getListOfIndirectStatefulMemoriesBeingUsedByMatNodeAsSet())
                for sfMemName in usedStatefulMemSet:
                    if(statefulMemoryNameToUserMatListMap.get(sfMemName) == None):
                        statefulMemoryNameToUserMatListMap[sfMemName] = []
                    matList = statefulMemoryNameToUserMatListMap.get(sfMemName)
                    matList.append(matNode)
                    statefulMemoryNameToUserMatListMap[sfMemName] = matList
            else:
                matListNotUsingStatefulMem.append(matNode)
        return  statefulMemoryNameToUserMatListMap, matListNotUsingStatefulMem, usedStatefulMemSet

    def calculateTotalLatency(self,p4ProgramGraph, hw):
        ingressPipepine1Delay = 0
        egressPipepineDelay = 0
        for pipeline in p4ProgramGraph.parsedP4Program.pipelines:
            if(pipeline.name == PipelineID.INGRESS_PIPELINE.value):
                ingressPipepine1Delay = self.calculateTotalLatencyOfPipeline(p4ProgramGraph, PipelineID.INGRESS_PIPELINE, hw)
                print("ingressPipeline1Delay = 0 is "+str(ingressPipepine1Delay))
            if(pipeline.name == PipelineID.EGRESS_PIPELINE.value):
                egressPipepineDelay = self.calculateTotalLatencyOfPipeline(p4ProgramGraph, PipelineID.EGRESS_PIPELINE, hw)
                print("egressPipelineDelay = 0 is "+str(egressPipepineDelay))
        # print("Total delay is :"+str(ingressPipepine1Delay+egressPipepineDelay))
        # return ingressPipepine1Delay + egressPipepineDelay

    def calculateTotalLatencyOfPipeline(self,p4ProgramGraph, pipelineID, hw):
        stageIndexToTableMap = self.assignStartAndEndTimeForAllMatForOnePipeline(p4ProgramGraph, pipelineID=pipelineID, hw=hw)
        self.finalStartAndEndTimeForAllMatForOnePipeline(stageIndexToTableMap, p4ProgramGraph, pipelineID, hw)
        stageIndexList = list(stageIndexToTableMap.keys())
        stageIndexList.sort()
        prevStageStartTime = 0
        prevStageEndTime = 0
        for stageIndex in range(0, len(stageIndexList)):
            allTables = []
            self.getAllTableForStage(stageIndexToTableMap.get(stageIndex),allTables)
            startTimeList = [t.executionStartingCycle for t in allTables]
            endingTimeList = [x+self.hardwareSpecRawJsonObjects.single_stage_cycle_length for x in startTimeList]
            startTimeList.sort()
            endingTimeList.sort()
            if(len(startTimeList) ==0):
                startTimeList.append(prevStageEndTime+0)
                endingTimeList.append(prevStageEndTime+1)

            prevStageStartTime = startTimeList[len(startTimeList)-1]
            prevStageEndTime = endingTimeList[len(endingTimeList)-1]
            print("Stage: "+str(stageIndex)+" starts execution at cycle "+str(startTimeList[0])+" and finishes execution at cycle "+str(endingTimeList[len(endingTimeList)-1]))

# algo
#
# for first stage assign normally and with thwir own dependency.
#
# for next stages
#     for every table check whther it's part was  assigned on any previous stage or not
#     if assigned on previous stage then that table's starting cycle plus 1 (if on immediate previous stage, or if not on immediate previous stage then number of differences in stage number
#     else it's predecessor is in some other previous stage that table's (last stage : because it may be embedded on more than one stage) starting cycle plus max( dependency, stage number diff)
#     else if it's predecessor is in same stage then calculate what is it's delay with it's predecessor then that predecesor's start  time plus the dependency delay is the starting time for this table
#
# then for every stage calculate all table's start and end cycle. from that as usual find the max latency

    def finalStartAndEndTimeForAllMatForOnePipeline(self,stageIndexToTableMap, p4ProgramGraph, pipelineID, hw):
        stageIndexList = list(stageIndexToTableMap.keys())
        stageIndexList.sort()
        for stageIndex in range(1, len(stageIndexList)):
            hierarchialTableList = stageIndexToTableMap.get(stageIndex)
            allTblListOfThisStage = []
            self.getAllTableForStage(hierarchialTableList,allTblListOfThisStage)
            print("\n\nAssigining final start and end cycle for stage "+str(stageIndex))
            startingCycleInducedFromPreviousStage =-1
            startingCycleInducedFromPrdecessor = -1
            startingCycleInducedFromSameStagePrdecessor = -1
            for t in allTblListOfThisStage:
                previousStageIndex, previousStartingCycle = self.findInstanceOfTable(stageIndexToTableMap, 0, stageIndex, t.name)
                if(previousStageIndex != -1):
                    startingCycleInducedFromPreviousStage = previousStartingCycle + (stageIndex-1- previousStageIndex) # exxtra stages for stage differences
                    if(startingCycleInducedFromPreviousStage == 0):
                        startingCycleInducedFromPreviousStage = 1 #Because if they are in consecutive stages then we need at least 1 cycle
                    print("Table "+t.name +" Found in previous stage "+str(previousStageIndex)+" With starting cycle "+str(previousStartingCycle)+" current stage index is "+str(stageIndex))
                predecessorStageImdex, predecessorStartingCycle, dependencyType = self.findPredecessor(stageIndexToTableMap, startStageIndex=0, endStageIndex=stageIndex, table=t,p4ProgramGraph=p4ProgramGraph, pipelineID=pipelineID)
                if(predecessorStageImdex != -1):
                    startingCycleInducedFromPrdecessor = predecessorStartingCycle + dependencyType + (stageIndex-1- predecessorStageImdex) # exxtra stages for stage differences
                    if(startingCycleInducedFromPrdecessor == 0):
                        startingCycleInducedFromPrdecessor = 1 #Because if they are in consecutive stages then we need at least 1 cycle
                    print("Table "+t.name +"'s final predecessor found in stage: "+str(predecessorStageImdex)+" With starting cycle "+str(predecessorStartingCycle)+" current stage index is "+str(stageIndex)+" Dependency type  is "+str(dependencyType))
                sameStagePredecessorStageImdex, sameStagePredecessorStartingCycle, sameStageDependencyType = self.findPredecessor(stageIndexToTableMap, startStageIndex=stageIndex, endStageIndex=stageIndex+1, table=t,p4ProgramGraph=p4ProgramGraph, pipelineID=pipelineID)
                if(sameStagePredecessorStageImdex != -1):
                    startingCycleInducedFromSameStagePrdecessor = sameStagePredecessorStartingCycle + sameStageDependencyType
                    if(startingCycleInducedFromSameStagePrdecessor == 0):
                        startingCycleInducedFromSameStagePrdecessor = 1 #Because if they are in consecutive stages then we need at least 1 cycle
                    print("Table "+t.name +"'s Same Stage predecessor found in stage: "+str(predecessorStageImdex)+" With starting cycle "+str(predecessorStartingCycle)+" current stage index is "+str(stageIndex)+" Dependency type  is "+str(dependencyType))
                maxStartingCycle = max(startingCycleInducedFromPreviousStage,startingCycleInducedFromPrdecessor, startingCycleInducedFromSameStagePrdecessor)
                # deltaSratingCycle  = maxStartingCycle - t.executionStartingCycle
                t.executionStartingCycle = maxStartingCycle
                t.executionEndingCycle = t.executionStartingCycle + hw.hardwareSpecRawJsonObjects.single_stage_cycle_length
                print("Table: "+str(t.name)+ " Final Execution starting cycle : "+str(t.executionStartingCycle)+" Ending cycle: "+str(t.executionEndingCycle))
                # Now find which is the worst possible depedency of table t . then find how many cycle increase it is. then if a table's ctarting cycle is increase by x
                # then all of its concurently executale table's starting cycle is needed to be updated by x cycle

    def findPredecessor(self,stageIndexToTableMap, startStageIndex, endStageIndex, table,p4ProgramGraph, pipelineID):
        '''Only find predecessor within the stage boundary. Because if the predecessor is in some later stage of current table that means nothing'''
        print("finding predecessor of "+table.name)
        stageIndexList = list(stageIndexToTableMap.keys())
        stageIndexList.sort()
        predecessorsStageIndex = -1
        predecessorsStartingCycle = -1
        dependencyType = None
        for p in table.predecessors:
            if(p== confConst.DUMMY_START_NODE):
                pass
            else:
                stIndex, startCycle = self.findInstanceOfTable(stageIndexToTableMap, startStageIndex, endStageIndex, p)
                if(predecessorsStageIndex < stIndex):
                    predecessorsStageIndex = stIndex
                    predecessorsStartingCycle = startCycle
                    dependencyType = self.getDependencyDelayBetweenTwoLogicalTable(table.predecessors.get(p), table, p4ProgramGraph, pipelineID)
                    print("Predecessor table "+p+" Stage index: "+str(predecessorsStageIndex)+" starting cycle "+str(predecessorsStartingCycle))
        return predecessorsStageIndex, predecessorsStartingCycle, dependencyType


    def findInstanceOfTable(self,stageIndexToTableMap, startStageIndex, endStageIndex, tableName):
        stageIndexList = list(stageIndexToTableMap.keys())
        stageIndexList.sort()
        tablesStageIndex = -1
        tablesStartingCycle = -1
        dependencyType = None
        for stageIndex in range(startStageIndex, endStageIndex):
            hierarchialTableList = stageIndexToTableMap.get(stageIndex)
            tempTablesStartingCycle = self.findInstanceOfTableInTableList(hierarchialTableList, tableName)
            if(tempTablesStartingCycle != -1):
                if(stageIndex> tablesStageIndex):
                    tablesStageIndex = stageIndex
                    tablesStartingCycle = tempTablesStartingCycle
        return tablesStageIndex, tablesStartingCycle

    def findInstanceOfTableInTableList(self,tableList,  tableName):
        startingCycle = -1
        for t in tableList:
            if(t.name == tableName) and (t.executionStartingCycle > startingCycle):
                startingCycle = t.executionStartingCycle
            # print("t.concurrentlyExecutableDependentTableList is "+str(type(t.concurrentlyExecutableDependentTableList)))
            childListStartingCycle = self.findInstanceOfTableInTableList(t.concurrentlyExecutableDependentTableList, tableName)
            if(startingCycle < childListStartingCycle):
                startingCycle = childListStartingCycle
        return startingCycle



    def assignStartAndEndTimeForAllMatForOnePipeline(self, p4ProgramGraph, pipelineID, hw):
        stageIndexList = list(self.stageWiseResources.keys())
        stageIndexList.sort()
        stageIndexToTableMap = {}
        for stageIndex in range(0, len(stageIndexList)):
            tblList = self.stageWiseResources.get(stageIndex).listOfLogicalTableMappedToThisStage.get(pipelineID)
            tblList1 = self.preProcessInterStageTableDependencies(tblList)
            stageIndexToTableMap[stageIndex] = tblList1
        stageIndexList = list(stageIndexToTableMap.keys())
        stageIndexList.sort()
        for stageIndex in range(0, len(stageIndexList)):
            print("\n\nStage index : "+str(stageIndex))
            allTableMappedToThisStage = stageIndexToTableMap.get(stageIndex)
            self.assignStartAndFinishCycleToSuperTable(allTableMappedToThisStage, 0, hw)
        return stageIndexToTableMap

    def assignStartAndFinishCycleToSuperTable(self,tblList, startCycle, hw):
        for tbl in tblList:
            tbl.executionStartingCycle = startCycle
            tbl.executionEndingCycle= tbl.executionStartingCycle + hw.hardwareSpecRawJsonObjects.single_stage_cycle_length
            print("Table "+str(tbl.name)+" Starting cycle "+str(tbl.executionStartingCycle)+" Ending cycle "+str(tbl.executionEndingCycle))
            for child in tbl.concurrentlyExecutableDependentTableList:
                self.assignStartAndFinishCycleToSuperTable([child], tbl.executionStartingCycle+1,hw)


    def assignStartAndEndTimeForAllMatForOnePipelineOld(self, p4ProgramGraph, pipelineID, hw):
        stageIndexList = list(self.stageWiseResources.keys())
        stageIndexList.sort()
        stageIndexToTableMap = {}
        for stageIndex in range(0, len(stageIndexList)):
            tblList = self.stageWiseResources.get(stageIndex).listOfLogicalTableMappedToThisStage.get(pipelineID)
            tblList1 = self.preProcessInterStageTableDependencies(tblList)
            stageIndexToTableMap[stageIndex] = tblList1
        stageIndexList = list(stageIndexToTableMap.keys())
        stageIndexList.sort()
        # allTableMappedToThisStage = self.stageWiseResources.get(0).listOfLogicalTableMappedToThisStage.get(pipelineID)
        # tableNameForThisStage = [x.name for x in allTableMappedToThisStage]
        # print("Tables mapped to physical stage "+str(stageIndexList[0])+" are ",tableNameForThisStage)
        for stageIndex in range(0, len(stageIndexList)):
            print("\n\nStage index : "+str(stageIndex))
            allTableMappedToThisStage = self.stageWiseResources.get(stageIndex).listOfLogicalTableMappedToThisStage.get(pipelineID)
            tableNameForThisStage = [x.name for x in allTableMappedToThisStage]
            # print("Tables mapped to physical stage "+str(stageIndex)+" are ",tableNameForThisStage)
            allTableMappedToPreviousStage = self.getAllTableForStage(stageIndexToTableMap.get(stageIndex-1))
            superTablesInCurrentStage = stageIndexToTableMap.get(stageIndex) # we will only consider the the lonely tables or any table that have some other table as
            # their concurrently exxecutable table list. Because if a table has some concurrently executable tables with it, that means these child tables are actually
            #direct child of this super table in the TDG. Therefore they will not have any direct dependency with any table in previous stage.
            for tbl1 in superTablesInCurrentStage:
                maxCycleDelay = 0
                print("Super table Name "+str(tbl1.name))
                for tbl2 in allTableMappedToPreviousStage:
                    delayInCycleLEngth = self.getDependencyDelayBetweenTwoLogicalTable(tbl2, tbl1, p4ProgramGraph, pipelineID)
                    if(maxCycleDelay <delayInCycleLEngth):
                        maxCycleDelay = delayInCycleLEngth
                        print("Prev stage  table Name "+str(tbl2.name))
                        print("New max delay : "+str(maxCycleDelay))
                for predecessor in tbl1.predecessors.values():

                    delayInCycleLEngth = self.getDependencyDelayBetweenTwoLogicalTable(predecessor, tbl1, p4ProgramGraph, pipelineID)
                    if(maxCycleDelay <delayInCycleLEngth):
                        maxCycleDelay = delayInCycleLEngth
                        print("Predecesor   table Name "+str(predecessor.name))
                        print("New max delay : "+str(maxCycleDelay))
                tbl1.executionStartingCycle = tbl1.executionStartingCycle + maxCycleDelay
                tbl1.executionEndingCycle = tbl1.executionStartingCycle+hw.hardwareSpecRawJsonObjects.single_stage_cycle_length
                print("Super  table "+str(tbl1.name)+" Starting cycle "+str(tbl1.executionStartingCycle)+" Ending cycle "+str(tbl1.executionEndingCycle))
                for child in tbl1.concurrentlyExecutableDependentTableList:
                    child.executionStartingCycle = tbl1.executionStartingCycle+ 1 + maxCycleDelay
                    child.executionEndingCycle  = tbl1.executionStartingCycle+ 1 + maxCycleDelay + hw.hardwareSpecRawJsonObjects.single_stage_cycle_length
                    print("Concucrrently executable table "+str(child.name)+" Starting cycle "+str(child.executionStartingCycle)+" Ending cycle "+str(child.executionEndingCycle))

        for stageIndex in stageIndexToTableMap.keys():
            tblList = stageIndexToTableMap.get(stageIndex)
            print("Stage index: "+str(stageIndex))
            for t in tblList:
                print("\tTable: "+(t.name)+" -- Start time :"+str(t.executionStartingCycle)+" End time :"+str(t.executionEndingCycle))
                for child in t.concurrentlyExecutableDependentTableList:
                    print("\t\tTable: "+(child.name)+" -- Start time :"+str(child.executionStartingCycle)+" End time :"+str(child.executionEndingCycle))
        return stageIndexToTableMap



    def getAllTableForStage(self,tblListInHierarchialFormat, allTable):
        if(tblListInHierarchialFormat == None):
            return []
        for t in tblListInHierarchialFormat:
            if t!= None:
                allTable.append(t)
            for depTable in t.concurrentlyExecutableDependentTableList:
                self.getAllTableForStage([depTable],allTable)
        return allTable
    def preProcessInterStageTableDependencies(self, tblList):

        tblListForThisStage = []
        for tbl in tblList:
            self.clearTable(tbl)
        copyOfTableList = copy.deepcopy(tblList)
        for tbl in tblList:
            for tbl1 in tblList:
                if (tbl.isTableExistsInNoOrReverseOrSuccessorDependencyList(tbl1)) and (len(copyOfTableList)>0):
                    if(self.isTableAlreadyInTTblList(tblListForThisStage,tbl) and (self.isTableAlreadyInTTblList(tblListForThisStage,tbl1))):
                        pass
                    else:
                        copiedTable = self.removeTableFromTableList(copyOfTableList, tbl)
                        if (copiedTable == None):
                            copiedTable = self.getTableReferenceFromTableList(tblListForThisStage,tbl)
                        dependentTable = self.removeTableFromTableList(copyOfTableList,tbl1)
                        if(dependentTable == None): #This should not happen becuase tbl1 will have dependency with tbl only if there is a NO/Reverse/Successor dependency
                            # print("Severer error. This should not happen becuase tbl1 will have dependency with tbl only if there is a NO/Reverse/Successor dependency. Exiting !!")
                            # exit(1)
                            dependentTable = self.getTableReferenceFromTableList(tblListForThisStage,tbl1)
                        if(self.isTableAlreadyInTTblList(tblListForThisStage,dependentTable) == False):
                            copiedTable.concurrentlyExecutableDependentTableList.append(dependentTable)
                        dependentTable.executionStartingCycle = dependentTable.executionStartingCycle +  self.hardwareSpecRawJsonObjects.dependency_delay_in_cycle_legth.successor_dependency + copiedTable.executionStartingCycle
                        if(self.isTableAlreadyInTTblList(tblListForThisStage,copiedTable) == False):
                            tblListForThisStage.append(copiedTable)


        for tbl in copyOfTableList:  # adding the remainigntable who are totallty independent
            if(self.isTableAlreadyInTTblList(tblListForThisStage,tbl) == False):
                tblListForThisStage.append(tbl)
        return tblListForThisStage

    def isTableAlreadyInTTblList(self,tblList,tbl):
        val = self.getTableReferenceFromTableList(tblList, tbl)
        if(val == None):
            return False
        else:
            return True
    def getTableReferenceFromTableList(self,tblList, tbl):
        val = None
        for i in range(0,len(tblList)):
            if tblList[i].name == tbl.name:
                val = tblList[i]
                return val
            else:
                val = None
                for concurrentTable in tblList[i].concurrentlyExecutableDependentTableList:
                    val1 = self.getTableReferenceFromTableList(tblList[i].concurrentlyExecutableDependentTableList, tbl)
                    if(val1 != None):
                        val = val1
        return val

    def clearTable(self, tbl):
        val = None
        if (len(tbl.concurrentlyExecutableDependentTableList) ==0):
            return
        for concurrentTable in tbl.concurrentlyExecutableDependentTableList:
            self.clearTable(concurrentTable)
        tbl.concurrentlyExecutableDependentTableList = []
        return val

    def removeTableFromTableList(self,tblList, tbl):
        val = None
        for i in range(0,len(tblList)):
            if tblList[i].name == tbl.name:
                val = tblList.pop(i)
                return val
        return val


    def calculateTotalLatencyOfPipelineOld(self,p4ProgramGraph, pipelineID):
        stageIndexList = list(self.stageWiseResources.keys())
        stageIndexToStartTimeMap= {}
        stageIndexToEndTimeMap= {}
        stageIndexToStartTimeMap[0] = 0
        stageIndexToEndTimeMap[0] = self.stageWiseResources.get(0).getCycleLengthForThisStage(pipelineID)
        for stageIndex in range(1, len(stageIndexList)):
            interStageDelay = 0
            if(len(self.stageWiseResources.get(stageIndex-1).listOfLogicalTableMappedToThisStage.get(pipelineID)) == 0) or \
                    (len(self.stageWiseResources.get(stageIndex).listOfLogicalTableMappedToThisStage.get(pipelineID)) == 0):
                interStageDelay = 1
            else:
                for stage1Table in self.stageWiseResources.get(stageIndex-1).listOfLogicalTableMappedToThisStage.get(pipelineID):
                    for stage2Table in self.stageWiseResources.get(stageIndex).listOfLogicalTableMappedToThisStage.get(pipelineID):
                        delay = self.getDependencyDelayBetweenTwoLogicalTable(stage1Table, stage2Table, p4ProgramGraph, pipelineID)
                        if(delay>interStageDelay):
                            interStageDelay = delay
            previousStageStartTime = stageIndexToStartTimeMap.get(stageIndex-1)
            currentStageStartTime = previousStageStartTime + interStageDelay
            currentStageEndTime = currentStageStartTime + self.stageWiseResources.get(stageIndex).getCycleLengthForThisStage(pipelineID)
            stageIndexToStartTimeMap[stageIndex] = currentStageStartTime
            stageIndexToEndTimeMap[stageIndex] = currentStageEndTime
        endTimeValueList = list(stageIndexToEndTimeMap.values())
        endTimeValueList.sort()
        print("Final time is "+str(endTimeValueList[len(endTimeValueList)-1]))
        return endTimeValueList[len(endTimeValueList)-1]



    def calculateTotalLatencyOfOnePipeline(self,p4ProgramGraph, pipelineID):
        stageIndexList = list(self.stageWiseResources.keys())
        totalDelay = self.stageWiseResources.get(0).getCycleLengthForThisStage(pipelineID)
        for stageIndex in range(1, len(stageIndexList)-1):
            stage1Dealy = self.stageWiseResources.get(stageIndex-1).getCycleLengthForThisStage(pipelineID)
            stage2Dealy = self.stageWiseResources.get(stageIndex).getCycleLengthForThisStage(pipelineID)
            interStageDelay = 1
            if(len(self.stageWiseResources.get(stageIndex-1).listOfLogicalTableMappedToThisStage.get(pipelineID)) == 0) or\
                (len(self.stageWiseResources.get(stageIndex).listOfLogicalTableMappedToThisStage.get(pipelineID)) == 0):
                interStageDelay = 1
            else:
                for stage1Table in self.stageWiseResources.get(stageIndex-1).listOfLogicalTableMappedToThisStage.get(pipelineID):
                    for stage2Table in self.stageWiseResources.get(stageIndex).listOfLogicalTableMappedToThisStage.get(pipelineID):
                        delay = self.getDependencyDelayBetweenTwoLogicalTable(stage1Table, stage2Table, p4ProgramGraph, pipelineID)
                        if(delay>interStageDelay):
                            interStageDelay = delay
            if(stage1Dealy >0) and (stage2Dealy >0):
                totalDelay = totalDelay +  stage2Dealy - (stage1Dealy - interStageDelay)
            elif ((stage1Dealy == 0) and (stage2Dealy >0)):
                totalDelay = totalDelay
            else:
                totalDelay = totalDelay + 1

        return totalDelay

    def getDependencyDelayBetweenTwoLogicalTable(self, stage1Table, stage2Table, p4ProgramGraph, pipelineID):
        pipeplineGraph = p4ProgramGraph.pipelineIdToPipelineGraphMap.get(pipelineID)
        dep = pipeplineGraph.matToMatDependnecyAnalysis(stage1Table,stage2Table)
        if(dep.dependencyType == DependencyType.MATCH_DEPENDENCY):
            return self.hardwareSpecRawJsonObjects.dependency_delay_in_cycle_legth.match_dependency
        elif(dep.dependencyType == DependencyType.ACTION_DEPENDENCY):
            return self.hardwareSpecRawJsonObjects.dependency_delay_in_cycle_legth.action_dependency
        elif(dep.dependencyType == DependencyType.SUCCESOR_DEPENDENCY):
            return self.hardwareSpecRawJsonObjects.dependency_delay_in_cycle_legth.successor_dependency
        elif(dep.dependencyType == DependencyType.REVERSE_MATCH_DEPENDENCY):
            return self.hardwareSpecRawJsonObjects.dependency_delay_in_cycle_legth.reverse_match_dependency
        elif(dep.dependencyType == DependencyType.NO_DEPNDENCY):
            return self.hardwareSpecRawJsonObjects.dependency_delay_in_cycle_legth.default_dependency
        elif(dep.dependencyType == DependencyType.DUMMY_DEPENDENCY_TO_END):
            return self.hardwareSpecRawJsonObjects.dependency_delay_in_cycle_legth.default_dependency
        elif(dep.dependencyType == DependencyType.DUMMY_DEPENDENCY_FROM_START):
            return 0
        return 0
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