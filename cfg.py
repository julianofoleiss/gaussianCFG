from instruction import *
from bb import *
from bbrepository import *


class CFG:
    def __init__(self, dotFile=None):
        self.edges = dict()
        self.bbs = dict()

        if dotFile is not None:
            self.__loadFromDot(dotFile)

    def __loadFromDot(self, dotFile):
        f = open(dotFile)

        bbr = BBRepository()

        line = f.readline()
        while line != "":

            if line.find("->") != -1:
                line = line.split("->")

                sourceAddr = int(line[0].strip().replace("_", ""),16)
                targetAddr = int(line[1].strip().split(" ")[0].replace("_", ""),16)

                source = bbr.getBBWithEntryAddress(sourceAddr)
                if source is None:
                    source = BB(sourceAddr)
                    bbr.addBB(source)

                target = bbr.getBBWithEntryAddress(targetAddr)
                if target is None:
                    target = BB(targetAddr)
                    bbr.addBB(target)

                source.addTarget(target)
                target.addSource(source)
                self.addOrIncrementEdge(source, target)

            # else:
            #     if line.find("}") == -1:
            #         print "line containing a node"

            line = f.readline()

    def similarity(self, otherCFG):
        edges =  self.edges.keys()
        edges.sort(key=lambda x: x[0])
        matches = 0

        for i in edges:
            if i in otherCFG.edges:
                matches+=1

        return matches

    def addOrIncrementEdge(self, sourceBB, targetBB):
        edge = (sourceBB.entryAddress, targetBB.entryAddress)

        # print "addOrIncrementEdge(", edge, ")"

        if edge in self.edges:
            self.edges[edge] += 1
            # print "incremented edge"
        else:
            self.edges[edge] = 1
            # print "added new edge"

        if sourceBB.entryAddress not in self.bbs:
            self.bbs[sourceBB.entryAddress] = sourceBB

        if targetBB.entryAddress not in self.bbs:
            self.bbs[targetBB.entryAddress] = targetBB

    def printCFG(self):
        edges = []
        print len(self.bbs), " basic blocks\n"
        for i in self.bbs:
            ins = self.bbs[i].getInstructions()
            print self.bbs[i]
            for k in ins:
                print k

            for k in self.bbs[i].targets:
                edge = (self.bbs[i].entryAddress, k.entryAddress)
                if edge in self.edges:
                    edges.append((self.bbs[i], k, self.edges[edge]))

        print "\n", len(edges), " edge(s)\n"

        for i in edges:
            print hex(i[0].entryAddress), ' -> ', hex(i[1].entryAddress), "(", i[2], ')'

    def toDot(self, dotFilename, graphToolCompat, edgeLabels):
        '''
        Prints out the graph as a DOT file.
        :param dotFilename: string
        :param graphToolCompat: boolean
        :param edgeLabels: boolean
        :return: None
        '''

        out = open(dotFilename, "w")
        out.write("digraph{\n")

        edges = []
        for i in self.bbs:
            instrList = self.bbs[i].instructions.items()
            instrList.sort(key=lambda x: x[0])
            # str(instrList[0][1].image)

            if graphToolCompat:
                out.write("\t_" + hex(self.bbs[i].entryAddress) + " [label=\"_" + hex(self.bbs[i].entryAddress) + "\"]\n")
            else:
                out.write("\t_" + hex(self.bbs[i].entryAddress) + " [label=\"" + str(instrList[0][1].image) + "\\n" + hex(
                    self.bbs[i].entryAddress) + "\\n" + ("done" if self.bbs[i].done else "not done") + "\\n" + str(
                    len(self.bbs[i].getInstructions())) + " instructions" + "\"]" "\n")

            for k in self.bbs[i].targets:
                edge = (self.bbs[i].entryAddress, k.entryAddress)
                if edge in self.edges:
                    edges.append((self.bbs[i], k, self.edges[edge]))

        # cada elemento de edges eh uma tupla (source, target, number_of_transitions)
        for i in edges:
            if edgeLabels:
                out.write(
                    "\t_" + hex(i[0].entryAddress) + ' -> _' + hex(i[1].entryAddress) + " [label=\"" + str(i[2]) + '\"]\n')
            else:
                out.write(
                    "\t_" + hex(i[0].entryAddress) + ' -> _' + hex(i[1].entryAddress) + "\n")

        out.write("}\n")
        out.close()


if __name__ == '__main__':
    cfg = CFG()
    bbr = BBRepository()
    bb = BB(0x1000)
    i = Instruction("push rbp", 0x1000, 1)
    i2 = Instruction("mov rbp, rsp", 0x1001, 2)
    bb.addInstruction(i)
    bb.addInstruction(i2)

    i3 = Instruction("push rbp", 0x2000, 1)
    i4 = Instruction("mov rbp, rsp", 0x2001, 1)
    i5 = ControlFlowInstruction("call 0x1000", 0x2002, 5, target=i.pc, direct=True)
    bb2 = BB(0x2000)
    bb2.addInstruction(i3)
    bb2.addInstruction(i4)
    bb2.addInstruction(i5)

    bbr.addBB(bb)
    bbr.addBB(bb2)

    bb2.addTarget(bb)
    bb.addSource(bb2)

    cfg.addOrIncrementEdge(bb2, bb)

    cfg.printCFG()

    cfg.toDot("test.dot")
