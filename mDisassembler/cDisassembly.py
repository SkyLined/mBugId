from mNotProvided import fAssertTypes;

from ..cProcess import cProcess;

from .cInstruction import cInstruction;

class cDisassembly(object):
  def __init__(oSelf, aoInstructions):
    fAssertTypes({
      "aoInstructions": (aoInstructions, [cInstruction]),
    });
    oSelf.__aoInstructions = aoInstructions;
  
  @property
  def uLength(oSelf):
    return len(oSelf.__aoInstructions);

  def foGetInstruction(oSelf, uIndex):
    fAssertTypes({
      "uIndex": (uIndex, int),
    });
    return oSelf.__aoInstructions[uIndex];

  def fo0GetInstructionAtAddress(oSelf, uAddress):
    for oInstruction in oSelf.__aoInstructions:
      if oInstruction.uAddress == uAddress:
        return oInstruction;
    return None;
  
  def __len__(oSelf):
    return len(oSelf.__aoInstructions);

  def __str__(oSelf):
    return "\r\n".join(
      str(oInstruction)
      for oInstruction in oSelf.__aoInstructions
    ),
