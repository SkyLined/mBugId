import ctypes, ctypes.wintypes;

INVALID_HANDLE_VALUE      = -1;
PIPE_READMODE_MESSAGE     = 0x00000002;
OPEN_EXISTING             = 0x00000003;
FILE_GENERIC_WRITE        = 0x40000000;
NMPWAIT_WAIT_FOREVER      = 0xFFFFFFFF;
ERROR_PIPE_BUSY           = 0x000000E7;

def fPLMDebugNamedPipeSendData(sPipeName, sData);
  # Connect to the named pipe and send the command-line arguments to BugId.
  while 1:
    # https://msdn.microsoft.com/en-us/library/windows/desktop/aa363858(v=vs.85).aspx
    hPipe = ctypes.windll.kernel32.CreateFileW(
      ur"\\.\pipe\%s" % sPipeName, # lpFileName
      FILE_GENERIC_WRITE, # dwDesiredAccess
      0, # dwShareMode
      None, # lpSecurityAttributes
      OPEN_EXISTING, # dwCreationDisposition
      0, # dwFlagsAndAttributes
      None, # hTemplateFile
    );
    if hPipe != INVALID_HANDLE_VALUE:
      break;
    assert ctypes.windll.kernel32.GetLastError() == ERROR_PIPE_BUSY, \
      "CreateFile error %d" % ctypes.windll.kernel32.GetLastError();
    # https://msdn.microsoft.com/en-us/library/windows/desktop/aa365800(v=vs.85).aspx
    assert ctypes.windll.kernel32.WaitNamedPipeW(
      ur"\\.\pipe\%s" % sPipeName, # lpNamedPipeName
      NMPWAIT_WAIT_FOREVER, # nTimeOut
    ), \
      "WaitNamedPipe error %d" % ctypes.windll.kernel32.GetLastError();
  
  # Send the pipe mode to send messages
  dwPipeReadMode = ctypes.wintypes.DWORD(PIPE_READMODE_MESSAGE);
  # https://msdn.microsoft.com/en-us/library/windows/desktop/aa365787(v=vs.85).aspx
  assert ctypes.windll.kernel32.SetNamedPipeHandleState(
    hPipe, # hNamedPipe
    ctypes.byref(dwPipeReadMode), # lpMode
    None, # lpMaxCollectionCount
    None, # lpCollectDataTimeout
  ), \
      "SetNamedPipeHandleState error %d" % ctypes.windll.kernel32.GetLastError();
  
  # Send the arguments passed to us to BugId
  oBuffer = ctypes.create_string_buffer(sData);
  dwBytesWritten = ctypes.wintypes.DWORD(0);
  # https://msdn.microsoft.com/en-us/library/windows/desktop/aa365747(v=vs.85).aspx
  assert ctypes.windll.kernel32.WriteFile(
    hPipe, # hFile
    oBuffer, # lpBuffer
    ctypes.sizeof(oBuffer), # nNumberOfBytesToWrite
    ctypes.byref(dwBytesWritten), # lpNumberOfBytesWritten
    None, # lpOverlapped
  ), \
      "WriteFile error %d" % ctypes.windll.kernel32.GetLastError();
  assert dwBytesWritten.value == ctypes.sizeof(oBuffer), \
      "WriteFile wrote %d instead of %d bytes" % (dwBytesWritten.value, ctypes.sizeof(oBuffer));
  
  # Close the pipe
  # https://msdn.microsoft.com/en-us/library/windows/desktop/ms724211(v=vs.85).aspx
  assert ctypes.windll.kernel32.CloseHandle(
    hPipe, # hObject
  ), \
      "CloseHandle error %d" % ctypes.windll.kernel32.GetLastError();

