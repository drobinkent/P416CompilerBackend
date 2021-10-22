import logging

import ConfigurationConstants as ConfConst
from P4ProgramParser.P416JsonParser import ParsedP416ProgramForV1ModelArchitecture
from utils import JsonParserUtil

logger = logging.getLogger('MAIN')
hdlr = logging.FileHandler(ConfConst.LOG_FILE_PATH )
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)

class P4ProgramParserFactory:


    def getParsedP4Program(self, p4JsonFile, p4VersionAndArchitecture="P416_V1_Model"):
        rawJsonObjects =  JsonParserUtil.loadRowJsonAsDictFromFile(p4JsonFile)
        if((rawJsonObjects == None) ):
            logger.info("Failed to load P4 Json :"+p4JsonFile+" Exiting!!!")
            exit(1)

        if(p4VersionAndArchitecture=="P416_V1_Model"):
            returnValue = ParsedP416ProgramForV1ModelArchitecture.from_dict(rawJsonObjects)
            return returnValue
        else:
            print("P4 version and architecture :"+ p4VersionAndArchitecture+"  not supported")