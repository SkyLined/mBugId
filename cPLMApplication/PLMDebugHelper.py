import os, sys;
# Search main cBugId folder for dxConfig first.
sys.path.insert(0, os.path.abspath(os.path.join(__file__, "..", "..")));
from dxConfig import dxConfig;
sys.path.pop(0); # Restore normal search path

from fNamedPipeSendData import fNamedPipeSendData;

if __name__ == "__main__":
  fNamedPipeSendData(dxConfig["sPLMDebugHelperPipeName"], " ".join(sys.argv[1:]));

