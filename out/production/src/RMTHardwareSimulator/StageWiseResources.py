import copy
import logging

import CompilerConfigurations
import ConfigurationConstants as confConst
import math

import sys

from DependencyAnlyzer.DefinitionConstants import PipelineID

sys.path.append("..") # Adds higher directory to python modules path.
from P4ProgramParser.P416JsonParser import MatchType
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
        self.listOfLogicalTableMappedToThisStage= {}
        self.listOfLogicalTableMappedToThisStage[PipelineID.INGRESS_PIPELINE] = []
        self.listOfLogicalTableMappedToThisStage[PipelineID.EGRESS_PIPELINE] = []
        self.unprocessedStageResourceDescription = stageResourceDescription
        # self.perMatInstructionMemoryCapacity = stageResourceDescription.per_mat_instruction_memory_capacity
        self.availableActionCrossbarBitWidth = stageResourceDescription.action_crossbar_bit_width
        self.usedActionCrossbarBitWidth = 0
        # self.availableActionMemoryBlockWidth = stageResourceDescription.action_memory_block_width
        # self.usedActionMemoryBlocks = 0
        # self.actionMemoryBlockBitWidth = stageResourceDescription.action_memory_block_bitwdith
        # self.availableActionMemoryBitWidth = stageResourceDescription.action_crossbar_bit_width
        # self.usedActionMemoryBitWidth = 0
        self.usedNumberOfActions = 0
        self.sramResource = SRAMResource(stageResourceDescription.sram_resources, self.rmtHWSpec)
        self.sramMatResource = SRAMMatResource(stageResourceDescription.sram_mat_resources, self.rmtHWSpec)
        self.tcamMatResource = TCAMMatResource(stageResourceDescription.tcam_mat_resources, self.rmtHWSpec)
        # self.aluResource = AluResource(stageResourceDescription.alu_resources, self.rmtHWSpec)
        self.externResource = ExternResource(stageResourceDescription.extern_resources, self.rmtHWSpec)




    def printAvailableResourceStatistics(self):
        print("Stage Index: "+str(self.stageIndex))
        print("availableActionCrossbarBitWidth is: "+str(self.availableActionCrossbarBitWidth)+" usedActionCrossbarBitWidth is : "+str(self.usedActionCrossbarBitWidth))
        # print("availableActionMemoryBlocks is: " + str(self.availableActionMemoryBlockWidth) + " usedActionMemoryBlocks is : " + str(self.usedActionMemoryBlocks))
        # print("availableNumberOfActions is: "+str(self.availableNumberOfActions)+" usedNumberOfActions is : "+str(self.usedNumberOfActions))
        self.sramResource.printAvailableResourceStatistics()
        self.sramMatResource.printAvailableResourceStatistics()
        self.tcamMatResource.printAvailableResourceStatistics()

    def getCycleLengthForThisStage(self, pipelineId):
        if(len(self.listOfLogicalTableMappedToThisStage.get(pipelineId)) >0):
            return self.rmtHWSpec.hardwareSpecRawJsonObjects.single_stage_cycle_length
        else:
            return 0



    # def getAvailableSRAMMatKeyCount(self):
    #     return self.sramMatResource.availableSramMatFields

    def getAvailableSRAMMatEntrieCountforGivenWidth(self, keyWidth):
        '''Assuming that, the kwywidth is already converted into the necessary width for the SRAM based MAT using convertMatKeyBitWidthLengthToSRAMMatKeyLength.
        So the whole keywidth will be of multiple in terms of SRAM Mat blocks.'''
        requiredNumberOfSRAMblockForTheKey = int(keyWidth / self.sramMatResource.perSramMatBitWidth)
        #Now how many entries of this width the available sram can support? nned to keep another
        return requiredNumberOfSRAMblockForTheKey

    def getAvailableTCAMMatKeyCrossbarBitwidth(self):
        return self.tcamMatResource.availableTcamMatCrossbarBitwidth
    def getAvailableSRAMMatKeyCrossbarBitwidth(self):
        return self.sramMatResource.availableSramMatCrossbarBitwidth

    def allocateTCAMMatKeyCrossbarBitwidth(self, keyWidth):
        self.tcamMatResource.availableTcamMatCrossbarBitwidth = self.tcamMatResource.availableTcamMatCrossbarBitwidth - keyWidth
        self.tcamMatResource.usedTcamMatCrossbarBitwidth = self.tcamMatResource.usedTcamMatCrossbarBitwidth + keyWidth

    def allocateSRAMMatKeyCrossbarBitwidth(self, keyWidth):
        self.sramMatResource.availableSramMatCrossbarBitwidth = self.sramMatResource.availableSramMatCrossbarBitwidth - keyWidth
        self.sramMatResource.usedSramMatCrossbarBitwidth = self.sramMatResource.usedSramMatCrossbarBitwidth + keyWidth

    def getAvailableTCAMMatKeyBlockCount(self):
        return self.tcamMatResource.availableTcamMatBlocks
    def getAvailableSRAMMatKeyBlockCount(self):
        return self.sramMatResource.availableSramMatBlocks

    def allocateTCAMMatBlockCount(self, blockCount):
        self.tcamMatResource.availableTcamMatBlocks = self.tcamMatResource.availableTcamMatBlocks - blockCount
        self.tcamMatResource.usedTcamMatBlocks = self.tcamMatResource.usedTcamMatBlocks + blockCount

    def allocateSRAMMatBlocks(self, blockCount):

        self.sramMatResource.availableSramMatBlocks = self.sramMatResource.availableSramMatBlocks - blockCount
        self.sramMatResource.usedSramMatBlocks = self.sramMatResource.usedSramMatBlocks + blockCount

    # def getAvailableTCAMMatKeyCount(self):
    #     return self.tcamMatResource.availableTcamMatFields
    # def allocateTCAMMatKeyCount(self, keyCount):
    #     self.tcamMatResource.availableTcamMatFields = self.tcamMatResource.availableTcamMatFields - keyCount
    #     self.tcamMatResource.usedTcamMatFields = self.tcamMatResource.usedTcamMatFields + keyCount

    # def allocateSRAMMatKeyCount(self, keyCount):
    #     self.sramMatResource.availableSramMatFields = self.sramMatResource.availableSramMatFields - keyCount
    #     self.sramMatResource.usedSramMatFields = self.sramMatResource.usedSramMatFields + keyCount

    def convertMatKeyBitWidthLengthToSRAMMatKeyLength(self, matKeysBitWidth):
        requiredSRAMMatBitwidth = math.ceil(matKeysBitWidth / self.sramMatResource.perSramMatBitWidth) * self.sramMatResource.perSramMatBitWidth
        return requiredSRAMMatBitwidth
    def convertMatKeyBitWidthLengthToSRAMMatBlockCount(self, matKeysBitWidth):
        # requiredSRAMMatBlockCount = math.ceil(matKeysBitWidth/self.sramMatResource.perSramMatBitWidth)*self.sramMatResource.sramMatHashingWay
        requiredSRAMMatBlockCount = math.ceil(matKeysBitWidth/self.sramMatResource.perSramMatBitWidth)
        return requiredSRAMMatBlockCount
    def convertMatKeyBitWidthLengthToTCAMMatBlockCount(self, matKeysBitWidth):
        requiredTCAMMatBlockCount = math.ceil(matKeysBitWidth/self.tcamMatResource.perTcamBlockBitWidth)
        return requiredTCAMMatBlockCount
    def convertMatKeyBitWidthLengthToTCAMMatKeyLength(self, matKeysBitWidth):
        requiredTCAMMatBitwidth = math.ceil(matKeysBitWidth/self.tcamMatResource.perTcamBlockBitWidth) * self.tcamMatResource.perTcamBlockBitWidth
        return requiredTCAMMatBitwidth



    def getAvailableActionCrossbarBitwidth(self):
        return self.availableActionCrossbarBitWidth

    def allocateActionMemoryPortWidth(self, actionEntryBitwidth):
        memoryPortWidthList = self.bitWidthToMemoryPortWidthConsumption(actionEntryBitwidth, list(self.externResource.bitWidthToRegisterExternMap.keys()))
        totalMemoryPortWidth = sum(memoryPortWidthList)
        self.sramResource.availableSramPortWidthForActionLoading =  self.sramResource.availableSramPortWidthForActionLoading -totalMemoryPortWidth
        self.sramResource.usedSramPortWidthForActionLoading =  self.sramResource.usedSramPortWidthForActionLoading + totalMemoryPortWidth



    def allocateActionCrossbarBitwidth(self, actionCrossbarBitwidth):
        '''same logic as the previous function.
        When there are multiple tables or action is mapped on a stage, only one table is eecuted at a time and one action is executed at a time
        Therefore, only keep the action that have maximum crossbar width requirement among all table and their actions.'''
        if(actionCrossbarBitwidth > self.usedActionCrossbarBitWidth):
            self.availableActionCrossbarBitWidth = self.availableActionCrossbarBitWidth  + self.usedActionCrossbarBitWidth - actionCrossbarBitwidth
            self.usedActionCrossbarBitWidth =  actionCrossbarBitwidth
        pass
    def allocateMatEntriesOverTCAMBasedMATSinSingleStage(self,matKeyBitWidth, requiredMatEntries):
        if(matKeyBitWidth <=0) or (requiredMatEntries <=0):
            return #Becuase if the match key bitwidth is zero or there is no match key, there is nothing to embed
        matKeyBitWidth = self.convertMatKeyBitWidthLengthToTCAMMatKeyLength(matKeyBitWidth)
        matKeyTcamBlockWidth = math.ceil(matKeyBitWidth/self.tcamMatResource.perTcamBlockBitWidth) # Means how many blocks we need to merge to form a key. For example: for 80 bit mat key we need 2 40 bit tcam block
        requiredBlocks = math.ceil(requiredMatEntries / self.tcamMatResource.perTcamBlockRowCount)
        requiredTCAMBlocks = requiredBlocks * matKeyTcamBlockWidth
        self.allocateTCAMMatBlockCount(requiredTCAMBlocks)
        return

    def allocateMatEntriesOverSRAMBasedMATSInSingleStage(self,matKeyBitWidth, requiredMatEntries, hashingWay):
        blockWidth, requiredSramBlocks = self.getMemoryBlockWidthAndBlockCountFromBitWidthAndRequiredNumberOfEntries(bitWidth=matKeyBitWidth,
                         memoryBlockBitwidth=self.sramResource.perMemoryBlockBitwidth,memoryBlockRowCount=self.sramResource.perMemoryBlockRowCount,
                         requiredNumberOfEntries=requiredMatEntries, hashingWay=hashingWay)
        # requiredSramBlocks = requiredSramBlocks* self.sramMatResource.sramMatHashingWay
        memoryPortWidthList = self.bitWidthToMemoryPortWidthConsumption(matKeyBitWidth, list(self.externResource.bitWidthToRegisterExternMap.keys()))
        totalMemoryPortWidth = sum(memoryPortWidthList)
        self.sramResource.availableSramBlocks = self.sramResource.availableSramBlocks - requiredSramBlocks
        self.sramResource.usedSramBlocks = self.sramResource.usedSramBlocks + requiredSramBlocks

    def deAllocateMatEntriesOverSRAMBasedMATSInSingleStage(self,matKeyBitWidth, requiredMatEntries,hashingWay):
        blockWidth, requiredSramBlocks = self.getMemoryBlockWidthAndBlockCountFromBitWidthAndRequiredNumberOfEntries(bitWidth=matKeyBitWidth,
                 memoryBlockBitwidth=self.sramResource.perMemoryBlockBitwidth,memoryBlockRowCount=self.sramResource.perMemoryBlockRowCount,
                 requiredNumberOfEntries=requiredMatEntries,hashingWay=hashingWay)
        requiredSramBlocks = requiredSramBlocks* self.sramMatResource.sramMatHashingWay
        memoryPortWidthList = self.bitWidthToMemoryPortWidthConsumption(matKeyBitWidth, list(self.externResource.bitWidthToRegisterExternMap.keys()))
        totalMemoryPortWidth = sum(memoryPortWidthList)
        self.sramResource.availableSramBlocks = self.sramResource.availableSramBlocks + requiredSramBlocks
        self.sramResource.usedSramBlocks = self.sramResource.usedSramBlocks - requiredSramBlocks



    # def getTotalAccomodatableSRAMMatEntriesForGivenMatKeyBitwidth(self, matKeyBitWidth):
    #     matKeyBitWidth = self.convertMatKeyBitWidthLengthToSRAMMatKeyLength(matKeyBitWidth)
    #     matKeySRAMBlockWidth = math.ceil(matKeyBitWidth / self.sramMatResource.perSramMatBitWidth) *self.sramMatResource.sramMatHashingWay# Means how many blocks we need to merge to form a key. For example: for 80 bit mat key we need 2 40 bit tcam block
    #     availableKeyBlock = math.floor(self.sramResource.availableSramBlocks/matKeySRAMBlockWidth) # if we need 3 blocks to form a mat key and we have 5 tcam block then we can accomodate only 1 block for the matkey
    #     accomodatableSRAMEntries = availableKeyBlock * self.sramResource.perMemoryBlockRowCount
    #     return  accomodatableSRAMEntries
    def isMatEntriesAccomodatableInSRAMBasedMATInThisStage(self,matKeyBitWidth, requiredMatEntries, hashingWay):
        isAccomodatable = False
        blockWidth, requiredSramBlocks = self.getMemoryBlockWidthAndBlockCountFromBitWidthAndRequiredNumberOfEntries(bitWidth=matKeyBitWidth,
                 memoryBlockBitwidth=self.sramResource.perMemoryBlockBitwidth,memoryBlockRowCount=self.sramResource.perMemoryBlockRowCount,
                 requiredNumberOfEntries=requiredMatEntries,hashingWay=1)
        requiredSramBlocks = requiredSramBlocks * hashingWay
        memoryPortWidthList = self.bitWidthToMemoryPortWidthConsumption(matKeyBitWidth, list(self.externResource.bitWidthToRegisterExternMap.keys()))
        totalMemoryPortWidth = sum(memoryPortWidthList)

        if(self.sramResource.availableSramBlocks >= requiredSramBlocks) and (self.sramResource.availableSramPortWidthForActionLoading >= totalMemoryPortWidth):
            isAccomodatable = True
        else:
            isAccomodatable = False
            print("The SRAM based MAT  requires total "+str(requiredMatEntries)+ "where each one is "+str(matKeyBitWidth)+"  bit wide. Which requires "+str(requiredSramBlocks)+" SRAM blocks.")
            print("But the stage can not  accomodatee them in SRAM. It have only "+str(self.sramResource.availableSramBlocks)+ " SRAM blocks.")
        return isAccomodatable

    def getTotalAccomodatableTCAMMatEntriesForGivenMatKeyBitwidth(self, matKeyBitWidth):
        matKeyBitWidth = self.convertMatKeyBitWidthLengthToTCAMMatKeyLength(matKeyBitWidth)
        matKeyTcamBlockWidth = math.ceil(matKeyBitWidth/self.tcamMatResource.perTcamBlockBitWidth) # Means how many blocks we need to merge to form a key. For example: for 80 bit mat key we need 2 40 bit tcam block
        availableKeyBlock = math.floor(self.tcamMatResource.availableTcamMatBlocks/matKeyTcamBlockWidth) # if we need 3 blocks to form a mat key and we have 5 tcam block then we can accomodate only 1 block for the matkey
        accomodatableTcamEntries = availableKeyBlock * self.tcamMatResource.perTcamBlockRowCount
        return accomodatableTcamEntries

    def isMatEntriesAccomodatableInTCAMBasedMATInThisStage(self,matKeyBitWidth, requiredMatEntries):
        if(matKeyBitWidth <= 0):
            return True #Because if there is no key to match nothing there is to embed
        accomodatableTcamEntries = self.getTotalAccomodatableTCAMMatEntriesForGivenMatKeyBitwidth(matKeyBitWidth)
        if(requiredMatEntries <= accomodatableTcamEntries):
            return True
        else:
            print("The TCAM based MAT  requires total "+str(requiredMatEntries)+ " entries where each one is "+str(matKeyBitWidth)+"  bit wide. ")
            print("But the stage can only accomodatee "+str(accomodatableTcamEntries))
            return False


    def allocateStatefulMemoerySetOnStage(self, p4ProgramGraph, pipelineID, statefulMemSet, hardware):
        # print("Test")
        isEmbeddable = True
        for regName in statefulMemSet:
            regBitwidth, regArrayLength = p4ProgramGraph.parsedP4Program.getRegisterArraysResourceRequirment(regName)
            if(self.isIndirectStatefulMemoryAccomodatable(regName, indirectStatefulMemoryBitwidth=regBitwidth, numberOfIndirectStatefulMemoryEntries=regArrayLength)):
                self.allocateSramBlockAndPortWidthForIndirectStatefulMemory(indirectStatefulMemoryBitwidth=regBitwidth, numberOfIndirectStatefulMemoryEntries=regArrayLength, indirectStatefulMemoryName=regName)
                isEmbeddable = True
            else:
                isEmbeddable = False
                print("The resource requirement for the indirect stateful memory: "+regName + " can not be fulfilled with the available resources in stage  "+str(self.stageIndex))
        return  isEmbeddable


    def allocateSramBlockForActionMemory(self,  actionEntryBitwidth, numberOfActionEntries):
        #TODO : record here which mat's stateful memory is using these blocks
        blockWidth, requiredSramBlocks = self.getMemoryBlockWidthAndBlockCountFromBitWidthAndRequiredNumberOfEntries(bitWidth=actionEntryBitwidth,
                     memoryBlockBitwidth=self.sramResource.perMemoryBlockBitwidth,memoryBlockRowCount=self.sramResource.perMemoryBlockRowCount,
                     requiredNumberOfEntries=numberOfActionEntries,hashingWay=1)
        memoryPortWidthList = self.bitWidthToMemoryPortWidthConsumption(actionEntryBitwidth, list(self.externResource.bitWidthToRegisterExternMap.keys()))
        totalMemoryPortWidth = sum(memoryPortWidthList)

        self.sramResource.availableSramBlocks = self.sramResource.availableSramBlocks - requiredSramBlocks
        self.sramResource.usedSramBlocks = self.sramResource.usedSramBlocks + requiredSramBlocks



    # def getTotalNumberOfAccomodatableActionEntriesForGivenActionEntryBitWidth(self, actionEntryBitwidth):
    #     # requiredActionMemoryBlockWidth = 0  # should ne set to some real large value
    #     # numberOfEntriesAccomodatableInBlockWidth = math.ceil(  self.actionMemoryBlockBitWidth/actionEntryBitwidth)
    #     # if(numberOfEntriesAccomodatableInBlockWidth>1): #indicates multiple entries are accomodatable in one sram cell
    #     #     pass
    #     #
    #
    #     requiredActionMemoryBlockWidth = math.ceil(actionEntryBitwidth / self.actionMemoryBlockBitWidth) # if we have an action entry with parameters width 120 bit and
    #     #the action memory block bidwidth is 80 then we need at least 2 blocks.
    #
    #     if(requiredActionMemoryBlockWidth <= self.availableActionMemoryBlockWidth) and (self.sramResource.availableSramBlocks >= requiredActionMemoryBlockWidth):
    #
    #         accomodatableActionBlocksInSRAM = math.floor(self.sramResource.availableSramBlocks/requiredActionMemoryBlockWidth)
    #         totalAccmmodatableEntries = accomodatableActionBlocksInSRAM * self.sramResource.perMemoryBlockRowCount
    #         return totalAccmmodatableEntries
    #     else:
    #         return 0

    def isActionMemoryAccomodatable(self, actionEntryBitwidth, numberOfActionEntries): #TODO: at this moment we are assuming that
        isAccomodatable = False
        blockWidth, requiredSramBlocks = self.getMemoryBlockWidthAndBlockCountFromBitWidthAndRequiredNumberOfEntries(bitWidth=actionEntryBitwidth,
                                             memoryBlockBitwidth=self.sramResource.perMemoryBlockBitwidth,memoryBlockRowCount=self.sramResource.perMemoryBlockRowCount,
                                             requiredNumberOfEntries=numberOfActionEntries,hashingWay=1)
        memoryPortWidthList = self.bitWidthToMemoryPortWidthConsumption(actionEntryBitwidth, list(self.externResource.bitWidthToRegisterExternMap.keys()))
        totalMemoryPortWidth = sum(memoryPortWidthList)

        if(self.sramResource.availableSramBlocks >= requiredSramBlocks) and (self.sramResource.availableSramPortWidthForActionLoading >= totalMemoryPortWidth):
            isAccomodatable = True
        else:
            isAccomodatable = False
        return isAccomodatable

    def allocateSramBlockAndPortWidthForIndirectStatefulMemory(self, indirectStatefulMemoryBitwidth, numberOfIndirectStatefulMemoryEntries, indirectStatefulMemoryName):
        #TODO : record here which stateful register array (indirectStatefulMemoryName) is using these blocks
        blockWidth, requiredSramBlocks = self.getMemoryBlockWidthAndBlockCountFromBitWidthAndRequiredNumberOfEntries(bitWidth=indirectStatefulMemoryBitwidth,
             memoryBlockBitwidth=self.sramResource.perMemoryBlockBitwidth,memoryBlockRowCount=self.sramResource.perMemoryBlockRowCount,
             requiredNumberOfEntries=numberOfIndirectStatefulMemoryEntries,hashingWay=1)
        memoryPortWidthList = self.bitWidthToMemoryPortWidthConsumption(indirectStatefulMemoryBitwidth, list(self.externResource.bitWidthToRegisterExternMap.keys()))
        totalMemoryPortWidth = sum(memoryPortWidthList)

        self.sramResource.availableSramBlocks = self.sramResource.availableSramBlocks - requiredSramBlocks
        self.sramResource.usedSramBlocks = self.sramResource.usedSramBlocks + requiredSramBlocks
        self.sramResource.availableSramPortWidthForActionExecution = self.sramResource.availableSramPortWidthForActionExecution - totalMemoryPortWidth
        self.sramResource.usedSramPortWidthForActionExecution = self.sramResource.usedSramPortWidthForActionExecution + totalMemoryPortWidth

    def getLargestPortWidth(self, bitWidth, hwPortWidthList):
        hwPortWidthList.sort(reverse=True)
        for portWidth in hwPortWidthList:
            if (portWidth <= bitWidth) :
                return portWidth
        waste = 999999999
        selectedPortWidth = None
        hwPortWidthList.sort()
        for portWidth in hwPortWidthList:
            if((portWidth - bitWidth)<waste ):
                waste =portWidth - bitWidth
                selectedPortWidth = portWidth
        if(selectedPortWidth != None):
            return  selectedPortWidth
        return -1



    # def  fillP4HeaderFieldWithPhvFields(self, bitWidth, portWidthList):
    #     originalHeaderFieldWidth = bitWidth
    #     phvFieldListForThisHeaderField = []
    #     while(bitWidth > 0):
    #         nearestSizePhVField = self.getLargestPortWidth(bitWidth, portWidthList)
    #
    #         if(nearestSizePhVField == -1):
    #             print("A header field of bitwidth "+str(originalHeaderFieldWidth)+" can not be allocated PHV fields in this system. Hence The P4 program can not be mapped tothis hardware. Extiting!!")
    #             exit(1)
    #         else:
    #             portWidthList[nearestSizePhVField]= portWidthList.get(nearestSizePhVField) - 1
    #             bitWidth = bitWidth - nearestSizePhVField
    #             phvFieldListForThisHeaderField.append(nearestSizePhVField)
    #
    #     return phvFieldListForThisHeaderField
    def bitWidthToMemoryPortWidthConsumption(self, bitWidth, hwPortWidthList):
        portWidthList = []
        bitWidth = self.externResource.getNearestIntegralMultipleOfLeaseWidthPort(bitWidth)
        while (bitWidth > 0):
            nearestPortWidth = self.getLargestPortWidth(bitWidth, hwPortWidthList)
            if(nearestPortWidth == -1):
                print("An Indirect Stateful memory  of bitwidth "+str(nearestPortWidth)+" can not be allocated using available memory port widths of this system. Hence The P4 program can not be mapped tothis hardware. Extiting!!")
                exit(1)
            else:
                bitWidth = bitWidth - nearestPortWidth
                portWidthList.append(nearestPortWidth)
        return portWidthList

    def getTotalNumberOfAccomodatableEntriesForGivenBitWidth(self, bitWidth, memoryBlockBitwidth,memoryBlockRowCount, hashingWay):
        if(bitWidth == 0) :
            return self.sramResource.availableSramBlocks * memoryBlockRowCount*memoryBlockBitwidth # Because if there is nothing to embed we can go for maximum. it doesn't matter . so we are considering only one bit
        if(bitWidth < memoryBlockBitwidth) and ((memoryBlockBitwidth/bitWidth)>=2): # implies at least two entries can be acomodated in one cell
            perMemoryBlockAccomodatableEntries = math.floor((memoryBlockBitwidth/bitWidth))
            totalAccomodatablePackedBlocks = math.floor((self.sramResource.availableSramBlocks)/hashingWay)
            return math.floor((totalAccomodatablePackedBlocks * perMemoryBlockAccomodatableEntries*memoryBlockRowCount))
        elif (bitWidth < memoryBlockBitwidth) and ((memoryBlockBitwidth/bitWidth)>=1): # implies only one entry can be fully accomodated in one cell, so we do packing here
            accomodatableEntriesInPackingFactorNumberOfCells = math.floor((CompilerConfigurations.PACKING_FACTOR *  memoryBlockBitwidth)/bitWidth)
            totalAccomodatablePackedBlocks = math.floor(self.sramResource.availableSramBlocks/(CompilerConfigurations.PACKING_FACTOR*hashingWay))
            return math.floor((accomodatableEntriesInPackingFactorNumberOfCells * totalAccomodatablePackedBlocks * memoryBlockRowCount))
        else: # implies one entry requires more than one sram block
            if (bitWidth <= CompilerConfigurations.PACKING_FACTOR*memoryBlockBitwidth):
                accomodatableEntriesInPackingFactorNumberOfCells = math.floor((CompilerConfigurations.PACKING_FACTOR *  memoryBlockBitwidth)/bitWidth)
                totalAccomodatablePackedBlocks = math.floor(self.sramResource.availableSramBlocks/(CompilerConfigurations.PACKING_FACTOR*hashingWay))
                return math.floor((accomodatableEntriesInPackingFactorNumberOfCells * totalAccomodatablePackedBlocks * memoryBlockRowCount))
            else: # this condtion applies when the bitwidth is more than the packed factor number of sram block's combined width
                blockWidth = math.ceil(bitWidth/memoryBlockBitwidth)
                totalAccomodatablePackedBlocks = math.floor(self.sramResource.availableSramBlocks/(blockWidth*hashingWay))
                return math.floor((totalAccomodatablePackedBlocks * memoryBlockRowCount))
    def getMemoryBlockWidthAndBlockCountFromBitWidthAndRequiredNumberOfEntries(self,bitWidth,memoryBlockBitwidth,memoryBlockRowCount,requiredNumberOfEntries,hashingWay):
        '''
        :param bitWidth:
        :param memoryBlockBitwidth:
        :param memoryBlockRowCount:
        :param requiredNumberOfEntries:
        :return: return only how many sram blocks are required
        '''
        if(bitWidth == 0) or (requiredNumberOfEntries == 0):
            return 0,0
        if(bitWidth < memoryBlockBitwidth) and ((memoryBlockBitwidth/bitWidth)>=2): # implies at least two entries can be acomodated in one cell
            perMemoryBlockAccomodatableEntries = math.floor((memoryBlockBitwidth/bitWidth))
            totalBlockRequired = math.ceil(requiredNumberOfEntries/(perMemoryBlockAccomodatableEntries*memoryBlockRowCount))
            #return 1, totalBlockRequired, perMemoryBlockAccomodatableEntries  # the entries requires totalBlockRequired of one block wide units and able to store perMemoryBlockAccomodatableEntries
            return 1, 1*totalBlockRequired*hashingWay
        elif (bitWidth < memoryBlockBitwidth) and ((memoryBlockBitwidth/bitWidth)>=1): # implies only one entry can be fully accomodated in one cell, so we do packing here
            if(requiredNumberOfEntries <= memoryBlockRowCount):
                # return 1, 1, requiredNumberOfEntries  # Because we allocate sram in total block granulairuty
                return 1,1*hashingWay
            else:
                accomodatableEntriesInPackingFactorNumberOfCells = math.floor((CompilerConfigurations.PACKING_FACTOR *  memoryBlockBitwidth)/bitWidth)
                totalBlockRequired = math.ceil(requiredNumberOfEntries/(accomodatableEntriesInPackingFactorNumberOfCells*memoryBlockRowCount))
                # return  CompilerConfigurations.PACKING_FACTOR, totalBlockRequired, accomodatableEntriesInPackingFactorNumberOfCells
                return CompilerConfigurations.PACKING_FACTOR, CompilerConfigurations.PACKING_FACTOR*totalBlockRequired*hashingWay
        else: # implies one entry requires more than one sram block
            if (bitWidth <= CompilerConfigurations.PACKING_FACTOR*memoryBlockBitwidth):
                accomodatableEntriesInPackingFactorNumberOfCells = math.floor((CompilerConfigurations.PACKING_FACTOR *  memoryBlockBitwidth)/bitWidth)
                totalBlockRequired = math.ceil(requiredNumberOfEntries/(accomodatableEntriesInPackingFactorNumberOfCells*memoryBlockRowCount))
                # return  CompilerConfigurations.PACKING_FACTOR,totalBlockRequired, accomodatableEntriesInPackingFactorNumberOfCells
                return CompilerConfigurations.PACKING_FACTOR, CompilerConfigurations.PACKING_FACTOR*totalBlockRequired*hashingWay
            else: # this condtion applies when the bitwidth is more than the packed factor number of sram block's combined width
                blockWidth = math.ceil(bitWidth/memoryBlockBitwidth)
                totalBlockRequired = math.ceil(requiredNumberOfEntries/memoryBlockRowCount)
                return blockWidth, blockWidth* totalBlockRequired*hashingWay

    def isIndirectStatefulMemoryAccomodatable(self, indirectStatefulMemoryName, indirectStatefulMemoryBitwidth, numberOfIndirectStatefulMemoryEntries): #TODO: at this moment we are assuming that
        isAccomodatable = False
        blockWidth, requiredSramBlocks = self.getMemoryBlockWidthAndBlockCountFromBitWidthAndRequiredNumberOfEntries(bitWidth=indirectStatefulMemoryBitwidth,
                         memoryBlockBitwidth=self.sramResource.perMemoryBlockBitwidth,memoryBlockRowCount=self.sramResource.perMemoryBlockRowCount,
                         requiredNumberOfEntries=numberOfIndirectStatefulMemoryEntries,hashingWay=1)
        memoryPortWidthList = self.bitWidthToMemoryPortWidthConsumption(indirectStatefulMemoryBitwidth, list(self.externResource.bitWidthToRegisterExternMap.keys()))
        totalMemoryPortWidth = sum(memoryPortWidthList)
        if(totalMemoryPortWidth <= self.sramResource.availableSramPortWidthForActionExecution) \
                and (self.sramResource.availableSramBlocks>= requiredSramBlocks):
            isAccomodatable =  True
        else:
            print("The indirect stateful memory entries for "+str(indirectStatefulMemoryName) +" can not be accomodated in the stage "+str(self.stageIndex))
            print("Becuase it requires "+str(requiredSramBlocks)+"  blocks in sram and it also requies "+str(totalMemoryPortWidth)+" bit capability read write from SRAM. Which is not available. ")
            isAccomodatable = False
        return isAccomodatable


    def isIndirectStatefulMemoryAccomodatableOld(self, indirectStatefulMemoryBitwidth, numberOfIndirectStatefulMemoryEntries): #TODO: at this moment we are assuming that
        requiredMemoryBlockWidth = math.ceil(indirectStatefulMemoryBitwidth / self.sramResource.perMemoryBlockBitwidth) # if we have an action entry with parameters width 120 bit and
        print("This fucntion calculates the requiremnt in wrong way. including its allocation method")
        #the action memory block bidwidth is 80 then we need at least 2 blocks.
        #This requiredActionMemoryBlockWidth will be always less than or equal to the number of availalb eaction memory block width. Assuming that we will precheck it
        if(requiredMemoryBlockWidth*self.sramResource.perMemoryBlockBitwidth <= self.sramResource.availableSramPortBitwidth) \
                and (self.sramResource.availableSramBlocks>= requiredMemoryBlockWidth):
            accomodatableIndirectStatefulMemoryBlocksInSRAM = math.floor(self.sramResource.availableSramBlocks/requiredMemoryBlockWidth)
            totalAccmmodatableEntries = accomodatableIndirectStatefulMemoryBlocksInSRAM * self.sramResource.perMemoryBlockRowCount
            if(accomodatableIndirectStatefulMemoryBlocksInSRAM >0) and (numberOfIndirectStatefulMemoryEntries <= totalAccmmodatableEntries):
                return True
        else:
            print("The action entries can not be accomodated in this stage. Becuase the reqruired amount of resource is not available")
            exit(1)
        return False

    def allocateMatNodeOverTCAMMatWithOutParam(self, matNode,pipelineID):
        self.allocateTCAMMatKeyCrossbarBitwidth(matNode.matKeyBitWidth)
        #For TCAM all tcam blocks are only used for MATCHing therefore allocating a tcam block automatically modifies the block count.
        #However in the case of sram this is not the case
        self.allocateMatEntriesOverTCAMBasedMATSinSingleStage(matNode.matKeyBitWidth, matNode.getRequiredNumberOfMatEntries()) # This embeds both match-key and tables and entries in one stage
        self.allocateActionCrossbarBitwidth(matNode.getMaxActionCrossbarBitwidthRequiredByAnyAction())
        self.allocateSramBlockForActionMemory(actionEntryBitwidth = matNode.getMaxBitwidthOfActionParameter(), numberOfActionEntries= matNode.getRequiredNumberOfActionEntries())
        self.allocateActionMemoryPortWidth(matNode.getMaxActionCrossbarBitwidthRequiredByAnyAction())
        #TODO need to allocate direct stateful memories here
        self.listOfLogicalTableMappedToThisStage.get(pipelineID).append(matNode)

    def allocateMatNodeOverTCAMMat(self, matNode, numberOfMatEntriesToBeAllocated, numberOfActionEntriesToBeAllocated,pipelineID):
        self.allocateTCAMMatKeyCrossbarBitwidth(matNode.matKeyBitWidth)
        self.allocateMatEntriesOverTCAMBasedMATSinSingleStage(matNode.matKeyBitWidth, numberOfMatEntriesToBeAllocated) # This embeds both match-key and tables and entries in one stage
        self.allocateActionCrossbarBitwidth(matNode.getMaxActionCrossbarBitwidthRequiredByAnyAction())
        self.allocateSramBlockForActionMemory(actionEntryBitwidth = matNode.getMaxBitwidthOfActionParameter(), numberOfActionEntries= numberOfActionEntriesToBeAllocated)
        self.allocateActionMemoryPortWidth(matNode.getMaxActionCrossbarBitwidthRequiredByAnyAction())
        self.listOfLogicalTableMappedToThisStage.get(pipelineID).append(matNode)

    def allocateMatNodeOverSRAMMatWithoutParam(self, matNode,pipelineID):
        self.allocateSRAMMatKeyCrossbarBitwidth(matNode.matKeyBitWidth)
        #For TCAM all tcam blocks are only used for MATCHing therefore allocating a tcam block automatically modifies the block count.
        #However in the case of sram this is not the case. In sram based mat we can only use 8 SRAM based MAT (in bosshart paper), But there are 106 sram blocks,
        #Therefore unlike tcam based mat, in sram based mat we need to explicitily keep track of the number of available SRAM based mat blocks.
        self.allocateSRAMMatBlocks(self.convertMatKeyBitWidthLengthToSRAMMatBlockCount(matNode.matKeyBitWidth))
        self.allocateMatEntriesOverSRAMBasedMATSInSingleStage(matNode.matKeyBitWidth, matNode.getRequiredNumberOfMatEntries()) # This embeds both match-key and tables and entries in one stage
        self.allocateActionCrossbarBitwidth(matNode.getMaxActionCrossbarBitwidthRequiredByAnyAction())
        self.allocateSramBlockForActionMemory(actionEntryBitwidth = matNode.getMaxBitwidthOfActionParameter(), numberOfActionEntries= matNode.getRequiredNumberOfActionEntries())
        self.allocateActionMemoryPortWidth(matNode.getMaxActionCrossbarBitwidthRequiredByAnyAction())
        #TODO need to allocate direct stateful memories here
        self.listOfLogicalTableMappedToThisStage.get(pipelineID).append(matNode)
    def allocateMatNodeOverSRAMMat(self, matNode, numberOfMatEntriesToBeAllocated, numberOfActionEntriesToBeAllocated,pipelineID):
        self.allocateSRAMMatKeyCrossbarBitwidth(matNode.matKeyBitWidth)
        #For TCAM all tcam blocks are only used for MATCHing therefore allocating a tcam block automatically modifies the block count.
        #However in the case of sram this is not the case. In sram based mat we can only use 8 SRAM based MAT (in bosshart paper), But there are 106 sram blocks,
        #Therefore unlike tcam based mat, in sram based mat we need to explicitily keep track of the number of available SRAM based mat blocks.
        self.allocateSRAMMatBlocks(self.convertMatKeyBitWidthLengthToSRAMMatBlockCount(matNode.matKeyBitWidth))
        self.allocateMatEntriesOverSRAMBasedMATSInSingleStage(matNode.matKeyBitWidth, numberOfMatEntriesToBeAllocated,self.sramMatResource.sramMatHashingWay) # This embeds both match-key and tables and entries in one stage
        self.allocateActionCrossbarBitwidth(matNode.getMaxActionCrossbarBitwidthRequiredByAnyAction())
        self.allocateSramBlockForActionMemory(actionEntryBitwidth = matNode.getMaxBitwidthOfActionParameter(), numberOfActionEntries= numberOfActionEntriesToBeAllocated)
        self.allocateActionMemoryPortWidth(matNode.getMaxActionCrossbarBitwidthRequiredByAnyAction())
        self.listOfLogicalTableMappedToThisStage.get(pipelineID).append(matNode)
        # print("Test")

    def isMatNodeEmbeddableOnSRAMMatBlocks(self, matNode,maxActionCrossbarBitwidth):
        isEmbeddable = False
        #For TCAM all tcam blocks are only used for MATCHing therefore allocating a tcam block automatically modifies the block count.
        #However in the case of sram this is not the case. In sram based mat we can only use 8 SRAM based MAT (in bosshart paper), But there are 106 sram blocks,
        #Therefore unlike tcam based mat, in sram based mat we need to explicitily keep track of the number of available SRAM based mat blocks.
        if(self.convertMatKeyBitWidthLengthToSRAMMatBlockCount(matNode.matKeyBitWidth) <= self.getAvailableSRAMMatKeyBlockCount()) \
                and (matNode.matKeyBitWidth <= self.getAvailableSRAMMatKeyCrossbarBitwidth()):
            isEmbeddable=True
        else:
            print("The mat node: "+matNode.name+" requires total "+str(matNode.totalKeysTobeMatched)+" match keys and their bitwidth is "+str(self.convertMatKeyBitWidthLengthToSRAMMatKeyLength(matNode.matKeyBitWidth)))
            print("But the SRAM based MATS at stage " + str(self.stageIndex) +" can accomodate  bttwidth for matkey: " + str(self.getAvailableTCAMMatKeyCrossbarBitwidth()))
            isEmbeddable = False
        if(self.isMatEntriesAccomodatableInSRAMBasedMATInThisStage(self.convertMatKeyBitWidthLengthToSRAMMatKeyLength(matNode.matKeyBitWidth), matNode.getRequiredNumberOfMatEntries(), self.sramMatResource.sramMatHashingWay)):
            isEmbeddable=True
            self.allocateMatEntriesOverSRAMBasedMATSInSingleStage(self.convertMatKeyBitWidthLengthToSRAMMatKeyLength(matNode.matKeyBitWidth), matNode.getRequiredNumberOfMatEntries())
            if(self.isActionMemoryAccomodatable(actionEntryBitwidth=matNode.getMaxBitwidthOfActionParameter(), numberOfActionEntries=matNode.getRequiredNumberOfActionEntries())):
                isEmbeddable= True
                self.deAllocateMatEntriesOverSRAMBasedMATSInSingleStage(self.convertMatKeyBitWidthLengthToSRAMMatKeyLength(matNode.matKeyBitWidth), matNode.getRequiredNumberOfMatEntries())
            else:
                print("The SRAM based mat node: "+matNode.name+" requires total "+str(matNode.getRequiredNumberOfActionEntries())+" action entries for the SRAM based table.")
                print("But the avialble resource at stage is unable to embed these action entires in SRAM.")
                self.deAllocateMatEntriesOverSRAMBasedMATSInSingleStage(self.convertMatKeyBitWidthLengthToSRAMMatKeyLength(matNode.matKeyBitWidth), matNode.getRequiredNumberOfMatEntries())
                isEmbeddable=False
            if (self.availableActionCrossbarBitWidth>= maxActionCrossbarBitwidth):
                isEmbeddable = True
            else:
                isEmbeddable = False
                print("The mat node: "+matNode.name+" requires total "+str(maxActionCrossbarBitwidth)+" action crossbar width for SRAM based MAT. however only "+str(self.availableActionCrossbarBitWidth)+" bit width is available. Can not accomodate in stage"+str(self.stageIndex))
        else:
            print("The mat node: "+matNode.name+" requires total "+str(matNode.getRequiredNumberOfMatEntries())+" match entries in the SRAM based table")
            print("But the SRAM at stage is not enough")
            isEmbeddable = False

        #TODO: we need to handle indirect stateful memory handling here
        return isEmbeddable




    def isMatNodeEmbeddableOnTCAMMatBlocks(self, matNode,maxActionCrossbarBitwidth,maxActionMemoryBitwidth):

        # check whther, the key bit width and lengths are within available bitwdth and range
        # Then check, number of entries is accomodatable or not
        # then check total action memory is accomodatable or not
        isEmbeddable = False
        #TODO : this is with the assumption that, sum of match field width of the tcam mats is equal to the width of the tcam mat crossbar. Because if crossbar is smaller then we can not provide a field to tcam
        if ((self.convertMatKeyBitWidthLengthToTCAMMatBlockCount(matNode.matKeyBitWidth) <= self.getAvailableTCAMMatKeyBlockCount()) and\
            (matNode.matKeyBitWidth <= self.getAvailableTCAMMatKeyCrossbarBitwidth())):
            isEmbeddable=True # The key count and bit width is conformant with available resource
        else:
            print("The mat node: "+matNode.name+" requires total "+str(matNode.totalKeysTobeMatched)+" match keys and their bitwidth is "+str(self.convertMatKeyBitWidthLengthToTCAMMatKeyLength(matNode.matKeyBitWidth)))
            print("But the TCAM at stage " + str(self.stageIndex) +" can accomodate  MAT keys bttwidth of " + str(self.getAvailableTCAMMatKeyCrossbarBitwidth())+" bit only. So not embeddable")
            isEmbeddable = False
        if(self.isMatEntriesAccomodatableInTCAMBasedMATInThisStage(self.convertMatKeyBitWidthLengthToTCAMMatKeyLength(matNode.matKeyBitWidth), matNode.getRequiredNumberOfMatEntries())):
            isEmbeddable=True
        else:
            print("The mat node: "+matNode.name+" requires total "+str(matNode.getRequiredNumberOfMatEntries())+" match entries in the TCAM based table")
            print("But the TCAM at stage is not enough")
            isEmbeddable = False
        #The isActionMemoryAccomodatable checks both action entry and meomry port width required for the action entries.
        if(self.isActionMemoryAccomodatable(actionEntryBitwidth=matNode.getMaxBitwidthOfActionParameter(), numberOfActionEntries=matNode.getRequiredNumberOfActionEntries())):
            isEmbeddable= True
        else:
            print("The mat node: "+matNode.name+" requires total "+str(matNode.getRequiredNumberOfActionEntries())+" action entries for the TCAM based table.")
            print("But the avialble resource at stage is unable to embed these action entires in sram.")
            isEmbeddable=False
        if (self.availableActionCrossbarBitWidth>= maxActionCrossbarBitwidth):
            isEmbeddable = True
        else:
            isEmbeddable = False
            print("The mat node: "+matNode.name+" requires total "+str(maxActionCrossbarBitwidth)+" action crossbar width for TCAM Based MAR.however only "+str(self.availableActionCrossbarBitWidth)+" bit width is available. Can not accomodate in stage"+str(self.stageIndex))
        #TODO: we need to handle indirect stateful memory handling here

        return isEmbeddable



    def isMatNodeListEmbeddableOnThisStage(self, p4ProgramGraph,pipelineID, matNodeList,hardware):
        ''' All the matnodes in this list are actually the nodes who uses a specific set of stateful memoery. therefore they are executed only one at a single cycle.
        Therefore we will take the maximum action parameter bitwith of these tables'''
        '''This function returns true if all the MAt nodes in matNodeList is embaddable over the stageHardwareResource. If true it also allocates resources in stageHardwareResource.
        Else it returns False.'''
        isEmbeddable = True
        #The follwoing loop claculates Each mat node's resource requirement and saves in the same object.
        maxActionMemoryBitwidth = 0
        maxActionCrossbarBitwidth = 0
        for matNode in matNodeList:
            #Calculate individual resource consumption of rach mat node
            p4ProgramGraph.parsedP4Program.computeMatchActionResourceRequirementForMatNode(matNode, p4ProgramGraph, pipelineID)
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
        for matNode in matNodeList: # The matnode list already sorted and TCAM based tables will come first. So they will be embedded at first
            p4ProgramGraph.parsedP4Program.computeMatchActionResourceRequirementForMatNode(matNode, p4ProgramGraph, pipelineID) # Though redundant but not harm in calling
            if(matNode.originalP4node.match_type.value != MatchType.EXACT):
                #try to embed the matnode in tcam
                if(self.isMatNodeEmbeddableOnTCAMMatBlocks(matNode,maxActionCrossbarBitwidth,maxActionMemoryBitwidth)):
                    self.allocateMatNodeOverTCAMMatWithOutParam(matNode,pipelineID) #TODO : this need to include both action memory and direct statefule memories
                else:
                    isEmbeddable = False
            else:
                if(self.isMatNodeEmbeddableOnSRAMMatBlocks(matNode)):
                    self.allocateMatNodeOverSRAMMatWithoutParam(matNode,pipelineID) #TODO : this need to include both action memory and direct statefule memories #------------- check from here. uoto before is done
                elif(self.isMatNodeEmbeddableOnTCAMMatBlocks(matNode)):
                    self.allocateMatNodeOverTCAMMatWithOutParam(matNode,pipelineID)
                else:
                    isEmbeddable = False
        # if(isEmbeddable == True):
        #     self.allocateActionMemoryPortWidth(maxActionMemoryBitwidth)

        return isEmbeddable

            # mat key bidwidth , mat key count, mat entries -- are these things embeddable?
            # then action field count, action crossbar bitwidth, then action memory -- are these thing feasible

        # if total mat entriy rewuirement is okay, if total mat entry fields count and crossbar bitwidth requirement is okay ,
        # total sram requiree dby actions is okay , the action crossbar bitwidth is okay
        #
        # then the set of nodes are embeddable. otherwise not.
        #
        # writre a seperate function for each one of them and that will return true . then write a predicate combining all of them.
        # then do the actual allocations.










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
        # self.availableSramMatFields = sram_mat_resources.sram_mat_field_count
        # self.usedSramMatFields = 0
        self.availableSramMatCrossbarBitwidth = sram_mat_resources.match_crossbar_bit_width
        self.usedSramMatCrossbarBitwidth = 0
        self.availableSramMatBlocks = sram_mat_resources.block_count
        self.usedSramMatBlocks = 0
        self.supportedMatchTypes = sram_mat_resources.supported_match_types
        self.sramMatHashingWay = sram_mat_resources.per_sram_mat_block_spec.hashing_way
        self.perSramMatBitWidth = sram_mat_resources.per_sram_mat_block_spec.sram_bit_width
        pass
    def printAvailableResourceStatistics(self):
        print("\tSRAM MAT Resources")
        print("\t\tavailableSramMatCrossbarBitwidth is: "+str(self.availableSramMatCrossbarBitwidth)+" usedSramMatCrossbarBitwidth is : "+str(self.usedSramMatCrossbarBitwidth))
        print("\t\tavailableSramMatBlocks is: "+str(self.availableSramMatBlocks)+" usedSramMatBlocks is : "+str(self.usedSramMatBlocks))



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
        # self.availableTcamMatFields = tcam_mat_resources.tcam_mat_field_count
        # self.usedTcamMatFields = 0
        self.availableTcamMatCrossbarBitwidth = tcam_mat_resources.match_crossbar_bit_width
        self.usedTcamMatCrossbarBitwidth = 0
        self.availableTcamMatBlocks = tcam_mat_resources.block_count
        self.usedTcamMatBlocks = 0
        self.supportedMatchTypes = tcam_mat_resources.supported_match_types
        self.perTcamBlockBitWidth = tcam_mat_resources.per_tcam_mat_block_spec.tcam_bit_width
        self.perTcamBlockRowCount = tcam_mat_resources.per_tcam_mat_block_spec.tcam_row_count
        pass
    def printAvailableResourceStatistics(self):
        print("\tTCAM MAT Resources")
        print("\t\tavailableTcamMatCrossbarBitwidth is: "+str(self.availableTcamMatCrossbarBitwidth)+" usedTcamMatCrossbarBitwidth is : "+str(self.usedTcamMatCrossbarBitwidth))
        print("\t\tavailableTcamMatBlocks is: "+str(self.availableTcamMatBlocks)+" usedTcamMatBlocks is : "+str(self.usedTcamMatBlocks))


class SRAMResource:

    def __init__(self,sram_resources, rmtHWSpec):
        self.unprocessedSramResourceSpec = sram_resources
        self.availableSramPorts = sram_resources.memory_port_count
        self.availableSramPortWidthForActionLoading= sram_resources.memory_port_count * sram_resources.memory_port_width
        self.usedSramPortWidthForActionLoading = 0
        self.availableSramPortWidthForActionExecution = sram_resources.memory_port_count * sram_resources.memory_port_width
        self.usedSramPortWidthForActionExecution = 0
        self.availableSramBlocks = sram_resources.memory_block_count
        self.usedSramBlocks = 0
        # self.availalbeSramBlockBitwidth = sram_resources.memory_block_bit_width
        # self.usedSramBlockBitwidth=0
        # self.availableSramRows = self.availableSramBlocks * sram_resources.memoroy_block_row_count
        # self.usedSramRows=0
        self.perMemoryBlockRowCount = sram_resources.memoroy_block_row_count
        self.perMemoryBlockBitwidth = sram_resources.memory_port_width
        pass

    def printAvailableResourceStatistics(self):
        print("\tSRAM Resources")
        print("\t\tavailableSramPortWidthForActionLoading is: "+str(self.availableSramPortWidthForActionLoading)+" usedSramPortWidthForActionLoading is : "+str(self.usedSramPortWidthForActionLoading))
        print("\t\tavailableSramPortWidthForActionExecution is: "+str(self.availableSramPortWidthForActionExecution)+" usedSramPortWidthForActionExecution is : "+str(self.usedSramPortWidthForActionExecution))
        print("\t\tavailableSramBlocks is: "+str(self.availableSramBlocks)+" usedSramBlocks is : "+str(self.usedSramBlocks))
        # print("availableSramBlocks is: "+str(self.availableSramBlocks)+" usedSramBlocks is : "+str(self.usedSramBlocks))
        # print("availableSramBlocks is: "+str(self.availableSramBlocks)+" usedSramBlocks is : "+str(self.usedSramBlocks))

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


class RegisterExtern:

    def __init__(self, regExSpec):
        self.rawSpec = regExSpec
        pass

class ExternResource:

    # Assume we have register read extern. And according to the hardware we can acccomodate 8 read in one stage. Then
    # we have 8*80 bit read cpability (assuming 80 bitwide memory port). Now assume for a spceific action we need
    # 512 bit read for ingress and 108 bit for egress. So whe we are emnedding 512 bit read for ingress then we need to maintain
    # that in this stage we can read 640 bit in total among them 512 bit are used for ingress and 108 bit for egress.

    def __init__(self,externResourcesDescription, rmtHWSpec):
        self.registerExternList = []
        self.bitWidthToRegisterExternMap = {}
        if(externResourcesDescription.register_extern != None):
            for reg_ex in externResourcesDescription.register_extern:
                regExSpec = rmtHWSpec.nameToExternInstructionMap.get(reg_ex.name)
                if(regExSpec==None):
                    print("Severe Error. Specification for "+str(reg_ex.name)+" not  found in instruction set. Exiting")
                    exit(1)
                self.registerExternList.append(RegisterExtern(regExSpec))
                self.bitWidthToRegisterExternMap[regExSpec.extern_bitwidth] = regExSpec

    def getNearestIntegralMultipleOfLeaseWidthPort(self, bitWidth):
        portWidthList = list(self.bitWidthToRegisterExternMap.keys())
        portWidthList.sort()
        minWidthList = portWidthList[0]
        c = math.ceil(bitWidth/minWidthList)
        return c*minWidthList
        # for externRsrcDes in externResourcesDescription:
        #     # print(externRsrcDes)
        #     # if (externRsrcDes.name in )
        #     instructionSpec = rmtHWSpec.nameToExternInstructionMap.get(externRsrcDes.name)
        #     if(instructionSpec == None):
        #         logger.info("Instruction specification for instruction type: "+externRsrcDes.name+ " is not found in hardware specification. Exiting")
        #         print("Instruction specification for instruction type: "+externRsrcDes.name+ " is not found in hardware specification. Exiting")
        #         exit(1)
        #     externInstructionBitwidth = instructionSpec.extern_bitwidth
        #     if(self.availableBitwidthToRegisterInstructionMap.get(externInstructionBitwidth) == None):
        #         self.availableBitwidthToRegisterInstructionMap[externInstructionBitwidth] = []
        #     for i in range(0, externRsrcDes.count):
        #         bitWiseInstructionList = self.availableBitwidthToRegisterInstructionMap.get(externInstructionBitwidth)
        #         bitWiseInstructionList.append(instructionSpec)
        #         self.availableBitwidthToRegisterInstructionMap[externInstructionBitwidth] = bitWiseInstructionList