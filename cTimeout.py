class cTimeout(object):
  def __init__(oTimeout, sDescription, nFireAtOrAfterApplicationRunTimeInSeconds, fCallback, axCallbackArguments):
    oTimeout.sDescription = sDescription;
    oTimeout.__nFireAtOrAfterApplicationRunTimeInSeconds = nFireAtOrAfterApplicationRunTimeInSeconds;
    oTimeout.__fCallback = fCallback;
    oTimeout.__axCallbackArguments = axCallbackArguments;
  
  def fbShouldFire(oTimeout, nApplicationRunTime):
    return nApplicationRunTime >= oTimeout.__nFireAtOrAfterApplicationRunTimeInSeconds;
  
  def fFire(oTimeout):
    oTimeout.__fCallback(*oTimeout.__axCallbackArguments);