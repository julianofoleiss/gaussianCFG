import logging
from instruction import ControlFlowInstruction, Instruction
from bb import BB
from statistics import Statistics, Bin
from ibatch import InputFileBuffer, InstructionBatch
from cfg import CFG
from bbrepository import BBRepository
import numpy as np

logger = logging.getLogger("buildcfg")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)


class CFGBuilder:
    def __init__(self):
        return

    def buildCFG(self):
        return


class CFGBuilder0(CFGBuilder):
    '''
    :type samplesFile: string
    :type batchSize: int
    :type binSize: int
    :type stdDevThreshold: float
    :type windowSize: int
    :type recurrentThreshold: int
    :type targets: dict[int, int]
    :type bbr: BBRepository
    :type cfg: CFG
    '''

    def __init__(self, samplesFile, batchSize, binSize, stdDevThreshold, windowSize, recurrentThreshold):
        CFGBuilder.__init__(self)

        self.stat = Statistics(binSize, stdDevThreshold)
        self.ifb = InputFileBuffer(50000, samplesFile)
        self.batchSize = batchSize
        self.binSize = binSize
        self.stdDevThreshold = stdDevThreshold
        self.samplesFile = samplesFile
        self.windowSize = windowSize
        self.recurrentThreshold = recurrentThreshold
        self.targets = dict()
        self.bbr = BBRepository()
        self.cfg = CFG()
        self.numMerge = 0
        self.highStdevEdges = 0
        self.numHighStdevTries = 0
        self.numHighStdevOK = 0

    def buildCFGR(self, instrGen, justBuild, ib):
        for i in instrGen:

            if i.isBranchOrCall():
                if self.targets.has_key(i.target):
                    self.targets[i.target] += 1
                else:
                    self.targets[i.target] = 1

            b = self.stat.getBinFromAddr(i.pc)

            if b is None and (justBuild == 0):
                return

            if b is not None:
                recurrent = b.count > self.recurrentThreshold
            else:
                recurrent = False

            if recurrent or justBuild==1:

                # logger.debug("i: 0x%x", i.pc)
                if (self.targets.has_key(i.pc)) or (justBuild==1):
                    # logger.debug("\t is target...")
                    bb = self.bbr.getBB(i.pc)
                    if not bb:
                        bb = BB(i.pc)
                        self.bbr.addBB(bb)
                    while not bb.done:

                        x = self.bbr.getBB(i.pc)

                        if x:
                            if x.entryAddress != bb.entryAddress:
                                bb.done = 1
                                self.numMerge+=1
                                logger.debug("merging blocks %x and %x", bb.entryAddress, x.entryAddress)
                                bb.addTarget(x)
                                x.addSource(bb)
                                self.cfg.addOrIncrementEdge(bb, x)
                                break

                        if not bb.hasInstruction(i.pc):
                            bb.addInstruction(i)

                        if i.isBranchOrCall():
                            bb.done = 1

                            iafter = ib.getInstructionAfter(i)

                            if iafter is None:
                                break

                            #logger.debug("i: %s", i)
                            #logger.debug("iafter: %s", iafter)

                            if iafter.pc == i.target:
                                #branch taken

                                #logger.debug("0x%x: branch taken to 0x%x (%s)\n", i.pc, iafter.pc, i.text)

                                if self.targets.has_key(i.target):
                                    self.targets[i.target] += 1
                                else:
                                    self.targets[i.target] = 1

                                # justBuild = 1 if b.count > self.recurrentThreshold else 0
                                # self.buildCFGR(instrGen, justBuild, ib)

                                self.buildCFGR(instrGen, 0, ib)

                                targetBB = self.bbr.getBB(i.target)
                            else:
                                #branch not taken

                                #logger.debug("0x%x: fallthrough to 0x%x (%s)\n", i.pc, iafter.pc, i.text)

                                if self.targets.has_key(iafter.pc):
                                    self.targets[iafter.pc] +=1
                                else:
                                    self.targets[iafter.pc] = 1

                                self.buildCFGR(instrGen, 0, ib)

                                targetBB = self.bbr.getBB(iafter.pc)

                            if targetBB:
                                bb.addTarget(targetBB)
                                targetBB.addSource(bb)
                                self.cfg.addOrIncrementEdge(bb, targetBB)
                        try:
                            i = instrGen.next()
                        except StopIteration:
                            break

            #TODO: talvez quem que mexer em todos que usam "target" self.targets.has_key(i.target)
            if i.isBranchOrCall():
                iafter = ib.getInstructionAfter(i)
                if iafter is not None:
                    targetBB = self.bbr.getBB(iafter.pc)
                    thisBB = self.bbr.getBB(i.pc)
                    if targetBB and thisBB:
                        thisBB.addTarget(targetBB)
                        targetBB.addSource(thisBB)
                        self.cfg.addOrIncrementEdge(thisBB, targetBB)

    def buildCFG(self):

        # ignore the first line in the samples file
        self.ifb.getLine()

        moreBatches = not self.ifb.eof

        commonBinIns = dict()
        totalIns = dict()

        lowstdev = 0
        highstdev = 0

        lowstdevValues = []
        histdevValues = []

        stddevs = []

        while (moreBatches):

            ib = InstructionBatch(self.batchSize, self.ifb)
            moreBatches = ib.fromFile()
            ib.calcStatistics(self.windowSize, 1)
            self.stat.registerLowStDevStatistics(ib)

            stddevs.append(ib.meanWindowStdev)

            if ib.batchId % 100 == 0:
                logger.debug("batch %d", ib.batchId)

            if ib.meanWindowStdev <= self.stdDevThreshold:
                instrGen = ib.genInstruction()
                self.buildCFGR(instrGen, 0, ib)
                lowstdev+=1
                lowstdevValues.append(ib.meanWindowStdev)
            else:
                highstdev+=1
                histdevValues.append(ib.meanWindowStdev)

                printedIns = False
                instrGen = ib.genInstruction()

                for i in instrGen:

                    if i.isBranchOrCall():
                        if self.targets.has_key(i.target):
                            self.targets[i.target] += 1
                        else:
                            self.targets[i.target] = 1

                        b = self.stat.getBinFromAddr(i.pc)

                        if b is None:
                            continue

                        bb = self.bbr.getBB(i.pc)

                        if bb and b.count > self.recurrentThreshold:
                            iafter = ib.getInstructionAfter(i)
                            if iafter is not None:
                                otherBB = self.bbr.getBB(iafter.pc)
                                if not otherBB:
                                    logger.debug("trying to create a new BB for %x", iafter.pc)
                                    self.buildCFGR(instrGen, 1, ib)
                                    self.numHighStdevTries+=1
                                    otherBB = self.bbr.getBB(iafter.pc)
                                    if otherBB:
                                        logger.debug("got it!")
                                        self.numHighStdevOK+=1

                                if otherBB:
                                    bb.addTarget(otherBB)
                                    otherBB.addSource(bb)
                                    self.cfg.addOrIncrementEdge(bb, otherBB)
                                    self.highStdevEdges+=1

            # if i.pc not in totalIns:
            #     totalIns[i.pc] = 1
            # else:
            #     totalIns[i.pc]+=1
            #
            # b = self.stat.getBinFromAddr(i.pc)
            # if b.count > self.recurrentThreshold:
            #     #logger.debug("instruction at %X is in a common bin", i.pc)
            #     if i.pc not in commonBinIns:
            #         commonBinIns[i.pc] = 1
            #     else:
            #         commonBinIns[i.pc]+=1
            #
            # if i.isBranchOrCall():
            #     if(self.targets.has_key(i.target)):
            #         self.targets[i.target]+=1
            #     else:
            #         self.targets[i.target] = 1

        #
        # commonBinList = commonBinIns.items()
        #
        # commonBinList.sort(key=lambda x: x[0])
        #
        # logger.debug("common bins:")
        # for i in commonBinList:
        #     logger.debug("0x%x: %d", i[0], i[1])
        #
        # logger.debug("control flow targets: (%d items)", len(self.targets))
        # targetList = self.targets.items()
        # targetList.sort(key=lambda x: x[0])
        #
        # for i in targetList:
        #     logger.debug("0x%x: %d", i[0], i[1])
        #
        # logger.debug("there were %d distinct instructions in common bins", len(commonBinIns))
        #
        # logger.debug("a total of %d distinct instructions were sampled.", len(totalIns))

        self.cfg.toDot("test_builder0.dot", False, True)
        self.cfg.printCFG()

        # bb = self.bbr.getBB(0x400811)
        #
        # for i in bb.getInstructions():
        #     print hex(i.pc)

        print len(self.bbr.blocks), " basic blocks were recognized"
        print len(self.stat.bins), " address bins were created"
        print lowstdev, " low standard deviation batches"
        print highstdev, " high standard deviation batches"

        totalBBIns = []
        for i in self.bbr.blocks:
            totalBBIns.append(len(self.bbr.blocks[i].instructions))

        print "each block has an average of ",  np.mean(totalBBIns), "+-" , np.std(totalBBIns), " instructions"
        print "number of basic block merges: ", self.numMerge
        print "number of high standard deviation recurrent edges marked: ", self.highStdevEdges
        print "number of high standard deviation basic block build tries: ", self.numHighStdevTries
        print "number of high standard deviation basic block actually built: ", self.numHighStdevOK

        histdevValues.sort()
        lowstdevValues.sort()

        print "high stdev values", histdevValues
        print "hsv mean = ", np.mean(histdevValues), "+-" ,np.std(histdevValues)
        print "low stdev values", lowstdevValues
        print "lo mean = ", np.mean(lowstdevValues), "+-" ,np.std(lowstdevValues)

        #implementar metricas: quantidade de instrucoes e blocos basicos por funcao

        stdev = file(self.samplesFile + ".stdev", 'w')
        for i in stddevs:
            stdev.write(str(i) + "\n")
        stdev.close()

class CFGBuilder1(CFGBuilder):
    '''
    :type samplesFile: string
    :type batchSize: int
    :type binSize: int
    :type stdDevThreshold: float
    :type windowSize: int
    :type recurrentThreshold: int
    :type targets: dict[int, int]
    :type bbr: BBRepository
    :type cfg: CFG
    '''

    def __init__(self, samplesFile, batchSize, binSize, stdDevThreshold, windowSize, recurrentThreshold):
        CFGBuilder.__init__(self)

        self.stat = Statistics(binSize, stdDevThreshold)
        self.ifb = InputFileBuffer(50000, samplesFile)
        self.batchSize = batchSize
        self.binSize = binSize
        self.stdDevThreshold = stdDevThreshold
        self.samplesFile = samplesFile
        self.windowSize = windowSize
        self.recurrentThreshold = recurrentThreshold
        self.targets = dict()
        self.bbr = BBRepository()
        self.cfg = CFG()
        self.numMerge = 0
        self.highStdevEdges = 0
        self.numHighStdevTries = 0
        self.numHighStdevOK = 0

    def buildCFGR(self, instrGen, justBuild, ib):
        for i in instrGen:

            b = self.stat.getBinFromAddr(i.pc)

            if b is None and (justBuild == 0):
                return

            if b is not None:
                recurrent = b.count > self.recurrentThreshold
            else:
                recurrent = False

            if recurrent or justBuild==1:
                # logger.debug("\t is target...")
                bb = self.bbr.getBB(i.pc)
                if not bb:
                    bb = BB(i.pc)
                    self.bbr.addBB(bb)

                while not bb.done:

                    x = self.bbr.getBB(i.pc)

                    if x:
                        if x.entryAddress != bb.entryAddress:
                            bb.done = 1
                            self.numMerge+=1
                            logger.debug("merging blocks %x and %x", bb.entryAddress, x.entryAddress)
                            bb.addTarget(x)
                            x.addSource(bb)
                            self.cfg.addOrIncrementEdge(bb, x)
                            break

                    if not bb.hasInstruction(i.pc):
                        bb.addInstruction(i)

                    if i.isBranchOrCall():
                        bb.done = 1

                        iafter = ib.getInstructionAfter(i)

                        if iafter is None:
                            break

                        #logger.debug("i: %s", i)
                        #logger.debug("iafter: %s", iafter)

                        if iafter.pc == i.target:
                            #branch taken

                            #logger.debug("0x%x: branch taken to 0x%x (%s)\n", i.pc, iafter.pc, i.text)

                            # justBuild = 1 if b.count > self.recurrentThreshold else 0
                            #
                            # self.buildCFGR(instrGen, justBuild, ib)

                            self.buildCFGR(instrGen, 0, ib)

                            targetBB = self.bbr.getBB(i.target)
                        else:
                            #branch not taken

                            #logger.debug("0x%x: fallthrough to 0x%x (%s)\n", i.pc, iafter.pc, i.text)

                            self.buildCFGR(instrGen, 0, ib)

                            targetBB = self.bbr.getBB(iafter.pc)

                        if targetBB:
                            bb.addTarget(targetBB)
                            targetBB.addSource(bb)
                            self.cfg.addOrIncrementEdge(bb, targetBB)
                    try:
                        i = instrGen.next()
                    except StopIteration:
                        break

            if i.isBranchOrCall():
                iafter = ib.getInstructionAfter(i)
                if iafter is not None:
                    targetBB = self.bbr.getBB(iafter.pc)
                    thisBB = self.bbr.getBB(i.pc)
                    if targetBB and thisBB:
                        thisBB.addTarget(targetBB)
                        targetBB.addSource(thisBB)
                        self.cfg.addOrIncrementEdge(thisBB, targetBB)

    def buildCFG(self):

        # ignore the first line in the samples file
        self.ifb.getLine()

        moreBatches = not self.ifb.eof

        commonBinIns = dict()
        totalIns = dict()

        lowstdev = 0
        highstdev = 0

        stddevs = []

        while (moreBatches):

            ib = InstructionBatch(self.batchSize, self.ifb)
            moreBatches = ib.fromFile()
            ib.calcStatistics(self.windowSize, 1)
            self.stat.registerLowStDevStatistics(ib)

            stddevs.append(ib.meanWindowStdev)

            if ib.batchId % 100 == 0:
                logger.debug("batch %d", ib.batchId)

            if ib.meanWindowStdev <= self.stdDevThreshold:
                instrGen = ib.genInstruction()
                self.buildCFGR(instrGen, 0, ib)
                lowstdev+=1
            else:
                highstdev+=1

                printedIns = False
                instrGen = ib.genInstruction()

                for i in instrGen:

                    if i.isBranchOrCall():

                        b = self.stat.getBinFromAddr(i.pc)

                        if b is None:
                            continue

                        bb = self.bbr.getBB(i.pc)

                        if bb and b.count > self.recurrentThreshold:
                            iafter = ib.getInstructionAfter(i)
                            if iafter is not None:
                                otherBB = self.bbr.getBB(iafter.pc)
                                if not otherBB:
                                    logger.debug("trying to create a new BB for %x", iafter.pc)
                                    self.buildCFGR(instrGen, 1, ib)
                                    self.numHighStdevTries+=1
                                    otherBB = self.bbr.getBB(iafter.pc)
                                    if otherBB:
                                        logger.debug("got it!")
                                        self.numHighStdevOK+=1

                                if otherBB:
                                    bb.addTarget(otherBB)
                                    otherBB.addSource(bb)
                                    self.cfg.addOrIncrementEdge(bb, otherBB)
                                    self.highStdevEdges+=1

        self.cfg.toDot("test_builder1.dot", True, False)
        self.cfg.printCFG()

        print len(self.bbr.blocks), " basic blocks were recognized"
        print len(self.stat.bins), " address bins were created"
        print lowstdev, " low standard deviation batches"
        print highstdev, " high standard deviation batches"

        totalBBIns = []
        for i in self.bbr.blocks:
            totalBBIns.append(len(self.bbr.blocks[i].instructions))

        print "each block has an average of ",  np.mean(totalBBIns), "+-" , np.std(totalBBIns), " instructions"
        print "number of basic block merges: ", self.numMerge
        print "number of high standard deviation recurrent edges marked: ", self.highStdevEdges
        print "number of high standard deviation basic block build tries: ", self.numHighStdevTries
        print "number of high standard deviation basic block actually built: ", self.numHighStdevOK

        #implementar metricas: quantidade de instrucoes e blocos basicos por funcao

        stdev = file(self.samplesFile + ".stdev", 'w')
        for i in stddevs:
            stdev.write(str(i) + "\n")
        stdev.close()

if __name__ == "__main__":
    #builder = CFGBuilder0("isampling.out", 20, 20, 40, 6, 30)
    #binsize ajuda a encontrar blocos basicos maiores
    #stddevthreshold tambem..
    #blocos grandes sofrem bastante acredito que isso seja culpa do algoritmo de bin. ver a saida das bins...
    #builder = CFGBuilder0("isampling50.out", batchSize=50, binSize=30 , stdDevThreshold=500, windowSize=10, recurrentThreshold=15)
    #builder = CFGBuilder0("isampling50_matmul.out", batchSize=50, binSize=30 , stdDevThreshold=100, windowSize=10, recurrentThreshold=10)

    #bem loco!!!
    #builder = CFGBuilder0("isampling50.out", batchSize=50, binSize=30 , stdDevThreshold=500, windowSize=25, recurrentThreshold=15)

    builder = CFGBuilder0("isampling50.out", batchSize=50, binSize=30 , stdDevThreshold=500, windowSize=25, recurrentThreshold=15)

    builder.buildCFG()

    # builder = CFGBuilder1("isampling50.out", batchSize=50, binSize=30 , stdDevThreshold=500, windowSize=30, recurrentThreshold=15)
    #
    # builder.buildCFG()
