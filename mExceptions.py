class cNoAccessToProcessException(Exception):
  def __init__(oSelf, uProcessId: int):
    oSelf.uProcessId = uProcessId;
    Exception.__init__(oSelf, "The process with id %d/0x%X cannot be accessed." % (uProcessId, uProcessId));
