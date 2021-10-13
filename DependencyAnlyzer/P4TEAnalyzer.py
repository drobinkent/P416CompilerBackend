

class MATNode:
    nodeType = None

    def __init__(self, nodeType,name,oriiginalP4node):
        self.nodeType = nodeType
        self.nextNodes= []
        self.name = name
        self.matchKey = None
        self.actions= None
        self.oriiginalP4node = oriiginalP4node

        return






# class P4TETableNode(P4TEAnalyzerNode):
#
#     def __init__(self, nodeType,name):
#         self.nodeType = nodeType
#         self.nextNodes= []
#         self.name = name
#         return
#
# class P4TEConditionalNode(P4TEAnalyzerNode):
#
#     def __init__(self, nodeType,name):
#         self.nodeType = nodeType
#         self.nextNodes= []
#         self.name = name
#         return