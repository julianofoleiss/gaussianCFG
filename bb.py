from instruction import *
import operator


def f7(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


class BB:
    """
    :type entryAddress: int
    :type done: bool
    :type instructions: dict[int, Instruction]
    :type targets: list[BB]
    :type sources: list[BB]
    """

    def __init__(self, entryAddress):
        self.entryAddress = entryAddress
        self.done = False
        self.instructions = dict()
        self.targets = []
        self.sources = []

    def __str__(self):
        done = str(0) if not self.done else str(1)
        return 'bb beginning at ' + hex(self.entryAddress) + ' with ' + str(
            self.getNumInstructions()) + ' instructions ' + \
               str(len(self.targets)) + " targets and " + str(len(self.sources)) + ' sources' + " DONE? " + done

    def addInstruction(self, instruction):
        if instruction.pc in self.instructions:
            print ('bb already contains instruction at ', hex(instruction.pc), '(', instruction.text, ')')
            return False
        else:
            for i in range(instruction.size):
                self.instructions[instruction.pc + i] = instruction
            return True

    def hasInstruction(self, instructionPc):
        if instructionPc in self.instructions:
            return self.instructions[instructionPc]
        else:
            return False

    def getInstructions(self):
        ret = sorted(self.instructions.items(), key=operator.itemgetter(0))
        # ret = zip(*ret)[1]
        ret = [item[1] for item in ret]
        ret = f7(ret)
        return ret

    def isDone(self):
        return self.done

    def getNumInstructions(self):
        values = self.instructions.values()
        return len(set(values))

    def addTarget(self, targetBB):
        if targetBB not in self.targets:
            self.targets.append(targetBB)

    def addSource(self, sourceBB):
        if sourceBB not in self.sources:
            self.sources.append(sourceBB)


if __name__ == '__main__':
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

    bb2.addTarget(bb)
    bb2.addTarget(bb)
    bb.addSource(bb2)
    bb.addSource(bb2)

    print (bb)
    print (bb2)

    ins = bb.getInstructions()
    print (type(ins))
    for i in ins:
        print (i)

    ins = bb2.getInstructions()
    for i in ins:
        print (i)
