from mWindowsAPI import cVirtualAllocation;

from ..dxConfig import dxConfig;

def cCdbWrapper_fAllocateReserveMemoryIfNeeded(oCdbWrapper):
  ### Allocate reserve memory ######################################################################################
  # Reserve some memory for exception analysis in case the target application causes a system-wide low-memory
  # situation.
  if dxConfig["uReservedMemory"]:
    if oCdbWrapper.o0ReservedMemoryVirtualAllocation is None:
      try:
        oCdbWrapper.o0ReservedMemoryVirtualAllocation = cVirtualAllocation.foCreateForProcessId(
          uProcessId = oCdbWrapper.oUtilityProcess.uId,
          uSize = dxConfig["uReservedMemory"],
        );
      except MemoryError:
        oCdbWrapper.fbFireCallbacks("Log message", "Could not allocate 0x%X bytes reserved memory." % dxConfig["uReservedMemory"]);
        oCdbWrapper.o0ReservedMemoryVirtualAllocation = None;
        # If we cannot allocate memory, we'll just continue anyway.
