import ctypes;
from ctypes.wintypes import *;
# Some basic stuff first.
CAST = ctypes.cast;
POINTER = ctypes.POINTER;
TRUE = True;
FALSE = False;
NULL = None;
SIZE_T = ctypes.c_size_t;
UCHAR = ctypes.c_ushort;
PDWORD = POINTER(DWORD);
PHANDLE = POINTER(HANDLE);
#SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS
class SID(ctypes.Structure):
  pass; # This is super secret!!
class SID_AND_ATTRIBUTES(ctypes.Structure):
  _fields_ = [
    ("Sid", POINTER(SID)),
    ("Attributes", DWORD),
  ];
#TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
TOKEN_INFORMATION_CLASS = ctypes.c_ulong;
class TOKEN_MANDATORY_LABEL(ctypes.Structure):
  _fields_ = [
    ("Label", SID_AND_ATTRIBUTES),
  ];
