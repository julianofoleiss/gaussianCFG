from ibatch import InputFileBuffer

def outputTrace(infile, outfile):
    ifb = InputFileBuffer(1000, infile)

    line = ifb.getLine()

    more_lines = not ifb.eof

    out = open(outfile, 'w')


    while not ifb.eof:
        line = ifb.getLine()
        line = line.split('\t')
        out.write(str(int(line[1],16)) + "\n")

if __name__ == "__main__":
    outputTrace("isampling50.out", "trace.out")