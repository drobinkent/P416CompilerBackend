import logging
from enum import Enum
import sys


sys.path.append("..")
import ConfigurationConstants as confConst



import networkx as nx
logger = logging.getLogger('DependencyGraphBuilder')
hdlr = logging.FileHandler(confConst.LOG_FILE_PATH )
hdlr.setLevel(logging.INFO)
formatter = logging.Formatter('[%(asctime)s] p%(process)s {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s','%m-%d %H:%M:%S')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logging.StreamHandler(stream=None)
logger.setLevel(logging.INFO)



class Dependency:
    def __init__(self, node1, node2, dependencyType):
        self.node1 = node1
        self.node2 = node2
        self.dependencyType = dependencyType






