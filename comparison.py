from cfg import *

if __name__ == "__main__":
    g = CFG("test_builder0.dot")
    h = CFG("test_builder1.dot")
    f = CFG("../CFG_noextern.dot")

    print g.similarity(f)
    # print h.similarity(f)
    #
    print g.similarity(f) / float(len(f.edges))
    # CFGprint f.similarity(g) / float(len(f.edges))
    #
    # print h.similarity(f) / float(len(h.edges))
    # print f.similarity(h) / float(len(f.edges))
