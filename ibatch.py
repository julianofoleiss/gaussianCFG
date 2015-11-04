from instruction import *
import numpy as np
import logging

logger = logging.getLogger("ibatch")
logger.setLevel(logging.NOTSET)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)


class InputFileBuffer():
    def __init__(self, size, filename):
        self.data = [0] * size
        self.size = size
        self.filename = filename
        self.file = open(filename)
        self.eof = False
        for i in range(size):
            self.data[i] = self.file.readline()
        self.p = 0

    def __getNextLines(self):
        for i in range(self.size):
            data = self.file.readline()
            if data != "":
                self.data[i] = data
            else:
                self.eof = True
                break

    def getLine(self):

        if (self.p >= self.size):
            self.p = 0
            self.__getNextLines()

        line = self.data[self.p]
        self.p += 1

        return line

    def peekLine(self):
        if (self.p >= self.size):
            self.p = 0
            self.__getNextLines()

        return self.data[self.p]


class InstructionBatch():
    """
    :type batchId: int
    :type instructions: np.ndarray[instruction.Instruction]
    :type size: int
    :type ifb: InputFileBuffer
    :type meanWindows = np.ndarray
    :type PCs: list[int]
    :type meanWindowStdev: float
    :type meanWindowMean: float
    :type pcStdev: float
    :type pcMean: float
    """

    def __init__(self, size, inputFileBuffer):
        self.batchId = -1
        self.instructions = np.array([])
        self.size = size
        self.ifb = inputFileBuffer

        # statistics
        self.meanWindows = np.array([])
        self.PCs = []
        self.meanWindowStdev = 0
        self.meanWindowMean = 0
        self.pcStdev = 0
        self.pcMean = 0

    '''
        This function reads an instruction batch from a file.
        Returns True if there are further batches in the file, False otherwise.
    '''

    def fromFile(self):

        self.batchId = int(self.ifb.peekLine().split('\t')[4])

        logger.debug('batchId: %d', self.batchId)

        for i in range(self.size):
            line = self.ifb.getLine()
            if (self.ifb.eof):
                return False

            line = line.split('\t')
            instType = line[3].split(' ')[0]

            # print line

            if (instType == 'BRANCHORCALL'):
                newInst = ControlFlowInstruction(line[5], int(line[1], base=16), int(line[2]))

                newInst.direct = True if line[3].split(' ')[1] == 'DIRECT' else False

                if newInst.direct:
                    addrSplit = line[5].split(" ")

                    if (addrSplit[1].startswith("0x")):
                        newInst.target = int(addrSplit[1], base=16)
                    else:
                        print ('could not find the target address!')
                        newInst.target = 666
                else:
                    # peek nao funciona se a instrucao e a ultima...
                    # logo, se Nao e a ultima instrucao do lote..
                    if (i < (self.size - 1)):
                        if line[3].split(' ')[2] == "INCOND":
                            nextLine = self.ifb.peekLine()
                            newInst.target = int(nextLine.split('\t')[1], base=16)
                        else:
                            print "conditional indirect branches not supported yet."
                    else:
                        newInst.target = 0xDEADBEEF
            else:
                newInst = Instruction(line[5], int(line[1], base=16), int(line[2]))

            newInst.image = line[6].replace("\n", "")

            self.instructions = np.append(self.instructions, newInst)

        # print newInst

        # for i in self.instructions:
        # 	print i
        return True

    def genInstruction(self):
        for i in self.instructions:
            yield i

    def getInstructionAfter(self, inst):
        """
        :param inst: instruction.Instruction
        :rtype: instruction.Instruction
        """

        if inst in self.instructions:
            pos = 0
            for i in self.instructions:
                if i == inst:
                    break
                pos+=1

            pos+=1

            if pos >= len(self.instructions):
                return None
            return self.instructions[pos]
        else:
            return None


    def calcStatistics(self, windowSize, windowStep):
        PCbuffer = []
        meanBuffer = np.array([0])
        instructions = self.genInstruction()

        for i in range(0, windowSize):
            try:
                ins = instructions.next()
                logger.debug('ins.pc = %ld', ins.pc)
            except StopIteration:
                break

            PCbuffer.append(ins.pc)
            meanBuffer[0] += ins.pc

        logger.debug(meanBuffer[0])

        for i in range(windowSize, self.size):
            logger.debug(i)
            logger.debug('i-windowsize = %d', i - windowSize)
            try:
                ins = instructions.next()
            except StopIteration:
                break

            PCbuffer.append(ins.pc)
            logger.debug('ins.pc = %ld', ins.pc)
            logger.debug('pcbuffer[i-windowsize] = %d', PCbuffer[i - windowSize])
            logger.debug(meanBuffer[i - windowSize] - PCbuffer[i - windowSize] + PCbuffer[i])
            meanBuffer = np.append(meanBuffer, meanBuffer[i - windowSize] - PCbuffer[i - windowSize] + PCbuffer[i])

        np.set_printoptions(precision=20)
        logger.debug(meanBuffer)

        for i in range(len(meanBuffer)):
            meanBuffer[i] /= windowSize
            logger.debug("meanbuffer[%d] = %ld", i, meanBuffer[i])

        self.meanWindowStdev = window_stdev = np.std(meanBuffer)
        self.meanWindowMean = window_mean = np.average(meanBuffer)
        self.pcMean = pc_mean = np.average(PCbuffer)
        self.pcStdev = pc_stdev = np.std(PCbuffer)

        self.meanWindows = meanBuffer
        self.PCs = PCbuffer

        logger.debug("average of all pc = %e", pc_mean)
        logger.debug("standard deviation of mean pc =  %e", pc_stdev)
        logger.debug("average of all windows = %e", window_mean)
        logger.debug("standard deviation of mean windows = %e", window_stdev)


if __name__ == '__main__':
    # ib = InstructionBatch(20)
    # traceFile = open("isampling.out")
    # traceFile.readline()
    # ib.fromFile(traceFile)

    ifb = InputFileBuffer(20, "isampling.out")
    ifb.getLine()

    ib = InstructionBatch(20, ifb)
    ib.fromFile()

    ib2 = InstructionBatch(20, ifb)
    ib2.fromFile()

    for i in ib.genInstruction():
        logger.debug(i)

    ib.calcStatistics(6, 1)

    # for i in ib2.genInstruction():
    # 	print i

    # ib2.calcStatistics(6, 1)

    # ib3 = InstructionBatch(20, ifb)
    # ib3.fromFile()

    # ib3.calcStatistics(6, 1)

    # for i in ib3.genInstruction():
    # 	print i


    # ib4 = InstructionBatch(20, ifb)
    # ib4.fromFile()

    # ib4.calcStatistics(6, 1)

    # for i in ib4.genInstruction():
    # 	print i
