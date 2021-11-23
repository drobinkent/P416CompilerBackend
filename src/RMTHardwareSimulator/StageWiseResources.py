import logging
import ConfigurationConstants as confConst
import math

from P416JsonParser import MatchType

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
        self.availableActionMemoryBlocks = stageResourceDescription.action_memory_blocks
        self.usedActionMemoryBlocks = 0
        self.actionMemoryBlockBitWidth = stageResourceDescription.action_memory_block_bit_width
        # self.availableActionMemoryBitWidth = stageResourceDescription.action_crossbar_bit_width
        # self.usedActionMemoryBitWidth = 0
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
    def allocateTCAMMatKeyBitwidth(self, keyWidth):
        self.tcamMatResource.availableTcamMatCrossbarBitwidth = self.tcamMatResource.availableTcamMatCrossbarBitwidth - keyWidth
        self.tcamMatResource.usedTcamMatCrossbarBitwidth = self.tcamMatResource.usedTcamMatCrossbarBitwidth + keyWidth

    def allocateTCAMMatBlocks(self, blockCount):
        self.tcamMatResource.availableTcamMatBlocks = self.tcamMatResource.availableTcamMatBlocks - blockCount
        self.tcamMatResource.usedTcamMatBlocks = self.tcamMatResource.usedTcamMatBlocks + blockCount

    def getAvailableTCAMMatKeyCount(self):
        return self.tcamMatResource.availableTcamMatFields
    def allocateTCAMMatKeyCount(self, keyCount):
        self.tcamMatResource.availableTcamMatFields = self.tcamMatResource.availableTcamMatFields - keyCount
        self.tcamMatResource.usedTcamMatFields = self.tcamMatResource.usedTcamMatFields + keyCount

    def convertMatKeyBitWidthLengthToSRAMMatKeyLength(self, matKeysBitWidth):
        requiredSRAMMatBitwidth = math.ceil(matKeysBitWidth/self.sramMatResource.sramMatBitWidth) * self.sramMatResource.sramMatBitWidth
        return requiredSRAMMatBitwidth

    def convertMatKeyBitWidthLengthToTCAMMatKeyLength(self, matKeysBitWidth):
        requiredTCAMMatBitwidth = math.ceil(matKeysBitWidth/self.tcamMatResource.perTcamBlockBitWidth) * self.tcamMatResource.perTcamBlockBitWidth
        return requiredTCAMMatBitwidth

    def getAvailableActionMemoryBitwidth(self):
        return self.availableActionMemoryBlocks * self.actionMemoryBlockBitWidth

    def getAvailableActionCrossbarBitwidth(self):
        return self.availableActionCrossbarBitWidth

    def allocateActionMemoryBitwidth(self, actionMemoryBitwidth):
        requiredActionMemoryBlockWidth = math.ceil(actionMemoryBitwidth / self.actionMemoryBlockBitWidth)
        self.availableActionMemoryBlocks = self.availableActionMemoryBlocks - requiredActionMemoryBlockWidth
        self.usedActionMemoryBlocks = self.usedActionMemoryBlocks + requiredActionMemoryBlockWidth

    def allocateActionCrossbarBitwidth(self, actionCrossbarBitwidth):
        self.availableActionCrossbarBitWidth = self.availableActionCrossbarBitWidth - actionCrossbarBitwidth
        self.usedActionCrossbarBitWidth = self.usedActionCrossbarBitWidth + actionCrossbarBitwidth
        pass
    def getTotalAccomodatableTcamBasedMATEntriesForGivenKeyBitwidth(self, matKeyBitWidth):
        matKeyBitWidth = self.convertMatKeyBitWidthLengthToTCAMMatKeyLength(matKeyBitWidth)
        matKeyTcamBlockWidth = int(matKeyBitWidth/self.tcamMatResource.perTcamBlockBitWidth) # Means how many blocks we need to merge to form a key. For example: for 80 bit mat key we need 2 40 bit tcam block
        requiredBlock = math.floor(self.tcamMatResource.availableTcamMatBlocks/matKeyTcamBlockWidth) # if we need 3 blocks to form a mat key and we have 5 tcam block then we can accomodate only 1 block for the matkey
        accomodatableTcamEntries = requiredBlock * self.tcamMatResource.perTcamBlockRowCount
        return  matKeyTcamBlockWidth, requiredBlock, accomodatableTcamEntries

    def getTotalAccomodatableActionEntriesForGivenActionEntryWidth(self, actionEntryBitwidth):
        requiredActionMemoryBlockWidth = math.ceil(actionEntryBitwidth / self.actionMemoryBlockBitWidth) # if we have an action entry with parameters width 120 bit and
        #the action memory block bidwidth is 80 then we need at least 2 blocks.
        #Here we are assuming that, assume we have a 80 bit wide 8 port system. now to accomodates 2 92 bit wide paramerers we need 184bit.
        # so in total at least 3 80 b wide ports are necessary. so we will use 3 sram blocks in parallel for this purpose.
        accomodatableActionBlocksInSRAM = math.floor(self.sramResource.availableSramBlocks/requiredActionMemoryBlockWidth)
        totalAccmmodatableActionEntries = accomodatableActionBlocksInSRAM * self.sramResource.perMemoryBlockRowCount
        return requiredActionMemoryBlockWidth, accomodatableActionBlocksInSRAM, totalAccmmodatableActionEntries


    def isActionMemoriesAccomodatable(self, actionEntryBitwidth, numberOfActionEntries): #TODO: at this moment we are assuming that
        requiredActionMemoryBlockWidth = math.ceil(actionEntryBitwidth / self.actionMemoryBlockBitWidth) # if we have an action entry with parameters width 120 bit and
        #the action memory block bidwidth is 80 then we need at least 2 blocks.
        #This requiredActionMemoryBlockWidth will be always less than or equal to the number of availalb eaction memory block width. Assuming that we will precheck it
        if(requiredActionMemoryBlockWidth <= self.availableActionMemoryBlocks) and (self.sramResource.availableSramBlocks>= requiredActionMemoryBlockWidth):
            accomodatableActionBlocksInSRAM = math.floor(self.sramResource.availableSramBlocks/requiredActionMemoryBlockWidth)
            totalAccmmodatableEntries = accomodatableActionBlocksInSRAM * self.sramResource.perMemoryBlockRowCount
            if(accomodatableActionBlocksInSRAM >0) and (numberOfActionEntries <= totalAccmmodatableEntries):
                return True
        else:
            print("The action entries can not be accomodated in this stage. Becuase the reqruier amount of resource is not available")
            exit(1)
        return False

    def allocateMatNodeOverTCAMMat(self, matNode):
        self.allocateTCAMMatKeyCount(matNode.totalKeysTobeMatched)
        self.allocateTCAMMatKeyBitwidth(self.convertMatKeyBitWidthLengthToTCAMMatKeyLength(matNode.matKeyBitWidth))
        matKeyTcamBlockWidth, requiredBlocks, accomodatableTcamEntries = self.getTotalAccomodatableTcamBasedMATEntriesForGivenKeyBitwidth(self.convertMatKeyBitWidthLengthToTCAMMatKeyLength(matNode.matKeyBitWidth))
        #allocate requiredBlocks*matKeyTcamBlockWidth number of basic tcam mat blocks for storing mat entries
        self.allocateTCAMMatBlocks(blockCount= matKeyTcamBlockWidth * requiredBlocks)
        requiredActionMemoryBlockWidth, accomodatableActionBlocksInSRAM, totalAccmmodatableActionEntries= \
            self.getTotalAccomodatableActionEntriesForGivenActionEntryWidth(matNode.getMaxBitwidthOfActionParameter())
        self.allocateSramBlockForActionMemory()




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
        matKeyTcamBlockWidth, requiredBlocks, accomodatableTcamEntries = self.getTotalAccomodatableTcamBasedMATEntriesForGivenKeyBitwidth(self.convertMatKeyBitWidthLengthToTCAMMatKeyLength(matNode.matKeyBitWidth))
        if(accomodatableTcamEntries >= matNode.getRequiredNumberOfMatEntries()):
            isEmbeddable=True
        else:
            print("The mat node: "+matNode.name+" requires total "+str(matNode.getRequiredNumberOfMatEntries())+" match entries in the TCAM based table")
            print("But the TCAM at stage "+str(self.stageIndex)+" can accomodate "+str(accomodatableTcamEntries)+" MAT entries.")
            isEmbeddable = False
            return isEmbeddable

        requiredActionMemoryBlockWidth, accomodatableActionBlocksInSRAM, totalAccmmodatableActionEntries= \
        self.getTotalAccomodatableActionEntriesForGivenActionEntryWidth(matNode.getMaxBitwidthOfActionParameter())
        if(totalAccmmodatableActionEntries >= matNode.getRequiredNumberOfMatEntries()):
            isEmbeddable= True
        else:
            print("The mat node: "+matNode.name+" requires total "+str(matNode.getRequiredNumberOfMatEntries())+" match entries in the TCAM based table.")
            print("But the avialble resource at stage "+str(self.stageIndex)+ " can only accomodate "+str(totalAccmmodatableActionEntries)+" action entires in sram.")
            isEmbeddable=False
        return isEmbeddable



    def isMatNodeListEmbeddableOnThisStage(self, p4ProgramGraph,pipelineID, matNodeList,hardware):
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
                # print("Old maxActionMemoryBitwidth = "+str(maxActionMemoryBitwidth))
                maxActionMemoryBitwidth = matNode.getMaxBitwidthOfActionParameter()
                # print("New maxActionMemoryBitwidth = "+str(maxActionMemoryBitwidth))
            if (matNode.getMaxActionCrossbarBitwidthRequiredByAnyAction() > maxActionCrossbarBitwidth):
                # print("Old maxActionCrossbarBitwidth = "+str(maxActionCrossbarBitwidth))
                maxActionCrossbarBitwidth = matNode.getMaxActionCrossbarBitwidthRequiredByAnyAction()
                # print("new maxActionCrossbarBitwidth = "+str(maxActionCrossbarBitwidth))

        if (self.getAvailableActionMemoryBitwidth() >= maxActionMemoryBitwidth) and \
                (self.getAvailableActionCrossbarBitwidth() > maxActionCrossbarBitwidth):
            self.allocateActionMemoryBitwidth(maxActionMemoryBitwidth)
            self.allocateActionCrossbarBitwidth(maxActionCrossbarBitwidth)
            for matNode in matNodeList: # The matnode list already sorted and TCAM based tables will come first. So they will be embedded at first
                if(matNode.originalP4node.match_type.value != MatchType.EXACT):
                    #try to embed the matnode in tcam
                    if(self.isMatNodeEmbeddableOnTCAMMats(matNode)):
                        self.allocateMatNodeOverTCAMMat(matNode)
                    else:
                        isEmbeddable = False
                else:
                    if(self.isMatNodeEmbeddableOnSRAMMats(matNode)):
                        self.allocateMatNodeOverSRAMMat(matNode)
                    elif(self.isMatNodeEmbeddableOnTCAMMats(matNode)):
                        self.allocateMatNodeOverTCAMMat(matNode)
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
    def allocateSramBlockForActionMemory(self, totalSramBlockRequired, totalSramPortWidthRequired, parentMat):
        if (self.sramResource.availableSramPortBitwidth >= totalSramPortWidthRequired) and (self.sramResource.availableSramBlocks >= totalSramBlockRequired):
            #TODO : record here which mat's stateful memory is using these blocks
            self.sramResource.availableSramBlocks = self.sramResource.availableSramBlocks - totalSramBlockRequired
            self.sramResource.usedSramBlocks = self.sramResource.usedSramBlocks + totalSramBlockRequired
            self.sramResource.availableSramPortBitwidth = self.sramResource.availableSramPortBitwidth - totalSramPortWidthRequired
            self.sramResource.usedSramPortBitwidth = self.sramResource.usedSramPortBitwidth + totalSramPortWidthRequired
            return True
        return False

    def isStatefulMemorySetAccomodatableInStage(self, p4ProgramGraph,pipelineID, statefulMemSet,hardware):
        print("Test")
        pipelineGraph= p4ProgramGraph.pipelineIdToPipelineGraphMap.get(pipelineID)
        totalSramRequirement=0
        totalBitWidth = 0
        isEmbeddable = True
        for regName in statefulMemSet:
            totalSramRequirementForOneReg, totalBitWidthForOneReg = p4ProgramGraph.parsedP4Program.getRegisterArraysResourceRequirment(regName)
            totalSramRequirement = totalSramRequirement + totalSramRequirementForOneReg
            totalBitWidth = totalBitWidth + totalBitWidthForOneReg
            totalSramBlockRequired = self.sramRequirementToBlockSizeConversion(totalSramRequirement)
            if(self.allocateSramBlockForIndirectStatefulMemory( totalSramBlockRequired = totalSramBlockRequired,
                                                                                 totalSramPortWidthRequired = totalBitWidthForOneReg, indirectStatefulMemoryName=regName) == True):
                isEmbeddable = True
            else:
                isEmbeddable = False
                print("The resource requirement for the indirect stateful memory: "+regName + " can not be fulfilled with the available resources in stage  "+str(self.stageIndex))
                return  isEmbeddable
        return  isEmbeddable



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
        self.perMemoryBlockRowCount = sram_resources.memoroy_block_row_count
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