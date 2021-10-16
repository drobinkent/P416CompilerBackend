from RMTHardwareSimulator.RMTHardwareSpecs import RMTV1ModelHardware



def createRmtHardware(headerFieldSpecs, rmtHardwaRemodel):
    if(rmtHardwaRemodel=="RMT_V1"):
        hw = RMTV1ModelHardware(headerFieldSpecs = headerFieldSpecs)
        # print(hw.pakcetHeaderVectorFieldSizeVsCountMap)
        return hw
    else:
        print("Hardware model : "+rmtHardwaRemodel+" is still not supported. Add support for this")

