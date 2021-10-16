import logging
from enum import Enum
import sys

from DependencyAnlyzer.DefinitionConstants import PipelineID
from DependencyAnlyzer.PipelineGraph import PipelineGraph

sys.path.append("..")
import ConfigurationConstants as confConst



import networkx as nx
logger = logging.getLogger('P4ProgramGraph')
hdlr = logging.FileHandler(confConst.LOG_FILE_PATH )
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)



class P4ProgramGraph:
    def __init__(self, parsedP4Program):
        '''
        This program loads the parsed Json object representation of a P4 program into a graph
        :param p4ProgramParserJsonObject: this is the object that is generated by parsing the P4 json for bmv2.
        '''
        self.pipelineIdToPipelineGraphMap = {}
        self.pipelineIdToPipelineMap = {}
        self.parsedP4Program = parsedP4Program

    def loadPipelines(self):
        logger.info("Loading pipelines")
        if (len(self.parsedP4Program.pipelines) <= 0):
            logger.info("There is no pipelines found in the parsed Json representation. Exiting")
            exit(0)
        for pipeline in self.parsedP4Program.pipelines:
            if(pipeline.name == PipelineID.INGRESS_PIPELINE.value):
                newPipelineGraph = PipelineGraph(pipelineID=PipelineID.INGRESS_PIPELINE, pipeline = pipeline, actions= self.parsedP4Program.actions)
                self.pipelineIdToPipelineGraphMap[PipelineID.INGRESS_PIPELINE] = newPipelineGraph
                self.pipelineIdToPipelineMap[PipelineID.INGRESS_PIPELINE] = pipeline
                # newPipelineGraph.loadNodes()
            if(pipeline.name == PipelineID.EGRESS_PIPELINE.value):
                newPipelineGraph = PipelineGraph(pipelineID=PipelineID.EGRESS_PIPELINE, pipeline = pipeline, actions= self.parsedP4Program.actions)
                self.pipelineIdToPipelineGraphMap[PipelineID.EGRESS_PIPELINE] = newPipelineGraph
                self.pipelineIdToPipelineMap[PipelineID.EGRESS_PIPELINE] = pipeline
                # newPipelineGraph.loadNodes()

    def headeranalyzer(self):
        print(self.parsedP4Program.nameToHeaderTypeObjectMap)
        self.parsedP4Program.getTotalHeaderLength()
        print("\n\n Ingress stage header analysis")
        fullListOfHeaderFieldsUsedInThePipeline =self.pipelineIdToPipelineGraphMap.get(PipelineID.INGRESS_PIPELINE).headeranalyzerForSinglePipeline()
        self.getTotalHeaderLengthForHeaderFieldList(fullListOfHeaderFieldsUsedInThePipeline)
        bitWidthByHeadercountForIngress = self.getHeaderCountByBitWidthForHeaderFieldList(fullListOfHeaderFieldsUsedInThePipeline)
        print("Bitwdith wise header count is ",bitWidthByHeadercountForIngress)
        print("\n\n Egress stage header analysis")
        fullListOfHeaderFieldsUsedInThePipeline = self.pipelineIdToPipelineGraphMap.get(PipelineID.EGRESS_PIPELINE).headeranalyzerForSinglePipeline()
        self.getTotalHeaderLengthForHeaderFieldList(fullListOfHeaderFieldsUsedInThePipeline)
        bitWidthByHeadercountForEgress = self.getHeaderCountByBitWidthForHeaderFieldList(fullListOfHeaderFieldsUsedInThePipeline)
        print("Bitwdith wise header count is ",bitWidthByHeadercountForEgress)
        mapToAppend = {}
        for k in bitWidthByHeadercountForEgress.keys():
            ingressObj = bitWidthByHeadercountForIngress.get(k)
            if(ingressObj == None):
                mapToAppend[k] = bitWidthByHeadercountForEgress.get(k)
            else:
                bitWidthByHeadercountForEgress[k] = bitWidthByHeadercountForEgress.get(k) + ingressObj
        for k in mapToAppend.keys():
            bitWidthByHeadercountForEgress[k] = mapToAppend.get(k)
        print("Bitwdith wise header count is ",bitWidthByHeadercountForEgress)
        return  bitWidthByHeadercountForEgress



    def getTotalHeaderLengthForHeaderFieldList(self, headerFieldList):
        total = 0
        for k in headerFieldList:
            hf = self.parsedP4Program.nameToHeaderTypeObjectMap.get(k)
            if (hf==None):
                flag = False
                for headerStruct in self.parsedP4Program.headers:
                    if(headerStruct.name == k):
                        flag = True
                        break
                    else:
                        flag = False
                if (flag == False):
                    logger.info("Field not found in map . The field is "+str(k))
            else:
                total = total + int(self.parsedP4Program.nameToHeaderTypeObjectMap.get(k).bitWidth)
        print("Total header legnth for given headerfield list is ",total)
        return total

    def getHeaderCountByBitWidthForHeaderFieldList(self, headerFieldList):
        total = 0
        bitWidthByHeadercount = {}
        for k in headerFieldList:
            hf = self.parsedP4Program.nameToHeaderTypeObjectMap.get(k)
            if (hf==None):
                logger.info("Field not found in map . The field is "+str(k))
            else:
                if(bitWidthByHeadercount.get(self.parsedP4Program.nameToHeaderTypeObjectMap.get(k).bitWidth) == None):
                    bitWidthByHeadercount[self.parsedP4Program.nameToHeaderTypeObjectMap.get(k).bitWidth] = 1
                else:
                    bitWidthByHeadercount[self.parsedP4Program.nameToHeaderTypeObjectMap.get(k).bitWidth] = bitWidthByHeadercount[self.parsedP4Program.nameToHeaderTypeObjectMap.get(k).bitWidth] + 1
        return bitWidthByHeadercount
