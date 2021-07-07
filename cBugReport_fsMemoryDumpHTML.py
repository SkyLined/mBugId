import re;

from .fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;

grbMemoryDumpLine = re.compile(
  rb"^"
  rb"([0-9a-f`]+)"    # **address**
  rb"\s+"             # whitespace
  rb"(?:"             # either {
    rb"([\?`]+)"      #   "????" <inaccessible>
  rb"|"               # } or {
    rb"([0-9a-f`]+)"  #   **pointer-address**
  rb")"               # }
  rb"(?:"             # optionally {
    rb"\s+"           #   whitespace
    rb"(.*?)"         #   **pointer-symbol**
  rb")?"              # }
  rb"\s*$"
);

def fbByteHasRemarks(oBugReport, uAddress):
  for (sRemark, uRemarkStartAddress, uRemarkSize) in oBugReport.atxMemoryRemarks:
    if uRemarkSize is not None and uAddress >= uRemarkStartAddress and uAddress < uRemarkStartAddress + uRemarkSize:
      return True;
  return False;

def fbAddressHasRemarks(oBugReport, uAddress):
  for (sRemark, uRemarkStartAddress, uRemarkSize) in oBugReport.atxMemoryRemarks:
    if uRemarkSize is None and uAddress == uRemarkStartAddress:
      return True;
  return False;

def fasGetRemarksForRange(oBugReport, uAddress, uSize):
  uStartAddress = uAddress;
  uEndAddress = uAddress + uSize;
  datsRemark_and_iEndOffset_by_iStartOffset = {};
  for (sRemark, uRemarkStartAddress, uRemarkSize) in oBugReport.atxMemoryRemarks:
    assert (
      isinstance(sRemark, str)
      and (isinstance(uRemarkStartAddress, int) or isinstance(uRemarkStartAddress, int))
      and (isinstance(uRemarkSize, int) or isinstance(uRemarkSize, int) or uRemarkSize is None)
    ), "Bad remark data: %s" % repr((sRemark, uRemarkStartAddress, uRemarkSize));
    uRemarkEndAddress = uRemarkStartAddress + (uRemarkSize or 1);
    if (
      (uRemarkStartAddress >= uStartAddress and uRemarkStartAddress < uEndAddress) # Remarks starts inside memory range
      or (uRemarkEndAddress > uStartAddress and uRemarkEndAddress <= uEndAddress) # or remark ends inside memory range
    ):
      iRemarkStartOffset = uRemarkStartAddress - uAddress;
      iRemarkEndOffset = uRemarkSize and iRemarkStartOffset + uRemarkSize or None;
      datsRemark_and_iEndOffset_by_iStartOffset.setdefault(iRemarkStartOffset, []).append((sRemark, iRemarkEndOffset));
  asRemarksForRange = [];
  for iRemarkStartOffset in sorted(datsRemark_and_iEndOffset_by_iStartOffset.keys()):
    for (sRemark, iRemarkEndOffset) in datsRemark_and_iEndOffset_by_iStartOffset[iRemarkStartOffset]:
      # Create a range description for the remark, which contains any of the following
      # [ start offset in range "~" end offset in range ] [ remark ] 
      # End offsets, when shown cannot be larger than the size of a pointer, which is at most 8 on supported ISAs, so %d will do
      sFormat = "%s";
      if iRemarkEndOffset is None:
        # Remark has no size, just show start offset:
        #     "*" start offset "=" remark
        sFormat = "*%d=%s" % (iRemarkStartOffset, sFormat);
      elif iRemarkStartOffset == 0 and iRemarkEndOffset == uSize:
        # Remark fits range exact: show no extra information:
        #     "=" remark
        sFormat = "=%s" % sFormat;
      else:
        if iRemarkStartOffset < 0 or iRemarkEndOffset > uSize:
          # This remark starts before this memory range and/or ends after it: show what part of the remark region
          # applies to this memory region:
          #     remark "[" start offset within remark region "~" length  "]"
          sRemarkStartOffset = (iRemarkStartOffset < -9 and "0x%X" or "%d") % -iRemarkStartOffset;
          sRemarkLength = "%d" % (iRemarkEndOffset > uSize and uSize or iRemarkEndOffset);
          sFormat = "%s[%s~%s]" % (sFormat, sRemarkStartOffset, sRemarkLength);
        # Determine start and end offset of remark in current memory region and the corresponding length
        iStartOffset = iRemarkStartOffset > 0 and iRemarkStartOffset or 0;
        iEndOffset = iRemarkEndOffset > uSize and uSize or iRemarkEndOffset;
        uLength = iEndOffset - iStartOffset;
        if uLength == 1:
          # Remark applies to one byte: show offset:
          #      offset "=" remark
          sFormat = "%d=%s" % (iStartOffset, sFormat);
        else:
          # Remark applies to multiple bytes: show start offset and length
          #      offset "~" length "=" remark
          sFormat = "%d~%d=%s" % (iStartOffset, uLength, sFormat);
      asRemarksForRange.append(sFormat % sRemark);
  return asRemarksForRange;

def cBugReport_fsMemoryDumpHTML(oBugReport, oCdbWrapper, oProcess, sDescription, uStartAddress, uEndAddress):
  uPointerSize = oProcess.uPointerSize;
  uAlignedStartAddress = uStartAddress - (uStartAddress % uPointerSize);
  uAlignedEndAddress = uEndAddress + uPointerSize - 1 - ((uEndAddress - 1) % uPointerSize);
  uAlignedSize = uAlignedEndAddress - uAlignedStartAddress;
  asMemoryTableHTML = [];
  asbMemoryDumpOutput = oProcess.fasbExecuteCdbCommand(
    sbCommand = b"dpp 0x%X L0x%X;" % (uAlignedStartAddress, uAlignedSize),
    sb0Comment = b"Get memory dump for 0x%X-0x%X" % (uStartAddress, uEndAddress),
    bOutputIsInformative = True
  );
  for sbLine in asbMemoryDumpOutput:
    obMemoryDumpLineMatch = re.match(grbMemoryDumpLine, sbLine);
    assert obMemoryDumpLineMatch, \
        "Unexpected memory dump output: %s" % repr(sbLine);
    (sbAddress, sb0Inaccessible, sbPointerAddress, sb0PointerSymbol) = \
        obMemoryDumpLineMatch.groups();
    uAddress = fu0ValueFromCdbHexOutput(sbAddress);
    asRemarks = fasGetRemarksForRange(oBugReport, uAddress, uPointerSize);
    if sb0Inaccessible:
      sMemoryDataHTML = '<td colspan="3" class="MemoryInaccessible">-- inaccessible --</td>';
    else:
      sbHexBytes = sbPointerAddress.replace(b"`", b"");
      uPointerAddress = fu0ValueFromCdbHexOutput(sbHexBytes);
      asPointerRemarks = fasGetRemarksForRange(oBugReport, uPointerAddress, 1);
      asRemarks += asPointerRemarks;
      sMemoryBytesHTML = '';
      sMemoryCharsHTML = '';
      uOffset = 0;
      sCurrentByteClass = None;
      sCurrentCharClass = None;
      while sbHexBytes:
        # byte prefix/separator
        sBytePrefixHTML = fbAddressHasRemarks(oBugReport, uAddress + uOffset) and "*" or " ";
        if sBytePrefixHTML == "*":
          sNewByteClass = "Important";
          if sCurrentByteClass is not sNewByteClass:
            if sCurrentByteClass:
              sMemoryBytesHTML += "</span>";
            sMemoryBytesHTML += '<span class="%s">' % sNewByteClass;
            sCurrentByteClass = sNewByteClass;
        sMemoryBytesHTML += sBytePrefixHTML;
        sNewByteAndCharClass = fbByteHasRemarks(oBugReport, uAddress + uOffset) and "Important" or None;
        # byte
        sByteHTML = oCdbWrapper.fsHTMLEncode(str(sbHexBytes[-2:], 'latin1'));
        if sCurrentByteClass is not sNewByteAndCharClass:
          if sCurrentByteClass:
            sMemoryBytesHTML += '</span>';
          if sNewByteAndCharClass:
            sMemoryBytesHTML += '<span class="%s">' % sNewByteAndCharClass;
          sCurrentByteClass = sNewByteAndCharClass;
        sMemoryBytesHTML += sByteHTML;
        # char
        sCharHTML = oCdbWrapper.fsHTMLEncode(chr(int(sbHexBytes[-2:], 16)));
        if sCurrentCharClass is not sNewByteAndCharClass:
          if sCurrentCharClass:
            sMemoryCharsHTML += '</span>';
          if sNewByteAndCharClass:
            sMemoryCharsHTML += '<span class="%s">' % sNewByteAndCharClass;
          sCurrentCharClass = sNewByteAndCharClass;
        sMemoryCharsHTML += sCharHTML;
        uOffset += 1;
        sbHexBytes = sbHexBytes[:-2];
      if sCurrentByteClass:
        sMemoryBytesHTML += '</span>';
      if sCurrentCharClass:
        sMemoryCharsHTML += '</span>';
      sMemoryPointerHTML = oCdbWrapper.fsHTMLEncode(str(sbPointerAddress, 'latin1'));
      if sb0PointerSymbol:
        sMemoryPointerHTML += ' &#8594; <span class="MemoryPointerSymbol">%s</span>' % \
          oCdbWrapper.fsHTMLEncode(sb0PointerSymbol);
      sMemoryDataHTML = "".join([
        '<td class="MemoryBytes">%s</td>' % sMemoryBytesHTML,
        '<td class="MemoryChars">%s</td>' % sMemoryCharsHTML,
        '<td class="MemoryPointer">%s</td>' % sMemoryPointerHTML,
      ]);
    asMemoryTableHTML.append("<tr>%s</tr>" % "".join([
      '<td class="MemoryAddress%s">%s</td>' % \
          (asRemarks and " Important" or "", oCdbWrapper.fsHTMLEncode(sbAddress)),
      sMemoryDataHTML,
      '<td>%s</td>' % (asRemarks and '<span class="MemoryRemarks">// %s</span>' % ", ".join(asRemarks) or ""),
    ]));
  return '<table class="MemoryBlock"><tbody>\r\n%s\r\n</tbody></table>\r\n' % "\r\n".join(asMemoryTableHTML);
