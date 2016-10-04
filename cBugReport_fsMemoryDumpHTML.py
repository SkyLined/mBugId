import re;
from dxBugIdConfig import dxBugIdConfig;

def fasGetRemarks(oBugReport, uAddress, uSize):
  dasRemarks_by_iStartOffset = {};
  for (sRemark, uRemarkStartAddress, uRemarkSize) in oBugReport.atxMemoryRemarks:
    if uAddress + uSize > uRemarkStartAddress and uRemarkStartAddress + (uRemarkSize or 1) > uAddress:
      iStartOffset = uRemarkStartAddress - uAddress;
      dasRemarks_by_iStartOffset.setdefault(iStartOffset, []).append(sRemark);
  asRemarks = [];
  for iStartOffset in sorted(dasRemarks_by_iStartOffset.keys()):
    sAddress = "0x%X" % uAddress;
    if iStartOffset > 0:
      # Start offset cannot be larger than the size of a pointer, which is at most 8 on supported ISAs
      sAddress += "+%d" % iStartOffset;
    elif iStartOffset < -9:
      sAddress += "-0x%X" % -iStartOffset;
    elif iStartOffset != 0:
      sAddress += "%d" % iStartOffset;
    asRemarks.append("%s=%s" % (sAddress, ", ".join(dasRemarks_by_iStartOffset[iStartOffset])));
  return asRemarks;

def cBugReport_fsMemoryDumpHTML(oBugReport, oCdbWrapper, sDescription, uStartAddress, uSize):
  uPointerSize = oCdbWrapper.fuGetValue("@$ptrsize");
  if not oCdbWrapper.bCdbRunning: return None;
  uAlignedStartAddress = uStartAddress - (uStartAddress % uPointerSize);
  uEndAddress = uStartAddress + uSize;
  uAlignedEndAddress = uEndAddress + uPointerSize - 1 - ((uEndAddress - 1) % uPointerSize);
  uAlignedSize = uAlignedEndAddress - uAlignedStartAddress;
  asMemoryTableHTML = [];
  asMemoryDumpOutput = oCdbWrapper.fasSendCommandAndReadOutput(
    "dpp 0x%X L0x%X; $$ Get memory before address" % (uAlignedStartAddress, uAlignedSize), bOutputIsInformative = True);
  for sLine in asMemoryDumpOutput:
    oMatch = re.match(r"([0-9a-f`]+)\s+(?:([\?`]+)|([0-9a-f`]+))(?:\s+(.*?))?\s*$", sLine);
    assert oMatch, "Unexpected memory dump output: %s" % repr(sLine);
    (sAddress, bInaccessible, sPointerAddress, sPointerSymbol) = oMatch.groups();
    uAddress = long(sAddress.replace("`", ""), 16);
    asRemarks = fasGetRemarks(oBugReport, uAddress, uPointerSize);
    if bInaccessible:
      sMemoryDataHTML = '<td colspan="3" class="MemoryInaccessible">-- inaccessible --</td>';
    else:
      uPointerAddress = long(sPointerAddress.replace("`", ""), 16);
      asPointerRemarks = fasGetRemarks(oBugReport, uPointerAddress, 1);
      asRemarks += asPointerRemarks;
      sByteData = sPointerAddress.replace("`", "");
      sMemoryBytesHTML = '';
      sMemoryCharsHTML = '';
      uOffset = 0;
      sPreviousClass = None;
      while sByteData:
        sClass = fasGetRemarks(oBugReport, uAddress + uOffset, 1) and "Important" or None;
        # There's a space between bytes, which is not part of the `Important` span unless it's in between two important
        # bytes.
        sBytepadding = uOffset and " " or "";
        if sClass is not sPreviousClass:
          if sClass:
            sMemoryBytesHTML += sBytepadding;
            sMemoryBytesHTML += '<span class="Important">';
            sMemoryCharsHTML += '<span class="Important">';
          else:
            sMemoryBytesHTML += '</span>';
            sMemoryBytesHTML += sBytepadding;
            sMemoryCharsHTML += '</span>';
        else:
          sMemoryBytesHTML += sBytepadding;
        sMemoryBytesHTML += oCdbWrapper.fsHTMLEncode(sByteData[-2:]);
        sMemoryCharsHTML += oCdbWrapper.fsHTMLEncode(chr(long(sByteData[-2:], 16)));
        uOffset += 1;
        sPreviousClass = sClass;
        sByteData = sByteData[:-2];
      if sClass:
        sMemoryBytesHTML += '</span>';
        sMemoryCharsHTML += '</span>';
      sMemoryPointerHTML = oCdbWrapper.fsHTMLEncode(sPointerAddress);
      if sPointerSymbol:
        sMemoryPointerHTML += ' &#8594; <span class="MemoryPointerSymbol">%s</span>' % \
          oCdbWrapper.fsHTMLEncode(sPointerSymbol);
      sMemoryDataHTML = "".join([
        '<td class="MemoryBytes">%s</td>' % sMemoryBytesHTML,
        '<td class="MemoryChars">%s</td>' % sMemoryCharsHTML,
        '<td class="MemoryPointer">%s</td>' % sMemoryPointerHTML,
      ]);
    asMemoryTableHTML.append("<tr>%s</tr>" % "".join([
      '<td class="MemoryAddress%s">%s</td>' % \
          (asRemarks and " Important" or "", oCdbWrapper.fsHTMLEncode(sAddress)),
      sMemoryDataHTML,
      '<td>%s</td>' % (asRemarks and '<span class="MemoryRemarks">// %s</span>' % ", ".join(asRemarks) or ""),
    ]));
  return '<table class="MemoryBlock"><tbody>\r\n%s\r\n</tbody></table>\r\n' % "\r\n".join(asMemoryTableHTML);
