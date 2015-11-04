import numpy as np
import pylab as P

if __name__ == "__main__":

    x = P.loadtxt("isampling50_matmul.out.stdev")
    #x = P.loadtxt("isampling50.out.stdev")

    X = np.sort(x)

    difs = []

    for i in range(0, len(x)-1):
        difs.append((i, abs(X[i] - X[i+1])))

    for i in difs:
        print i

    logx = 20 * np.log10(x + 0.00001)

    #print logx

    n, bins, patches = P.hist(logx, 100, histtype='stepfilled', normed=1)

    P.setp(patches)

    print len(logx)
    print len(bins)

    P.show()



