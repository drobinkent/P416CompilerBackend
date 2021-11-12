import logging
import ConfigurationConstants as confConst
logger = logging.getLogger('StageWiseResource')
hdlr = logging.FileHandler(confConst.LOG_FILE_PATH )
hdlr.setLevel(logging.INFO)
# formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
formatter = logging.Formatter('%(message)s','%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)


class StageWiseResource:

    def __init__(self, stageIndex, stageResourceDescription, rmtHWSpec ): # need to pass the instructionset here
        self.stageIndex = stageIndex
        self.rmtHWSpec = rmtHWSpec
        self.unprocessedStageResourceDescription = stageResourceDescription
        self.availableActionCrossbarBitWidth = stageResourceDescription.action_crossbar_bit_width
        self.usedActionCrossbarBitWidth = 0
        self.availableActions = stageResourceDescription.maximum_actions_supported
        self.usedActions = 0
        self.aluResource = AluResource(stageResourceDescription.alu_resources, self.rmtHWSpec)
        self.externResource = ExternResource(stageResourceDescription.extern_resources, self.rmtHWSpec)



        pass

class SRAMMatResource:

    def __init__(self):
        pass

class TCAMMatResource:

    def __init__(self):
        pass

class SRAMResource:

    def __init__(self):
        pass

class AluResource:

    def __init__(self, aluResourcesDescription, rmtHWspec):
        self.availableBitwidthToAluInstructionMap= {}
        self.usedBitwidthToAluInstructionMap= {}
        for aluRsrcDes in aluResourcesDescription:
            instructionSpec = rmtHWspec.nameToAluInstructionMap.get(aluRsrcDes.name)
            if(instructionSpec == None):
                logger.info("Instruction specification for instruction type: "+aluRsrcDes.name+ " is not found in hardware specification. Exiting")
                exit(1)
            aluInstructionBitwidth = instructionSpec.alu_bitwidth
            if(self.availableBitwidthToAluInstructionMap.get(aluInstructionBitwidth) == None):
                self.availableBitwidthToAluInstructionMap[aluInstructionBitwidth] = []
            for i in range(0, aluRsrcDes.count):
                bitWiseInstructionList = self.availableBitwidthToAluInstructionMap.get(aluInstructionBitwidth)
                bitWiseInstructionList.append(instructionSpec)
                self.availableBitwidthToAluInstructionMap[aluInstructionBitwidth] = bitWiseInstructionList







class ExternResource:

    def __init__(self,externResourcesDescription, rmtHWSpec):
        self.availableNameToExternInstructionMap= {}
        self.usedNameToExternInstructionMap= {}
        We need to maintain both name and botwidht to extern resource map.
        for externRsrcDes in externResourcesDescription:
            print(externRsrcDes)
            instructionSpec = rmtHWSpec.nameToExternInstructionMap.get(externRsrcDes.name)
            if(instructionSpec == None):
                logger.info("Instruction specification for instruction type: "+externRsrcDes.name+ " is not found in hardware specification. Exiting")
                exit(1)
            externInstructionBitwidth = instructionSpec.ex
            if(self.availableBitwidthToAluInstructionMap.get(externInstructionBitwidth) == None):
                self.availableBitwidthToAluInstructionMap[externInstructionBitwidth] = []
            for i in range(0, externRsrcDes.count):
                bitWiseInstructionList = self.availableBitwidthToAluInstructionMap.get(externInstructionBitwidth)
                bitWiseInstructionList.append(instructionSpec)
                self.availableBitwidthToAluInstructionMap[externInstructionBitwidth] = bitWiseInstructionList