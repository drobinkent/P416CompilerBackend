import sys
sys.path.append("..") # Adds higher directory to python modules path.
from P4ProgramParser import P416JsonParser
from utils import JsonParserUtil
import logging
import ConfigurationConstants as ConfConst
logger = logging.getLogger('MAIN')
hdlr = logging.FileHandler(ConfConst.LOG_FILE_PATH )
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)

def loadP416JsonUsingAutoGeneratedJsonParser(file_path,hw):
    rawJsonObjects =  JsonParserUtil.loadRowJsonAsDictFromFile(file_path)
    if((rawJsonObjects == None) ):
        logger.info("Failed to load P4 Json :"+file_path+" Exiting!!!")
        exit(1)
    prorgam = P416JsonParser.ParsedP416Program_from_dict(rawJsonObjects)
    prorgam.buildHeaderVector(hw)
    logger.info(prorgam)
    return prorgam