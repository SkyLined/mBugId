import os, re;
from .dxConfig import dxConfig;

def cProcess_fasbGetStack(oProcess, sbGetStackCommand):
  # Get the stack, which should make sure all relevant symbols are loaded or at least marked as requiring loading.
  # Noisy symbol loading is turned on during the command, so there will be symbol loading debug messages in between
  # the stack output, which makes the stack hard to parse: it is therefore discarded and the command is executed
  # again later (without noisy symbol loading) when symbols are loaded.
  # This only makes sense if we're using symbol servers, so we can download the symbols again if they fail.
  if oProcess.oCdbWrapper.bUsingSymbolServers and dxConfig["bMakeSureSymbolsAreLoaded"]:
    oProcess.fasbExecuteCdbCommand(
      sbCommand = b".symopt+ 0x80000000;%s;.symopt- 0x80000000" % sbGetStackCommand,
      sb0Comment = b"Get stack with debug symbols enabled",
    );
    if dxConfig["uMaxSymbolLoadingRetries"] > 0:
      # Try to reload all modules and symbols. The symbol loader will not reload all symbols, but only those symbols that
      # were loaded before or those it attempted to load before, but failed. The symbol loader will output all kinds of
      # cruft, which may contain information about PDB files that cannot be loaded (e.g. corrupt files). If any such
      # issues are detected, these PDB files are deleted and the code loops, so the symbol loader can download them
      # again and any further issues can be detected and fixed. The code loops until there are no more issues that can be
      # fixed, or it has run ten times.
      # This step may also provide some help debugging symbol loading problems that cannot be fixed automatically.
      for x in range(dxConfig["uMaxSymbolLoadingRetries"]):
        # Reload all modules with noisy symbol loading on to detect any errors. These errors are automatically detected
        # and handled in cCdbOutput.fHandleCommonErrorsInOutput, so all we have to do is check if any errors were found
        # and try again to see if they have been fixed.
        asbLastSymbolReloadOutput = oProcess.fasbExecuteCdbCommand(
          sbCommand = b".symopt+ 0x80000000;.reload /v;.symopt- 0x80000000;",
          sb0Comment = b"Reload symbols for all modules",
        );
        for sbLine in asbLastSymbolReloadOutput:
          # If there were any errors, make sure we try loading again.
          if re.match(rb"^%s\s*$" % b"|".join([
            rb"DBGHELP: (.*?) (\- E_PDB_CORRUPT|dia error 0x[0-9a-f]+)",
          ]), sbLine):
            break;
            # Found an error, stop this loop and try again.
        else:
          # Loop completed: no errors found, stop reloading modules.
          break;
  # Get the stack for real. At this point, no output from symbol loader is expected or handled.
  asbStackOutput = oProcess.fasbExecuteCdbCommand(
    sbCommand = sbGetStackCommand,
    sb0Comment = b"Get stack",
    bOutputIsInformative = True,
  );
  return asbStackOutput;
