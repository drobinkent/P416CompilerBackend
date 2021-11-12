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
        self.availableNumberOfActions = stageResourceDescription.maximum_actions_supported
        self.usedNumberOfActions = 0
        self.sramResource = SRAMResource(stageResourceDescription.sram_resources, self.rmtHWSpec)
        self.sramMatResource = SRAMMatResource(stageResourceDescription.sram_mat_resources, self.rmtHWSpec)
        self.tcamMatResource = TCAMMatResource(stageResourceDescription.tcam_mat_resources, self.rmtHWSpec)
        self.aluResource = AluResource(stageResourceDescription.alu_resources, self.rmtHWSpec)
        self.externResource = ExternResource(stageResourceDescription.extern_resources, self.rmtHWSpec)



        pass


#==================================== TODO Read following
# VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVIIIIIIIIIIIIIIIIII NOTE:
#
# SRAM, TCAMMAT, SRAMMAT,-- these resources have two proerties. Their actual capacity and port count.
# ubut these two resources are not not lineraly related to each other. for example, a register arrya needs 80b 1024 entirs. they consumes
# necessary resources. And the port width in a stage is 80b * 8. So we have to maintain what are the available
# stam/tcam ports bitwdith at a certain stage. when we want to map an action or match table, we have at first look at
# whther the required bitwidth can be supported by the avaialble port width in the stage. Then we have to
# check the storage capacity.

class SRAMMatResource:

    def __init__(self,sram_mat_resources, rmtHWSpec):
        self.unprocessedSramMatResourceSpec = sram_mat_resources
        self.availableSramMatFields = sram_mat_resources.sram_mat_field_count
        self.usedSramMatFields = 0
        self.availableSramMatCrossbarBitwidth = sram_mat_resources.match_crossbar_bit_width
        self.usedSramMatCrossbarBitwidth = 0
        self.supportedMatchTypes = sram_mat_resources.supported_match_types
        self.sramMatHashingWay = sram_mat_resources.per_sram_mat_block_spec.hashing_way
        self.sramMatBitWidth = sram_mat_resources.per_sram_mat_block_spec.sram_bit_width
        pass

# : int
# match_crossbar_bit_width: int
# block_count: str
# supported_match_types: SupportedMatchTypes
# per_sram_mat_block_spec: PerSRAMMatBlockSpec


class StatefulMemoryBlock:

    def __init__(self, bitWidth, rowCount):
        self.availableBitWidth = bitWidth
        self.usedBitWidth = 0
        self.availableRows = rowCount
        self.usedRows = 0
        pass

class TCAMMatResource:

    def __init__(self,tcam_mat_resources, rmtHWSpec):
        self.unprocessedTcamMatResourceSpec = tcam_mat_resources
        self.availableTcamMatFields = tcam_mat_resources.tcam_mat_field_count
        self.usedTcamMatFields = 0
        self.availableTcamMatCrossbarBitwidth = tcam_mat_resources.match_crossbar_bit_width
        self.usedTcamMatCrossbarBitwidth = 0
        self.availableTcamMatBlocks = tcam_mat_resources.block_count
        self.usedTcamMatBlocks = 0
        self.supportedMatchTypes = tcam_mat_resources.supported_match_types
        self.perTcamBlockBitWidth = tcam_mat_resources.per_tcam_mat_block_spec.tcam_bit_width
        self.perTcamBlockRowCount = tcam_mat_resources.per_tcam_mat_block_spec.tcam_row_count
        pass




class SRAMResource:

    def __init__(self,sram_resources, rmtHWSpec):
        self.unprocessedSramResourceSpec = sram_resources
        self.availableSramPorts = sram_resources.memory_port_count
        self.usedSramPorts = 0
        self.availableSramPortBitwidth = sram_resources.memory_port_width
        self.usedSramPortBitwidth = 0
        self.availableSramBlocks = sram_resources.memory_block_count
        self.availalbeSramBlockBitwidth = sram_resources.memory_block_bit_width
        self.usedSramBlockBitwidth=0
        self.availableSramRows = self.availableSramBlocks * sram_resources.memoroy_block_row_count
        self.usedSramRows=0
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

    # Assume we have register read extern. And according to the hardware we can acccomodate 8 read in one stage. Then
    # we have 8*80 bit read cpability (assuming 80 bitwide memory port). Now assume for a spceific action we need
    # 512 bit read for ingress and 108 bit for egress. So whe we are emnedding 512 bit read for ingress then we need to maintain
    # that in this stage we can read 640 bit in total among them 512 bit are used for ingress and 108 bit for egress.

    def __init__(self,externResourcesDescription, rmtHWSpec):
        self.availableBitwidthToExternInstructionMap= {}
        self.usedBitwidthToExternInstructionMap= {}
        for externRsrcDes in externResourcesDescription:
            print(externRsrcDes)
            instructionSpec = rmtHWSpec.nameToExternInstructionMap.get(externRsrcDes.name)
            if(instructionSpec == None):
                logger.info("Instruction specification for instruction type: "+externRsrcDes.name+ " is not found in hardware specification. Exiting")
                exit(1)
            externInstructionBitwidth = instructionSpec.extern_bitwidth
            if(self.availableBitwidthToExternInstructionMap.get(externInstructionBitwidth) == None):
                self.availableBitwidthToExternInstructionMap[externInstructionBitwidth] = []
            for i in range(0, externRsrcDes.count):
                bitWiseInstructionList = self.availableBitwidthToExternInstructionMap.get(externInstructionBitwidth)
                bitWiseInstructionList.append(instructionSpec)
                self.availableBitwidthToExternInstructionMap[externInstructionBitwidth] = bitWiseInstructionList