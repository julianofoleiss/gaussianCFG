import logging
import math

import numpy as np

from ibatch import *

logger = logging.getLogger("statistics")
logger.setLevel(logging.NOTSET)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

outlogger = logging.getLogger("out_statistics")
outlogger.setLevel(logging.DEBUG)
outlogger.addHandler(ch)


def f7(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


class Bin():
    """
    :type address: numpy.uint64
    :type count: int
    :type windows: list[int]
    """

    def __init__(self, addr):
        self.address = np.uint64(addr)
        self.count = 1
        self.windows = []

    def __str__(self):
        return hex(self.address) + ": " + str(self.count)

    def __cmp__(self, other):
        return np.int64(self.address) - np.int64(other.address)


class Statistics():
    """
    :type binSize: int
    :type bins: list[Bin]
    :type stdevThreshold: float
    """

    def __init__(self, binSize, stdevThreshold):
        self.binSize = binSize
        self.bins = np.array([])
        self.stdevThreshold = stdevThreshold
        return

    def euclideanDistance(self, x, y):
        return math.sqrt(abs(x - y) ** 2)

    def getBin(self, binId):
        """
        :param binId: int
        :return: Bin
        """
        return self.bins[binId]

    def getBinFromAddr(self, address):
        """
        :param address: int
        :return: Bin
        """
        d, b = self.whichBin(address)

        #print "distance = ", d, " in bin ", b

        if len(self.bins) < b:
            return None

        return self.bins[b]

    def whichBin(self, address):
        pos = np.searchsorted(self.bins, Bin(address))
        dAnt = np.infty
        dDep = np.infty
        dPos = np.infty

        logger.debug("address = 0x%x", address)
        logger.debug("pos = %d", pos)

        if pos > 0:
            # tem um bin antes desse.
            dAnt = self.euclideanDistance(np.mean(self.bins[pos - 1].windows), address)

        logger.debug("dAnt = %f", dAnt)

        if pos < (np.size(self.bins) - 1):
            # tem um bin depois desse
            dDep = self.euclideanDistance(np.mean(self.bins[pos + 1].windows), address)

        logger.debug("dDep = %f", dDep)

        if np.size(self.bins) > 0 and pos <= (np.size(self.bins) - 1):
            dPos = self.euclideanDistance(np.mean(self.bins[pos].windows), address)

        logger.debug("dPos = %f", dPos)

        # for k in self.bins:
        # 	logger.debug(k)

        if dAnt < dDep:
            closestP = pos - 1
            closest = dAnt
        else:
            closestP = pos + 1
            closest = dDep

        if dPos < closest:
            closestP = pos
            closest = dPos

        logger.debug("closest p: %d", closestP)
        logger.debug("closest: %f", closest)

        return closest, closestP

    def registerLowStDevStatistics(self, batch):
        """
        :param batch: ibatch.InstructionBatch
        """

        logger.debug("batch %s stdev: %s", batch.batchId, batch.meanWindowStdev)

        if batch.meanWindowStdev <= self.stdevThreshold:

            for w in batch.meanWindows:
                w = np.uint64(w)
                closest, closestP = self.whichBin(w)

                logger.debug("closest p: %d", closestP)
                logger.debug("closest: %f", closest)

                if closest == np.inf:
                    self.bins = np.append(self.bins, Bin(w))
                    self.bins[0].windows.append(w)
                else:
                    if closest <= self.binSize:
                        self.bins[closestP].count += 1
                        enc = 0
                        for k in self.bins[closestP].windows:
                            if k == w:
                                enc = 1
                                break
                        if not enc:
                            self.bins[closestP].windows.append(w)

                    else:
                        logger.debug("inserting bin for address 0x%x in position %d:", w, closestP)
                        finalPos = np.searchsorted(self.bins, Bin(w))
                        self.bins = np.insert(self.bins, finalPos, Bin(w))
                        self.bins[finalPos].windows.append(w)

                logger.debug("\n")

            logger.debug("there are %d address bins", len(self.bins))
            for i in self.bins:
                logger.debug(i)
                i.windows.sort()
                for k in i.windows:
                    logger.debug("\t 0x%x", k)

            return

        else:
            logger.debug("high threshold for batch %s", batch.batchId)

        # def registerStatistics(self, batch):

        # 	logger.debug("batch %s stdev: %s", batch.batchId, batch.meanWindowStdev)

        # 	if batch.meanWindowStdev <= self.stdevThreshold:

        # 		for i in batch.genInstruction():
        # 			pos = np.searchsorted(self.bins, Bin(i.pc))
        # 			dAnt = np.infty
        # 			dDep = np.infty
        # 			dPos = np.infty

        # 			logger.debug("i.pc = 0x%x", i.pc)
        # 			logger.debug("pos = %d", pos)

        # 			if pos > 0:
        # 				#tem um bin antes desse.
        # 				dAnt = self.euclideanDistance(self.bins[pos-1].address, i.pc)

        # 			logger.debug("dAnt = %f", dAnt)

        # 			if pos < (np.size(self.bins)-1):
        # 				#tem um bin depois desse
        # 				dDep = self.euclideanDistance(self.bins[pos+1].address, i.pc)

        # 			logger.debug("dDep = %f", dDep)

        # 			if np.size(self.bins) > 0 and pos <= (np.size(self.bins)-1):
        # 				dPos = self.euclideanDistance(self.bins[pos].address, i.pc)

        # 			logger.debug("dPos = %f", dPos)

        # 			# for k in self.bins:
        # 			# 	logger.debug(k)

        # 			if dAnt < dDep:
        # 				closestP = pos-1
        # 				closest = dAnt
        # 			else:
        # 				closestP = pos+1
        # 				closest = dDep

        # 			if dPos < closest:
        # 				closestP = pos
        # 				closest = dPos

        # 			logger.debug("closest p: %d", closestP)
        # 			logger.debug("closest: %f", closest)

        # 			if closest == np.inf:
        # 				self.bins = np.append(self.bins, Bin(i.pc))
        # 			else:
        # 				if closest <= self.binSize:
        # 					self.bins[closestP].count+=1
        # 					enc = 0
        # 					for k in self.bins[closestP].instructions:
        # 						if k.pc == i.pc:
        # 							enc = 1
        # 							break
        # 					if not enc:
        # 						self.bins[closestP].instructions.append(i)

        # 				else:
        # 					logger.debug("inserting bin for address 0x%x in position %d:", i.pc, closestP)
        # 					finalPos = np.searchsorted(self.bins, Bin(i.pc))
        # 					self.bins = np.insert(self.bins, finalPos, Bin(i.pc))
        # 					self.bins[finalPos].instructions.append(i)

        # 			logger.debug("\n")

        # 		logger.debug("there are %d address bins", len(self.bins))
        # 		for i in self.bins:
        # 			logger.debug(i)
        # 			i.instructions.sort(key=lambda x: x.pc)
        # 			for k in i.instructions:
        # 				logger.debug("\t 0x%x\t%s\t\t%s\t%s", k.pc, k.getType(), hex(k.target) if k.isBranchOrCall() else None, k.image )

        # 		return

        # 	else:
        # 		logger.debug("high threshold for batch %s", batch.batchId)


if __name__ == '__main__':

    stat = Statistics(20, 30)

    ifb = InputFileBuffer(20, "isampling.out")
    ifb.getLine()

    moreBatches = not ifb.eof

    while (moreBatches):
        ib = InstructionBatch(20, ifb)
        moreBatches = ib.fromFile()

        ib.calcStatistics(6, 1)
        stat.registerLowStDevStatistics(ib)

    binList = stat.bins.tolist()
    binList.sort(key=lambda x: x.count)

    for i in binList:
        outlogger.debug(i)
        i.windows.sort()
        for k in i.windows:
            outlogger.debug("\t 0x%x", k)

    outlogger.debug("there was a total of %d bins...", len(binList))

    # for i in ib.instructions:
    # 	binId = np.searchsorted(stat.bins, Bin(i.pc))
    # 	outlogger.debug("instruction %x in bin %d starting in %x", i.pc, binId, stat.bins[binId-1].address)


    logger.setLevel(logging.DEBUG)

    x, binId = stat.whichBin(0x404aa8)
    # pensar no -1.... talvez :D
    outlogger.debug("dist = %d", x)
    outlogger.debug("instruction %x in bin %d started in %x with count %d and %d distinct windows", 0x404aa8, binId,
                    stat.bins[binId].address, stat.bins[binId].count, len(stat.bins[binId].windows))


    # for i in binList:
    # 	outlogger.debug(i)
    # 	i.instructions.sort(key=lambda x: x.pc)
    # 	for k in i.instructions:
    # 		outlogger.debug("\t 0x%x\t%s\t\t%s\t%s", k.pc, k.getType(), hex(k.target) if k.isBranchOrCall() else None, k.image )
