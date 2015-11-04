class Instruction:
    def __init__(self, text, pc, size):
        self.text = text
        self.pc = pc
        self.size = size
        self.image = "(no image)"

    def isBranchOrCall(self):
        return isinstance(self, ControlFlowInstruction)

    def getType(self):
        return 'generic'

    def getImage(self):
        return self.image

    def __str__(self):
        return hex(self.pc) + ":\t" + self.text + "\t(thru " + hex(
            self.pc + self.size - 1) + ") [at " + self.image + "]"


class ControlFlowInstruction(Instruction):
    def __init__(self, text, pc, size, target=None, direct=True):
        Instruction.__init__(self, text, pc, size)
        # super().__init__(self, text, pc, size)
        self.target = target
        self.direct = direct

    def getTarget(self):
        return self.target

    def getType(self):
        return 'controFlow'

    def isDirect(self):
        return self.direct

    def __str__(self):
        return Instruction.__str__(self) + " target = " + hex(self.target) + ' direct? ' + str(bool(self.direct))


if __name__ == '__main__':
    i = ControlFlowInstruction("jmp main", 0x400000, direct=False)
    print (i.getType())
    print (i.getTarget())
    print (i.isBranchOrCall())
    print (isinstance(i, Instruction))
    print (issubclass(Instruction, ControlFlowInstruction))
    print (issubclass(ControlFlowInstruction, Instruction))
    print (i.isDirect())
