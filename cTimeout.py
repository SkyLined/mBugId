class cTimeout(object):
  def __init__(oTimeout, sDescription, nFireAtOrAfterApplicationRunTime, fCallback, axCallbackArguments):
    oTimeout.sDescription = sDescription;
    oTimeout.__nFireAtOrAfterApplicationRunTime = nFireAtOrAfterApplicationRunTime;
    oTimeout.__fCallback = fCallback;
    oTimeout.__axCallbackArguments = axCallbackArguments;
  
  def fbShouldFire(oTimeout, nApplicationRunTime):
    return nApplicationRunTime >= oTimeout.__nFireAtOrAfterApplicationRunTime;
  
  def fFire(oTimeout):
    oTimeout.__fCallback(*oTimeout.__axCallbackArguments);