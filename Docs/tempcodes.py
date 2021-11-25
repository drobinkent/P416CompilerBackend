if(self.isMatNodeEmbeddableOnThisStage(p4ProgramGraph,pipelineID, matNode,hardware, deepCopiedResourcesOfStage)):
    hardware.stageWiseResources[startingPhyicalStageIndex]= deepCopiedResourcesOfStage
    deepCopiedResourcesOfStage = copy.deepcopy(hardware.stageWiseResources.get(startingPhyicalStageIndex))
else:
    startingPhyicalStageIndex = startingPhyicalStageIndex + 1
    hwStage = hardware.stageWiseResources.get(startingPhyicalStageIndex)
    if(hwStage == None):
        print("The program already used "+str(startingPhyicalStageIndex.stageIndex-1)+" stages of the hardware. There are no more hardware available")
        exit(1)
    else:
        pass