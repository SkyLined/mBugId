class cTimeout(object):
  def __init__(oTimeout, sDescription, nFireAtOrAfterApplicationRunTimeInSeconds, f0Callback = None, txCallbackArguments = tuple()):
    oTimeout.sDescription = sDescription;
    oTimeout.__nFireAtOrAfterApplicationRunTimeInSeconds = nFireAtOrAfterApplicationRunTimeInSeconds;
    oTimeout.__f0Callback = f0Callback;
    oTimeout.__txCallbackArguments = txCallbackArguments;
  
  def fbShouldFire(oTimeout, nApplicationRunTimeInSeconds):
    return nApplicationRunTimeInSeconds >= oTimeout.__nFireAtOrAfterApplicationRunTimeInSeconds;
  
  def fFire(oTimeout, oCdbWrapper):
    if oTimeout.__f0Callback:
      oTimeout.__f0Callback(oCdbWrapper, *oTimeout.__txCallbackArguments);