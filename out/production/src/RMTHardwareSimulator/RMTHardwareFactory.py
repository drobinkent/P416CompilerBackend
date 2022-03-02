from RMTHardwareSimulator.RMTV1ModelHardware import RMTV1ModelHardware



def createRmtHardware( rmtHardwaRemodelName, instructionSetConfigurationJsonFile, hardwareSpecConfigurationJsonFile):
    if(rmtHardwaRemodelName=="RMT_V1"):
        hw = RMTV1ModelHardware(rmtHardwaRemodelName, instructionSetConfigurationJsonFile, hardwareSpecConfigurationJsonFile)
        # print(hw.pakcetHeaderVectorFieldSizeVsCountMap)
        return hw
    else:
        print("Hardware model : "+rmtHardwaRemodelName+" is still not supported. Add support for this")

