def fu0ValueFromCdbHexOutput(sb0BytesString):
  return int(sb0BytesString.replace(b"`", b""), 16) if sb0BytesString else None;