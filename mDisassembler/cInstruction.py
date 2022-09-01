import re;

from mNotProvided import fAssertTypes;
from mWindowsAPI import fsHexNumber;

class cInstruction(object):
  def __init__(oSelf, uAddress, sbBytes, sbName, tsbArguments):
    fAssertTypes({
      "uAddress": (uAddress, int),
      "sbBytes": (sbBytes, bytes),
      "sbName": (sbName, bytes),
      "tsbArguments": (tsbArguments,
        tuple(),
        (bytes,),
        (bytes, bytes),
        (bytes, bytes, bytes), # Up to three arguments are expected.
      ),
    });
    oSelf.__uAddress = uAddress;
    oSelf.__sbBytes = sbBytes;
    oSelf.__sbName = sbName;
    oSelf.__tsbArguments = tsbArguments;

  @property
  def uAddress(oSelf):
    return oSelf.__uAddress;

  @property
  def sbBytes(oSelf):
    return oSelf.__sbBytes;
  @property
  def sBytes(oSelf):
    return " ".join("%02X" % uByte for uByte in oSelf.__sbBytes);
  @property
  def uSize(oSelf):
    return len(oSelf.sbBytes);

  @property
  def sbName(oSelf):
    return oSelf.__sbName;
  @property
  def sName(oSelf):
    return str(oSelf.__sbName, "ascii", "strict");

  @property
  def tsbArguments(oSelf):
    return oSelf.__tsbArguments; # Does not prevent overwriting them!
  @property
  def sArguments(oSelf):
    return str(b", ".join(oSelf.__tsbArguments), "ascii", "strict");
  
  @property
  def sInstruction(oSelf):
    return "%-7s %s" % (oSelf.sName, oSelf.sArguments);

  def __str__(oSelf):
    return "%-10s | %-20s | %s" % (
      fsHexNumber(oSelf.uAddress),
      oSelf.sBytes,
      oSelf.sInstruction,
    );