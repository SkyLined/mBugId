class cTimeout(object):
  def __init__(oTimeout, nApplicationRunTime, fCallback, axCallbackArguments):
    oTimeout.__nApplicationRunTime = nApplicationRunTime;
    oTimeout.__fCallback = fCallback;
    oTimeout.__axCallbackArguments = axCallbackArguments;
  
  def fbShouldFire(oTimeout, nApplicationRunTime):
    return nApplicationRunTime >= oTimeout.__nApplicationRunTime;
  
  def fFire(oTimeout):
    oTimeout.__fCallback(*oTimeout.__axCallbackArguments);