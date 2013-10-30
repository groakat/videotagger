
import logging, logging.handlers
import inspect
from colorama import Fore, Back, Style
from colorama import init
init(autoreset=True)
    
# set logger up
      
# Make a global logging object.
logLevel = logging.INFO


log = logging.getLogger("log")
log.setLevel(logLevel)
h = logging.StreamHandler()
f = logging.Formatter(Back.RED + "%(levelname)s" + Back.RESET + " " +
                      Style.BRIGHT + "%(asctime)s " + Style.RESET_ALL +
                      "[T: %(thread)d] "+
                      Fore.YELLOW + "<%(funcName)s> " + Fore.RESET +
                      "[%(lineno)d] " +
                      Style.BRIGHT + "%(message)s" + Style.RESET_ALL)
h.setFormatter(f)
for handler in log.handlers:
    log.removeHandler(handler)
    
log.addHandler(h)

logE = logging.getLogger("logEnter")
logE.setLevel(logLevel)
hE = logging.StreamHandler()
fE = logging.Formatter("%(levelname)s %(asctime)s [T: %(thread)d] %(message)s - entering")
hE.setFormatter(fE)
for handler in logE.handlers:
    logE.removeHandler(handler)
    
logE.addHandler(hE)

logF = logging.getLogger("logFinish")
logF.setLevel(logLevel)
hF = logging.StreamHandler()
fF = logging.Formatter("%(levelname)s %(asctime)s [T: %(thread)d] %(message)s - exiting")
hF.setFormatter(fF)
for handler in logF.handlers:
    logF.removeHandler(handler)
    
logF.addHandler(hF)


def logClassFunction(f):
    def call(self, *args, **kwargs):
        eStr = "[{0}/" + Fore.YELLOW + "{1}" + Fore.RESET +"]"
        fStr = "[{0}/" + Fore.RED +"{1}" + Fore.RESET +"]"
        logE.debug(eStr.format(self.__class__, f.__name__)) #f.im_class, 
        res = f(self, *args, **kwargs)
        logF.debug(fStr.format(self.__class__, f.__name__))
        return res
    
    return call


def logClassFunctionInfo(f):
    def call(self, *args, **kwargs):
        eStr = "[{0}/" + Fore.YELLOW + "{1}" + Fore.RESET +"]"
        fStr = "[{0}/" + Fore.RED +"{1}" + Fore.RESET +"]"
        logE.info(eStr.format(self.__class__, f.__name__)) #f.im_class, 
        res = f(self, *args, **kwargs)
        logF.info(fStr.format(self.__class__, f.__name__))
        return res
    
    return call
