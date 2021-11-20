import logging
import ConfigurationConstants as confConst
import math
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
        self.availableActionMemoryBitWidth = stageResourceDescription.action_crossbar_bit_width
        self.usedActionMemoryBitWidth = 0
        self.availableNumberOfActions = stageResourceDescription.maximum_actions_supported
        self.usedNumberOfActions = 0
        self.sramResource = SRAMResource(stageResourceDescription.sram_resources, self.rmtHWSpec)
        self.sramMatResource = SRAMMatResource(stageResourceDescription.sram_mat_resources, self.rmtHWSpec)
        self.tcamMatResource = TCAMMatResource(stageResourceDescription.tcam_mat_resources, self.rmtHWSpec)
        self.aluResource = AluResource(stageResourceDescription.alu_resources, self.rmtHWSpec)
        self.externResource = ExternResource(stageResourceDescription.extern_resources, self.rmtHWSpec)

    def getAvailableSRAMMatKeyBitwidth(self):
        return self.sramMatResource.availableSramMatCrossbarBitwidth

    def getAvailableSRAMMatKeyCount(self):
        return self.sramMatResource.availableSramMatFields

    def getAvailableSRAMMatEntrieCountforGivenWidth(self, keyWidth):
        '''Assuming that, the kwywidth is already converted into the necessary width for the SRAM based MAT using convertMatKeyBitWidthLengthToSRAMMatKeyLength.
        So the whole keywidth will be of multiple in terms of SRAM Mat blocks.'''
        requiredNumberOfSRAMblockForTheKey = int(keyWidth/self.sramMatResource.sramMatBitWidth)
        #Now how many entries of this width the available sram can support? nned to keep another
        return self.sramMatResource.availableSramMatFields

    def getAvailableTCAMMatKeyBitwidth(self):
        return self.tcamMatResource.availableTcamMatCrossbarBitwidth

    def getAvailableTCAMMatKeyCount(self):
        return self.tcamMatResource.availableTcamMatFields

    def convertMatKeyBitWidthLengthToSRAMMatKeyLength(self, matKeysBitWidth):
        requiredSRAMMatBitwidth = math.ceil(matKeysBitWidth/self.sramMatResource.sramMatBitWidth) * self.sramMatResource.sramMatBitWidth
        return requiredSRAMMatBitwidth

    def convertMatKeyBitWidthLengthToTCAMMatKeyLength(self, matKeysBitWidth):
        requiredTCAMMatBitwidth = math.ceil(matKeysBitWidth/self.tcamMatResource.perTcamBlockBitWidth) * self.tcamMatResource.perTcamBlockBitWidth
        return requiredTCAMMatBitwidth

    def getAvailableActionMemoryBitwidth(self):
        return self.availableActionMemoryBitWidth

    def getAvailableActionCrossbarBitwidth(self):
        return self.availableActionCrossbarBitWidth

    def allocateActionMemoryBitwidth(self, actionMemoryBitwidth):
        self.availableActionMemoryBitWidth = self.availableActionMemoryBitWidth - actionMemoryBitwidth
        self.usedActionMemoryBitWidth = self.usedActionMemoryBitWidth + actionMemoryBitwidth
        pass

    def allocateActionCrossbarBitwidth(self, actionCrossbarBitwidth):
        self.availableActionCrossbarBitWidth = self.availableActionCrossbarBitWidth - actionCrossbarBitwidth
        self.usedActionCrossbarBitWidth = self.usedActionCrossbarBitWidth + actionCrossbarBitwidth
        pass
    def getTotalAccomodatableTcamBasedMATEntriesForGivenKeyBitwidth(self, matKeyBitWidth):
        matKeyTcamBlockWidth = int(matKeyBitWidth/self.tcamMatResource.perTcamBlockBitWidth) # Means how many blocks we need to merge to form a key. For example: for 80 bit mat key we need 2 40 bit tcam block
        requiredBlock = math.floor(self.tcamMatResource.availableTcamMatBlocks/matKeyTcamBlockWidth) # if we need 3 blocks to form a mat key and we have 5 tcam block then we can accomodate only 1 block for the matkey
        accomodatableTcamEntries = requiredBlock * self.tcamMatResource.perTcamBlockRowCount
        return  matKeyTcamBlockWidth, requiredBlock, accomodatableTcamEntries

    def getTotalAccomodatableActionEntriesForGivenKeyBitwidth(self, actionEntryBitwidth):
        actionEntrySRAMBlockwidth = int(actionEntryBitwidth/self.sramResource.availalbeSramBlockBitwidth) # Means how many blocks we need to merge to form a key. For example: for 180 bit action entry key we need at least 2 112 bit wide sram block
        requiredSRAMBlock = math.floor(self.sramResource.availableSramBlocks/matKeyTcamBlockWidth) # if we need 3 blocks to form a mat key and we have 5 tcam block then we can accomodate only 1 block for the matkey
        accomodatableTcamEntries = requiredBlock * self.tcamMatResource.perTcamBlockRowCount
        return  matKeyTcamBlockWidth, requiredBlock, accomodatableTcamEntries

    def isMatNodeEmbeddableOnTCAMMats(self, matNode):

        # check whther, the key bit width and lengths are within available bitwdth and range
        # Then check, number of entries is accomodatable or not
        # then check total action memory is accomodatable or not
        isEmbeddable = False

        if(matNode.totalKeysTobeMatched <= self.getAvailableTCAMMatKeyCount()) and \
                (self.convertMatKeyBitWidthLengthToTCAMMatKeyLength(matNode.matKeyBitWidth) <= self.getAvailableTCAMMatKeyBitwidth()):
            isEmbeddable=True # The key count and bit width is conformant with available resource
        else:
            print("The mat node: "+matNode.name+" requires total "+str(matNode.totalKeysTobeMatched)+" match keys and their bitwidth is "+str(self.convertMatKeyBitWidthLengthToTCAMMatKeyLength(matNode.matKeyBitWidth)))
            print("But the TCAM at stage "+str(self.stageIndex)+" can accomodate "+str(self.getAvailableTCAMMatKeyCount())+" MAT keys and their bttwidth is "+str(self.getAvailableTCAMMatKeyBitwidth()))
            isEmbeddable = False
            return isEmbeddable
        matKeyTcamBlockWidth, requiredBlock, accomodatableTcamEntries = self.getTotalAccomodatableTcamBasedMATEntriesForGivenKeyBitwidth(self.convertMatKeyBitWidthLengthToTCAMMatKeyLength(matNode.matKeyBitWidth))
        if(accomodatableTcamEntries >= matNode.getRequiredNumberOfMatEntries()):
            print("Test")
            pass
        else:
            print("The mat node: "+matNode.name+" requires total "+str(matNode.getRequiredNumberOfMatEntries())+" match entries in the TCAM based table")
            print("But the TCAM at stage "+str(self.stageIndex)+" can accomodate "+str(accomodatableTcamEntries)+" MAT entries.")
            isEmbeddable = False
            return isEmbeddable



    def isMatNodeEmbeddableOnSRAMMats(self, matNode):
        print("In isMatNodeEmbeddableOnSRAMMats.still unimplemented")
        exit(1)


    def sramRequirementToBlockSizeConversion(self, sramRequirementInBits):
        #TODO: a little bit problem here in this callucation. Assume we have 32x28 sram rows in a block. and we need 17 bit wide register entry to be accomodated in this stage.
        # Now at the end of one block we may have only 2 bits remaining. So dor a sepcific entry we have to look at two blocks. this case is not handled here
        totalSramBlockRequired = math.ceil(sramRequirementInBits/(self.sramResource.availalbeSramBlockBitwidth*self.sramResource.availableSramRows))
        return  totalSramBlockRequired

    def allocateSramBlockForIndirectStatefulMemory(self, totalSramBlockRequired, totalSramPortWidthRequired, indirectStatefulMemoryName):
        if (self.sramResource.availableSramPortBitwidth >= totalSramPortWidthRequired) and (self.sramResource.availableSramBlocks >= totalSramBlockRequired):
            #TODO : record here which stateful register array (indirectStatefulMemoryName) is using these blocks
            self.sramResource.availableSramBlocks = self.sramResource.availableSramBlocks - totalSramBlockRequired
            self.sramResource.usedSramBlocks = self.sramResource.usedSramBlocks + totalSramBlockRequired
            self.sramResource.availableSramPortBitwidth = self.sramResource.availableSramPortBitwidth - totalSramPortWidthRequired
            self.sramResource.usedSramPortBitwidth = self.sramResource.usedSramPortBitwidth + totalSramPortWidthRequired
            return True
        return False



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
        self.availableSramPortBitwidth = sram_resources.memory_port_width * sram_resources.memory_port_count
        self.usedSramPortBitwidth = 0
        self.availableActionMemoryBitwidth = sram_resources.memory_port_width * sram_resources.memory_port_count
        self.usedActionMemoryBitwidth = 0
        self.availableSramBlocks = sram_resources.memory_block_count
        self.usedSramBlocks = sram_resources.memory_block_count
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
            # print(externRsrcDes)
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