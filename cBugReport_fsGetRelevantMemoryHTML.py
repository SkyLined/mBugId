import re;
from dxBugIdConfig import dxBugIdConfig;

def fsHTMLProcessMemoryDumpLine(oCdbWrapper, sLine, uImportantOffset = None):
  oMatch = re.match(r"([0-9a-f`]+)\s+(?:([\?`]+)|([0-9a-f`]+))(?:\s+(.*?))?\s*$", sLine);
  assert oMatch, "Unexpected memory dump output: %s" % repr(sLine);
  (sAddress, bInaccessible, sPointerData, sPointerSymbol) = oMatch.groups();
  if bInaccessible:
    sProcessedLine = " | ".join([
      '<span class="MemoryAddress%s">%s</span>' % \
          (uImportantOffset is not None and " Important" or "", oCdbWrapper.fsHTMLEncode(sAddress)),
      '<span class="MemoryInaccessible">%s</span>' % "-- inaccessible --",
    ]);
  else:
    sByteData = sPointerData.replace("`", "");
    asBytesHTML = [];
    asCharsHTML = [];
    uOffset = 0;
    while sByteData:
      sCharHTML = oCdbWrapper.fsHTMLEncode(chr(long(sByteData[-2:], 16)));
      sByteHTML = oCdbWrapper.fsHTMLEncode(sByteData[-2:]);
      if uImportantOffset is not None and uImportantOffset == uOffset:
        sCharHTML = '<span class="Important">%s</span>' % sCharHTML;
        sByteHTML = '<span class="Important">%s</span>' % sByteHTML;
      uOffset += 1;
      asCharsHTML.append(sCharHTML);
      asBytesHTML.append(sByteHTML);
      sByteData = sByteData[:-2];
    sProcessedLine = " | ".join([
      '<span class="MemoryAddress%s">%s</span>' % \
          (uImportantOffset is not None and " Important" or "", oCdbWrapper.fsHTMLEncode(sAddress)),
      '<span class="MemoryBytes">%s</span> <span class="MemoryChars">%s</span>' % \
          (" ".join(asBytesHTML), "".join(asCharsHTML)),
      '<span class="MemoryPointer">%s</span>%s' % (
        oCdbWrapper.fsHTMLEncode(sPointerData),
        (sPointerSymbol 
          and (' &#8594; <span class="MemoryPointerSymbol">%s</span>' % oCdbWrapper.fsHTMLEncode(sPointerSymbol))
          or ""
        ),
      ),
    ]);
  return sProcessedLine;

def cBugReport_fsGetRelevantMemoryHTML(oBugReport, oCdbWrapper, uAddress, sDescription):
  uPointerSize = oCdbWrapper.fuGetValue("@$ptrsize");
  if not oCdbWrapper.bCdbRunning: return None;
  uAlignedAddress = uAddress - (uAddress % uPointerSize);
  # Get data from the memory the last instruction may have been refering.
  uBeforeAddress = uAlignedAddress - uPointerSize * dxBugIdConfig["uRelevantMemoryPointersBefore"]
  asBeforeReferencedMemory = oCdbWrapper.fasSendCommandAndReadOutput(
    "dpp 0x%X L0x%X; $$ Get memory before address" % (uBeforeAddress, dxBugIdConfig["uRelevantMemoryPointersBefore"]),
    bOutputIsInformative = True,
  );
  if not oCdbWrapper.bCdbRunning: return None;
  asAtAndAfterReferencedMemory = oCdbWrapper.fasSendCommandAndReadOutput(
    "dpp 0x%X L0x%X; $$ Get memory at and after address" % \
        (uAlignedAddress, dxBugIdConfig["uRelevantMemoryPointersAfter"] + 1),
    bOutputIsInformative = True,
  );
  if not oCdbWrapper.bCdbRunning: return None;
  uOffset = uAddress - uAlignedAddress;
  if uOffset != 0:
    sDescription += " (at offset %d)" % uOffset;
  asHTML = [];
  if asBeforeReferencedMemory:
    asHTML += ['<span class="Memory">%s</span>' % fsHTMLProcessMemoryDumpLine(oCdbWrapper, s) for s in asBeforeReferencedMemory];
  if asAtAndAfterReferencedMemory:
    sAtReferencedMemory = asAtAndAfterReferencedMemory.pop(0);
    asAfterReferencedMemory = asAtAndAfterReferencedMemory;
    asHTML += [
      '<span class="Memory">%s</span> <span class="Important">// %s</span>' % (
        fsHTMLProcessMemoryDumpLine(oCdbWrapper, sAtReferencedMemory, uOffset),
        oCdbWrapper.fsHTMLEncode(sDescription)
      )
    ];
    asHTML += ['<span class="Memory">%s</span>' % fsHTMLProcessMemoryDumpLine(oCdbWrapper, s) for s in asAfterReferencedMemory];
  
  return "<br/>".join(asHTML);
