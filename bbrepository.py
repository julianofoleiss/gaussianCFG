from instruction import *
from bb import *


class BBRepository:
    def __init__(self):
        self.blocks = dict()

    def getNumBlocks(self):
        """
        :rtype: int
        """
        return len(self.blocks)

    def addBB(self, bb):
        """
        :param bb: BB
        :rtype: bool
        """
        if bb.entryAddress in self.blocks:
            print 'basic block starting at ', bb.entryAddress, ' already in repository'
            return False
        else:
            self.blocks[bb.entryAddress] = bb
            return True

    def getBBWithEntryAddress(self, entryAddress):
        for i in self.blocks:
            if self.blocks[i].entryAddress == entryAddress:
                return self.blocks[i]
        return None

    def getBB(self, address):
        """
        :param address: int
        :rtype: BB
        """
        for i in self.blocks:
            if self.blocks[i].hasInstruction(address):
                return self.blocks[i]
        return None


if __name__ == '__main__':
    bbr = BBRepository()
    bb = BB(0x1000)
    i = Instruction("push rbp", 0x1000, 1)
    i2 = Instruction("mov rbp, rsp", 0x1001, 1)
    i3 = Instruction("pop rbp", 0x1002, 1)
    i4 = Instruction("ret", 0x1003, 1)
    bb.addInstruction(i)
    bb.addInstruction(i2)
    bb.addInstruction(i3)
    bb.addInstruction(i4)
    bbr.addBB(bb)
    bbr.addBB(bb)
    b = bbr.getBB(0x1000)
    ins = b.getInstructions()
    for i in ins:
        print i
