

from ortools.linear_solver import pywraplp

from DependencyAnlyzer.DefinitionConstants import PipelineID
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
        if(len(pipelineGraph.stageWiseLogicalMatList.get(logicalStageNumbersAsList[0]))>1 ):
            logger.info("The largest logical stage should only contain the dummy Start node. hence only one node can exist in this stage. But we have more than one MAT node in ths list.So there are some problem. Please DEBUG> Exiting")
            print("The largest logical stage should only contain the dummy Start node. hence only one node can exist in this stage. But we have more than one MAT node in ths list.So there are some problem. Please DEBUG> Exiting")
            (1)
        if(len(pipelineGraph.stageWiseLogicalMatList.get(logicalStageNumbersAsList[len(logicalStageNumbersAsList)-1]))>1 ):
            logger.info("The smallest logical stage should only contain the dummy END node. hence only one node can exist in this stage. But we have more than one MAT node in ths list.So there are some problem. Please DEBUG> Exiting")
            print("The smallest logical stage should only contain the dummy END node. hence only one node can exist in this stage. But we have more than one MAT node in ths list.So there are some problem. Please DEBUG> Exiting")
            (1)
        if(pipelineGraph.stageWiseLogicalMatList.get(logicalStageNumbersAsList[len(logicalStageNumbersAsList)-1])[0].name != confConst.DUMMY_END_NODE):
            print("The MAT node: "+ pipelineGraph.stageWiseLogicalMatList.get(logicalStageNumbersAsList[len(logicalStageNumbersAsList)-1])[0].name +" with smallest logical stage number :"+str(logicalStageNumbersAsList[len(logicalStageNumbersAsList)-1])+ " must have to be DUMMY End node. Debug please Exiting")
            exit(1)
        if(pipelineGraph.stageWiseLogicalMatList.get(logicalStageNumbersAsList[0])[0].name != confConst.DUMMY_START_NODE):
            print("The MAT node: "+ pipelineGraph.stageWiseLogicalMatList.get(logicalStageNumbersAsList[0])[0].name +" with highest logical stage number :"+str(logicalStageNumbersAsList[0])+ " must have to be DUMMY End node. Debug please Exiting")
        return

    def embedP4ProgramAccordingToSingleMatrix(self, p4ProgramGraph,pipelineID):
        print("Starting embedding the P4 Program graph on to the hardware")
        pipelineGraph = p4ProgramGraph.pipelineIdToPipelineGraphMap.get(pipelineID)
        logicalStageNumbersAsList = list(pipelineGraph.stageWiseLogicalMatList.keys())
        logicalStageNumbersAsList.sort(reverse=True) # We are sorting the logical stage numbers in descending order. Because we have calculated the levels in reverse order due to use of DFS
        #The first element in this list will be the logical stage number for the dummy start node.
        # And the last number will be the logical stage number for the dummy end node. The logical stage number  must should be -1
        self.sanityCheckingOfTheLogicalMats(logicalStageNumbersAsList, pipelineGraph)

        for logicalStageIndex in logicalStageNumbersAsList:
            if(pipelineGraph.stageWiseLogicalMatList.get(logicalStageIndex)[0].name == confConst.DUMMY_END_NODE) \
                or (pipelineGraph.stageWiseLogicalMatList.get(logicalStageIndex)[0].name == confConst.DUMMY_START_NODE):
                continue
            else:
                logicalMatList = pipelineGraph.stageWiseLogicalMatList.get(logicalStageIndex)
                for logicalMat in logicalMatList:
                    # print(logicalMat)
                    totalKeysTobeMatched, matKeyBitWidth, headerFieldWiseBitwidthOfMatKeys = p4ProgramGraph.parsedP4Program.getMatchKeyResourceRequirementForMatNode(logicalMat,pipelineID)
                    p4ProgramGraph.parsedP4Program.getActionResourceRequirementForMatNode(logicalMat,p4ProgramGraph,pipelineID)
                    #Embed logicalMat



    # get the levels in sorted order.
    # if -1 is dummy end and maximum is only dummy start then it is okay. otherwise something is wrong. we will stop there.
    # Write two seprate cionditions for checking these two.
    # Then fropm dmmy start we will start processing.