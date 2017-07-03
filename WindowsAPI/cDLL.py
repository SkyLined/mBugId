import ctypes;

class cDLL(object):
  def __init__(oDLL, sDLLFilePath):
    oDLL.__oWinDLL = ctypes.WinDLL(sDLLFilePath);
  
  def ffxGetFunction(oDLL, xReturnType, sFunctionName, *axArgumenTypes):
    fFunctionConstructor = ctypes.WINFUNCTYPE(xReturnType, *axArgumenTypes);
    return fFunctionConstructor(
      (sFunctionName, oDLL.__oWinDLL),
      tuple([(1, "p%d" % u, 0) for u in xrange(len(axArgumenTypes))])
    );
  
  def fAddFunction(oDLL, xReturnType, sFunctionName, *axArgumenTypes):
    fFunction = oDLL.ffxGetFunction(xReturnType, sFunctionName, *axArgumenTypes);
    setattr(oDLL, sFunctionName, fFunction);

if __name__ == "__main__":
  from ctypes.wintypes import *;
  oKERNEL32 = cDLL("kernel32.dll");
  oKERNEL32.ffxAddFunction(HANDLE, "GetStdHandle", DWORD);
  oKERNEL32.fAddFunction(BOOL, "SetConsoleTextAttribute", HANDLE, WORD);
  STD_OUTPUT_HANDLE = -11
  hStdOut = oKERNEL32.GetStdHandle(STD_OUTPUT_HANDLE);
  assert oKERNEL32.SetConsoleTextAttribute(hStdOut, 0x70), \
      "meh";
  print "ola!";
  assert oKERNEL32.SetConsoleTextAttribute(hStdOut, 0x07), \
      "meh";
