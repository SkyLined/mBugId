import ctypes;
from Defines import *;
from Types import *;

KERNEL32 = ctypes.windll.kernel32;
hProcessHeap = KERNEL32.GetProcessHeap();

from ADVAPI32 import ADVAPI32;
