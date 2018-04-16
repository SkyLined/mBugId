def fsNumberOfBytes(uNumberOfBytes):
  if uNumberOfBytes == 1:
    return "1 byte";
  elif uNumberOfBytes < 10:
    return "%d bytes" % uNumberOfBytes;
  else:
    return "%d/0x%X bytes" % (uNumberOfBytes, uNumberOfBytes);
