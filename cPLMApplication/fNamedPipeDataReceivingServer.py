import ctypes, ctypes.wintypes;

INVALID_HANDLE_VALUE      = -1;
PIPE_WAIT                 = 0x00000000;
PIPE_ACCESS_INBOUND       = 0x00000001;
PIPE_READMODE_MESSAGE     = 0x00000002;
PIPE_TYPE_MESSAGE         = 0x00000004;
ERROR_BROKEN_PIPE         = 0x0000006D;
ERROR_MORE_DATA           = 0x000000EA;
PIPE_UNLIMITED_INSTANCES  = 0x000000FF;

def fNamedPipeDataReceivingServer(sPipeName, fbCallback):
  # https://msdn.microsoft.com/en-us/library/windows/desktop/aa365150(v=vs.85).aspx
  hPipe = ctypes.windll.kernel32.CreateNamedPipeW(
    ur"\\.\pipe\%s" % sPipeName, # lpName
    PIPE_ACCESS_INBOUND, # dwOpenMode
    PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT, # dwPipeMode
    PIPE_UNLIMITED_INSTANCES, # nMaxInstances
    0x1000, # nOutBufferSize
    0x1000, # nInBufferSize
    0, # nDefaultTimeOut
    None, # lpSecurityAttributes
  );
  assert hPipe != INVALID_HANDLE_VALUE, \
      "CreateNamedPipe error %d" % ctypes.windll.kernel32.GetLastError();
  try:
    # Ideally, this would use overlapped I/O and events to wait for connections
    # until it is told to stop. However, that significantly complicates the code
    # so I've opted for sending a special message over the named pipe to stop
    # this loop.
    while 1:
      # Accept a connection on the named pipe.
      # https://msdn.microsoft.com/en-us/library/windows/desktop/aa365146(v=vs.85).aspx
      assert ctypes.windll.kernel32.ConnectNamedPipe(
        hPipe,
        None,
      ), \
          "ConnectNamedPipe error %d" % ctypes.windll.kernel32.GetLastError();
      
      # Read a message from the named pipe.
      uBufferLength = len("-p 65536 -tid 65536") + 1;
      sData = "";
      oBuffer = ctypes.create_string_buffer(uBufferLength);
      dwBytesRead = ctypes.wintypes.DWORD(0);
      while 1:
        # https://msdn.microsoft.com/en-us/library/windows/desktop/aa365467(v=vs.85).aspx
        if not ctypes.windll.kernel32.ReadFile(
          hPipe, # hFile
          oBuffer, # lpBuffer
          ctypes.sizeof(oBuffer), # nNumberOfBytesToRead
          ctypes.byref(dwBytesRead), # lpNumberOfBytesRead
          None, # lpOverlapped
        ):
          uLastError = ctypes.windll.kernel32.GetLastError();
          if uLastError == ERROR_BROKEN_PIPE:
            break; # The pipe had been closed
          assert uLastError == ERROR_MORE_DATA, \
            "ReadFile error %d" % ctypes.windll.kernel32.GetLastError();
        sData += oBuffer.value;
      
      # Disconnect the named pipe.
      assert ctypes.windll.kernel32.DisconnectNamedPipe(
        hPipe,
      ), \
          "DisconnectNamedPipe error %d" % ctypes.windll.kernel32.GetLastError();
      
      if not fbCallback(sData):
        break;
  finally:
    assert ctypes.windll.kernel32.CloseHandle(
      hPipe, # hObject
    ), \
        "CloseHandle error %d" % ctypes.windll.kernel32.GetLastError();