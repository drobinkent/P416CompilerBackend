from DependencyAnlyzer.P4ProgramGraph import P4ProgramGraph
from P416JsonParser import ParsedP416ProgramForV1ModelArchitecture
from P4ProgramParserFactory import P4ProgramParserFactory
from RMTHardwareSimulator import RMTHardwareFactory
from util import loadP416JsonUsingAutoGeneratedJsonParser

#64, 96, and 64 words of 8, 16, and 32b
p4ProgramParserFactory = P4ProgramParserFactory()
hw = RMTHardwareFactory.createRmtHardware(headerFieldSpecs= {8:64,16:96,32:64},rmtHardwaRemodel="RMT_V1")
p4program = p4ProgramParserFactory.getParsedP4Program(p4JsonFile="../Resources/spine.json",p4VersionAndArchitecture="P416_V1_Model")
p4ProgramGraph = P4ProgramGraph(p4program)
p4ProgramGraph.loadPipelines()
headerFieldSpecsInP4Program = p4ProgramGraph.headeranalyzer()



