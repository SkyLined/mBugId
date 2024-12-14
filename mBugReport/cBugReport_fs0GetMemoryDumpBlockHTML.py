import re;

from ..fu0ValueFromCdbHexOutput import fu0ValueFromCdbHexOutput;
from ..mCP437 import fsCP437HTMLFromBytesString;

from .fsGetHTMLForValue import fsGetHTMLForValue;
from .sBlockHTMLTemplate import sBlockHTMLTemplate;

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

def cBugReport_fs0GetMemoryDumpBlockHTML(oBugReport, oCdbWrapper, oProcess, asAddressDescriptionsHTML, uStartAddress, uEndAddress):
  o0VirtualAllocation = oProcess.fo0GetVirtualAllocationForAddress(uStartAddress);
  if not o0VirtualAllocation or o0VirtualAllocation.bFree:
    return None;
  uPointerSizeInBits = oProcess.uPointerSizeInBits;
  uPointerSizeInBytes = oProcess.uPointerSizeInBytes;
  
  asMemoryVirtualAllocationTableHTML = [
    "<tr><td colspan=2><b>Virtual Allocation</b></td></tr>\r\n",
    "<tr><td>Type</td><td>0x%X (%s)</td>\r\n" % (o0VirtualAllocation.uType, o0VirtualAllocation.sType),
    "<tr><td>Base address:</td><td>%s</td>\r\n" % fsGetHTMLForValue(o0VirtualAllocation.uAllocationBaseAddress, uPointerSizeInBits),
    "<tr><td>Start address:</td><td>%s</td>\r\n" % fsGetHTMLForValue(o0VirtualAllocation.uStartAddress, uPointerSizeInBits),
    "<tr><td>End address:</td><td>%s</td>\r\n" % fsGetHTMLForValue(o0VirtualAllocation.uEndAddress, uPointerSizeInBits),
    "<tr><td>Size:</td><td>0x%X</td>\r\n" % o0VirtualAllocation.uSize,
    "<tr><td>State:</td><td>0x%X (%s)</td>\r\n" % (o0VirtualAllocation.uState, o0VirtualAllocation.sState),
    "<tr><td>Protection</td><td>0x%X (%s)</td>\r\n" % (o0VirtualAllocation.uProtection, o0VirtualAllocation.sProtection),
  ];
  uAlignedStartAddress = uStartAddress - (uStartAddress % uPointerSizeInBytes);
  uAlignedEndAddress = uEndAddress + uPointerSizeInBytes - 1 - ((uEndAddress - 1) % uPointerSizeInBytes);
  uAlignedSize = uAlignedEndAddress - uAlignedStartAddress;
  asMemoryTableHTML = [];
  asbMemoryDumpOutput = oProcess.fasbExecuteCdbCommand(
    sbCommand = b"dpp 0x%X L0x%X;" % (uAlignedStartAddress, uAlignedSize),
    sb0Comment = b"Get memory dump for 0x%X-0x%X" % (uStartAddress, uEndAddress),
    bOutputIsInformative = True
  );
  uMaxOffsetSizeInBits = len(bin(uAlignedSize)) - 2;
  bLastLineWasInaccessible = False;
  for sbLine in asbMemoryDumpOutput:
    obMemoryDumpLineMatch = re.match(grbMemoryDumpLine, sbLine);
    assert obMemoryDumpLineMatch, \
        "Unexpected memory dump output: %s" % repr(sbLine);
    (sbAddress, sb0Inaccessible, sbPointerAddress, sb0PointerSymbol) = \
        obMemoryDumpLineMatch.groups();
    asPointerRemarks = [];
    if sb0PointerSymbol:
      # sb0PointerSymbol is actually "pointer sized value at address pointed to" space "symbol at address pointed to"
      # with the later being optional. We are only interested in the symbol, so we drop the first part and set it to
      # none if there is no second part:
      sb0PointerSymbol = b" ".join(sb0PointerSymbol.split(b" ")[1:]);
      if sb0PointerSymbol:
        asPointerRemarks.append(fsCP437HTMLFromBytesString(sb0PointerSymbol));
    uAddress = fu0ValueFromCdbHexOutput(sbAddress);
    asAddressRemarks = oBugReport.fasGetRemarksForRange(uAddress, uPointerSizeInBytes);
    s0AddressDetails = oProcess.fs0GetDetailsForAddress(uAddress);
    if s0AddressDetails:
      asAddressRemarks.append(s0AddressDetails);
    if sb0Inaccessible:
      if bLastLineWasInaccessible:
        if not asAddressRemarks:
          # Nothing to report; skip this.
          continue;
      else:
        bLastLineWasInaccessible = True;
      sMemoryDataHTML = "".join([
        '<td colspan="2" class="MemoryInaccessible">-- inaccessible --</td>',
        '<td class="MemoryDetails">',
          ('<span class="MemoryAddressRemarks">// %s</span>' % ", ".join(asAddressRemarks))
              if asAddressRemarks else "",
        '</td>',
      ]);
    else:
      bLastLineWasInaccessible = False;
      sbHexBytes = sbPointerAddress.replace(b"`", b"");
      uPointerAddress = fu0ValueFromCdbHexOutput(sbHexBytes);
      asPointerRemarks += oBugReport.fasGetRemarksForRange(uPointerAddress, 1);
      s0PointerAddressDetails = oProcess.fs0GetDetailsForAddress(uPointerAddress);
      if s0PointerAddressDetails:
        asPointerRemarks.append(s0PointerAddressDetails);
      sMemoryBytesHTML = '';
      sMemoryCharsHTML = '';
      uOffset = 0;
      sCurrentByteClass = None;
      sCurrentCharClass = None;
      while sbHexBytes:
        # byte prefix/separator
        sBytePrefixHTML = oBugReport.fbByteHasRemarks(uAddress + uOffset) and "*" or " ";
        if sBytePrefixHTML == "*":
          sNewByteClass = "Important";
          if sCurrentByteClass is not sNewByteClass:
            if sCurrentByteClass:
              sMemoryBytesHTML += "</span>";
            sMemoryBytesHTML += '<span class="%s">' % sNewByteClass;
            sCurrentByteClass = sNewByteClass;
        sMemoryBytesHTML += sBytePrefixHTML;
        sNewByteAndCharClass = oBugReport.fbByteHasRemarks(uAddress + uOffset) and "Important" or None;
        # byte
        sByteHTML = fsCP437HTMLFromBytesString(sbHexBytes[-2:]);
        if sCurrentByteClass is not sNewByteAndCharClass:
          if sCurrentByteClass:
            sMemoryBytesHTML += '</span>';
          if sNewByteAndCharClass:
            sMemoryBytesHTML += '<span class="%s">' % sNewByteAndCharClass;
          sCurrentByteClass = sNewByteAndCharClass;
        sMemoryBytesHTML += sByteHTML;
        # char
        sCharHTML = fsCP437HTMLFromBytesString(bytes((int(sbHexBytes[-2:], 16),)));
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
      sMemoryPointerHTML = fsGetHTMLForValue(uPointerAddress, uPointerSizeInBits);

      sMemoryDataHTML = "".join([
        '<td class="MemoryBytes">', sMemoryBytesHTML, '</td>',
        '<td class="MemoryChars">', sMemoryCharsHTML, '</td>',
        '<td class="MemoryPointer', " Important" if asPointerRemarks else "", '">', sMemoryPointerHTML, '</td>',
        '<td class="MemoryDetails">',
          ('<span class="MemoryPointerRemarks">&#8594; %s</span>' % " / ".join(asPointerRemarks))
              if asPointerRemarks else "",
          ('<span class="MemoryAddressRemarks">// %s</span>' % ", ".join(asAddressRemarks))
              if asAddressRemarks else "",
        '</td>',
      ]);
    sLineOffsetHex = "%X" % (uAddress - uAlignedStartAddress);
    sLineOffsetHTML = '<span class="HexNumberHeader">%s</span><span class="HexNumber">%s</span>' % (
        "0" * ((uMaxOffsetSizeInBits >> 3) - len(sLineOffsetHex)),
        sLineOffsetHex, 
      )
    asMemoryTableHTML.append("<tr>%s</tr>" % "".join([
      '<td class="MemoryAddress%s">' % (asAddressRemarks and " Important" or ""),
        fsGetHTMLForValue(uAddress, oProcess.uPointerSizeInBits),
      '</td>',
      '<td class="MemoryOffset">',
        "+", sLineOffsetHTML,
      '</td>',
      sMemoryDataHTML,
    ]));
  return sBlockHTMLTemplate % {
    "sName": "Memory %s" % " / ".join(asAddressDescriptionsHTML),
    "sCollapsed": "Collapsed",
    "sContent": "".join([
      '<table class="MemoryDump"><tbody>\r\n',
      "\r\n".join(asMemoryTableHTML), '\r\n',
      '</tbody></table>\r\n',
      '<table class="MemoryVirtualAllocation"><tbody>\r\n',
      "\r\n".join(asMemoryVirtualAllocationTableHTML), '\r\n',
      '</tbody></table>\r\n',
      "</span>",
    ]),
  };
