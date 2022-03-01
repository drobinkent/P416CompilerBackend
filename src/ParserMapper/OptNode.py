#!/usr/bin/env python

"""Optimal chain graph node"""

import sys
sys.path.append("..")
sys.path.append(".")
import ParserMapper.ParserMapperHeader
from abc import ABCMeta

from ParserMapper.DAGHeaderNode import HeaderNode
from ParserMapper.DAGChainNode import DAGChainNode
from ParserMapper.DAGChain import DAGChain

class OptNode(object, metaclass=ABCMeta):
    """Optimal chain graph node"""

    def __init__(self, chain, bpc, cover, fringe):
        self.chain = chain # This is a DAGChain
        self.bpc = bpc
        self.cover = cover
        self.fringe = fringe
        self._recalcStr()

    def _recalcStr(self):
        self._str = '%s: [%s, bpc=%1.3f]' % (self.__class__.__name__,
                self.chain, self.bpc)
        #self._shortStr = "%s@%03d" % (self.dagNode.shortStr(), self.loc)
        #self._cmpName = "%s:%03d" % (self.dagNode.getCmpName(), self.loc)

    def optNodeComparator(self, other):
        if type(other) == OptNode:
            c = self.chain.dagChainComparator( other.chain) # Need to compare the dagchains
            if c != 0:
                return c

            return 0
        else:
            return -1

    def __str__(self):
        if self._str is None:
            self._recalcStr()
        return self._str

# Basic test code
if __name__ == '__main__':
    hdr = Header.ParserMapperHeader('TestHeader')
    hdr.addField('test', 32)
    chainNode1 = DAGChainNode(HeaderNode(hdr, 1), 1, 3, 3)
    chainNode2 = DAGChainNode(HeaderNode(hdr, 2), 0, 2, 2)

    chain = DAGChain()
    chain.add(chainNode1)
    chain.add(chainNode2)

    optNode = OptNode(chain, 8, chain, None)
    print(optNode)
