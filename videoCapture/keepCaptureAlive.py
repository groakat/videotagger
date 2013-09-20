import sys
import subprocess as sp
from time import localtime

if __name__ == "__main__":
    rawArgs = sys.argv[1:]
    cnt = 0
    while(1):
        if cnt == 0:
            args = rawArgs + ['-sT', str(59 - localtime().tm_min)]
        else:
            args = rawArgs + ['-sT', str(59)]
        cnt += 1
            
        print("calling: python {args}".format(args=' '.join(args)))
        
        p = sp.Popen("python {args}".format(args=' '.join(args)),
                     shell=True, stdout=sp.PIPE, stderr=sp.STDOUT)
        output =  p.communicate()[0]
        
        if output[-1000:].find("exit by timer") == -1:            
            break
#     sp.Popen("python {args}".format(' '.join(sys.argb)))