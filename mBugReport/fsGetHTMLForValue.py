import re;

guNumberOfCharsBetweenTicks = 8;

def fsGetHTMLForValue(uValue, uBitSize):
  sValueHex = "%%0%dX" % (uBitSize >> 2) % uValue;
  sHumanReadableValue = "0x" + "`".join([
    sValueHex[uIndex:uIndex  + guNumberOfCharsBetweenTicks]
    for uIndex in range(0, len(sValueHex), guNumberOfCharsBetweenTicks)  
  ]);
  (sValuePadding, sValueWithoutPadding) = re.match(r"^(0x[0`]*)([0-9A-F`]+?)$", sHumanReadableValue).groups();
  return (
      '<span class="HexNumberHeader">%s</span>' +
      '<span class="HexNumber">%s</span>'
  ) % (sValuePadding, sValueWithoutPadding);
