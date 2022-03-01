#!/usr/bin/env python

"""A header node for use in a DAG"""
import sys
sys.path.append("..")
sys.path.append(".")
import ParserMapper.ParserMapperHeader
from ParserMapper.HeaderLib import getHeaderLengths
from ParserMapper.DAGNode import DAGNode

class HeaderNode(DAGNode):
    """Header node for use in a DAG"""
    
    def __init__(self, hdr, inst):
        super(HeaderNode, self).__init__(hdr, inst, min(getHeaderLengths(hdr)[1]) / 8)
        self._processLen = None

    def cmp(self, y):
        if self.hdr.name ==y.hdr.name :
            return 0
        elif self.hdr.name > y.hdr.name :
            return 1
        else:
            return 0
    def __lt__(self, y ):
        return self.hdr.name < y.hdr.name

#
#    def __str__(self):
#        return "HeaderNode: [HdrName='%s', Inst=%d, Length=%d]" % (self.hdr.name, self.inst, self.length)

    def getProcessLength(self):
        """Get the length of the header including any fields that need to be
        read beyond the end of header"""
        if self._processLen is None:
            lookupLen = self.hdr.decisionLengthLoc()
            self._processLen = max(self.length, lookupLen)
        return self._processLen

    def getLengths(self):
        """Get all valid lengths"""
        return [l / 8 for l in getHeaderLengths(self.hdr)[1]]

    def getDecisionBytes(self):
        """Get all decision byte positions"""
        return self.hdr.getDecisionBytes()[0]

    def getExtractBytes(self):
        """Get all extract byte positions"""
        return self.hdr.getExtractBytes()

    def getFields(self):
        """Get all fields within the header"""
        return self.hdr.getLookupLengthFields()


# Basic test code
if __name__ == '__main__':
    hdr = ParserMapper.ParserMapperHeader('TestHeader')
    hdr.addField('test', 8)
    node = HeaderNode(hdr, 1)
    print(node)
