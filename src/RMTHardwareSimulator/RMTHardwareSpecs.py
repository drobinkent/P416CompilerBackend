

class HeaderFieldDefinition:

    def __init__(self,headerFieldWidth, count):
        self.headerFieldWidth = headerFieldWidth
        self.count = count

class RMTV1ModelHardware:

    def __init__(self, headerFieldSpecs): # headerFieldSpecs map will contain "header field width" : "count" data .
        self.pakcetHeaderVectorFieldSizeVsCountMap= headerFieldSpecs

    def getPakcetHeaderVectorFieldSizeVsCountMap(self):
        return self.pakcetHeaderVectorFieldSizeVsCountMap
