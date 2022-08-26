sReportHTMLTemplate = ("""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge"/> 
    <meta http-equiv="Content-Security-Policy" content="disown-opener; referrer no-referrer;"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <meta name="twitter:card" content="summary"/>
    <meta name="twitter:site" content="@berendjanwever"/>
    <meta name="twitter:title" content="%(sId)s @ %(sBugLocation)s"/>
    <meta name="twitter:description" content="%(sBugDescription)s"/>
    <title>%(sId)s @ %(sBugLocation)s</title>
    <style>
      * {
        border: 0;
        margin: 0;
        padding: 0;
        border-spacing: 0;
        border-collapse: collapse;
        color: inherit;
        background: transparent;
        word-wrap: break-word;
        overflow-wrap: break-word;
        font-size: inherit;
      }
      html {
        overflow-y: scroll; /* prevent center jumping */
        color: rgba(22, 19, 16, 1);
        background: #E5E2DE;
        font-weight: 400;
        padding: 1em;
        font-family: Monospace;
      }
      body {
        margin: auto;
      }
      h2, h3, h4, h5 {
        font-weight: 700;
      }
      a {
        color: inherit;
        text-decoration: none;
        margin-bottom: -1px;
      }
      :link {
        border-bottom: 1px dotted rgba(0,0, 238, 0.5);
      }
      :link:hover, :link:active {
        border-bottom: 1px solid rgba(0,0, 238, 1);
      }
      :visited {
        border-bottom: 1px dotted rgba(85, 26, 139, 0.5);
      }
      :visited:hover, :visited:active {
        border-bottom: 1px solid rgba(85, 26, 139, 1);
      }
      table {
        border-spacing: 0;
        border-collapse: collapse;
      }
      ul, ol {
        padding-left: 2em;
      }
      .BlockHeader {
        padding: 0.5em 1em 0.5em 1em;
        color: rgba(255, 251, 247, 1);
        background-color: rgba(22, 19, 16, 1);
        font-size: 120%%;
        font-weight: 700;
        margin-bottom: 0.5em;
      }
      h2 {
        font-size: 120%%;
      }
      td:first-child {
        white-space: pre;
      }
      td {
        vertical-align: top;
      }
      sup, sub {
        font-size: 50%%;
      }
      hr {
        border: dotted black;
        border-width: 0 0 1pt 0;
      }
      .HexNumberHeader {
        opacity: 0.25;
      }
      .Block {
        margin-bottom: 0.5em;
        padding: 1em;
        border: 1px solid rgba(22, 19, 16, 0.2);
        border-radius: 0.5em;
        background-color: rgba(255, 251, 247, 1);
        box-shadow: 0 1em   2em rgba(22, 19, 16, 0.2),
                    0 1em   1em rgba(22, 19, 16, 0.05),
                    0 1em 0.5em rgba(22, 19, 16, 0.05);
        display: block;
      }
      .Content {
        margin-top: 1em;
        overflow-x: auto;
      }
      .Collapsible > .Content,
      .Collapsed > .CollapsedPlaceholder {
        display: block;
      }
      .Collapsible > .CollapsedPlaceholder,
      .Collapsed > .Content {
        display: none;
      }
      .BlockHeaderIcon {
        float: right;
        vertical-align: top;
        border: 1px solid rgba(255, 251, 247, 1);
      }
      .Collapsible .BlockHeaderIcon {
        padding: 1px 0.8em 0 0;
      }
      .Collapsed .BlockHeaderIcon {
        padding: 0.8em 0.8em 0 0;
      }
      .Footer {
        padding: 1em;
        text-align: center;
      }
      .Important {
        background-color: rgba(255,255,0,0.3);
      }
      .SecurityImpact {
        background-color: rgba(255,0,0,0.2);
      }
      .CDBPrompt {
        white-space: pre;
      }
      .CDBCommand {
        font-weight: bold;
        white-space: pre;
      }
      .CDBComment {
        font-weight: bold;
        white-space: pre;
        background-color: rgba(255,255,0,0.1);
      }
      .CDBCommandResult {
        font-weight: bold;
        white-space: pre;
      }
      .CDBStdOut {
        color: grey;
        white-space: pre;
      }
      .CDBOrApplicationStdOut {
        font-weight: bold;
        color: navy;
        background-color: rgba(255,255,0,0.3);
        white-space: pre;
      }
      .CDBStdErr {
        color: maroon;
        white-space: pre;
      }
      .CDBIgnoredException {
        color: grey;
        white-space: pre;
      }
      .BinaryInformation, .MemoryDump, .Registers, .Stack {
        white-space: pre;
      }
      .DisassemblyAddress {
        color: grey;
        padding-right: 0.5em;
        border-right: 1px solid silver;
      }
      .DisassemblyOpcode {
        padding-left: 0.5em;
        color: grey;
        padding-right: 0.5em;
        border-right: 1px solid silver;
      }
      .DisassemblyInstructionName {
        padding-left: 0.5em;
        padding-right: 0.5em;
      }
      .DisassemblyInstructionArguments {
        padding-left: 0.5em;
        padding-right: 0.5em;
      }
      .DisassemblyInstructionRemark {
        padding-left: 0.5em;
      }
      .MemoryAddress {
        color: grey;
        padding-right: 0.5em;
      }
      .MemoryOffset {
        color: grey;
        padding-right: 0.5em;
      }
      .MemoryInaccessible {
        color: grey;
        text-align: center;
      }
      .MemoryBytes {
        padding-left: 0.5em;
        padding-right: 0.5em;
      }
      .MemoryChars {
        padding-left: 0.5em;
        padding-right: 0.5em;
      }
      .MemoryPointer {
        padding-left: 0.5em;
        padding-right: 0.5em;
      }
      .MemoryDetails {
      }
      .MemoryPointerSymbol {
        padding-left: 0.5em;
        background-color: rgba(0,255,255,0.3);
      }
      .MemoryRemarks {
        padding-left: 0.5em;
        background-color: rgba(255,255,0,0.3);
      }
      .StackFrame {
      }
      .StackFrameInline {
        color: silver;
      }
      .StackFrameHidden {
        color: silver;
      }
      .StackFramePartOfId {
        background-color: rgba(255,255,0,0.3);
        font-weight: bold;
      }
      .StackFrameWithoutSymbol {
        font-style: italic;
      }
      .StackFrameNotes {
      }
      .StackFrameSource {
        color: grey;
      }
      .LogProcess {
      }
      .LogException {
      }
      .LogBreakpoint {
      }
      .LogEmbeddedCommandsBreakpoint {
      }
      .LogStdErrOutput {
        color: maroon;
      }
      .LogImportantStdErrOutput {
      }
      .LogStdOutOutput {
        font-weight: bold;
      }
      .LogImportantStdOutOutput {
      }
      .LogMessage {
      }
    </style>
    <script>
      function fAddClickHandler(oBlockHeaderElement) {
        var oBlockElement = oBlockHeaderElement.parentElement,
            bCollapsedPlaceholdersRemoved = false;
        oBlockHeaderElement.onclick = function () {
          oBlockElement.className = oBlockElement.className.replace(
            /\\b(Collapsed|Collapsible)\\b/,
            function (sCurrentClassName) {
              return {"Collapsible": "Collapsed", "Collapsed": "Collapsible"}[sCurrentClassName];
            }
          );
          if (!bCollapsedPlaceholdersRemoved) {
            // A copy of this list is needed as it is dynamic and we plan to remove elements.
            var aoCollapsedPlaceholderElements = Array.prototype.slice.call(document.getElementsByClassName("CollapsedPlaceholder"));
            for (var u = 0; u < aoCollapsedPlaceholderElements.length; u++) {
              var oCollapsedPlaceholderElement = aoCollapsedPlaceholderElements[u];
              oCollapsedPlaceholderElement.parentNode.removeChild(oCollapsedPlaceholderElement);
            };
          };
        };
      };
      onload = function() {
        var aoBlockHeaderElements = document.getElementsByClassName("BlockHeader");
        for (var u = 0; u < aoBlockHeaderElements.length; u++) {
          fAddClickHandler(aoBlockHeaderElements[u]);
        };
      };
    </script>
  </head>
  <body>
    <div class="Block Collapsible">
      <div class="BlockHeader">BugId %(sId)s @ %(sBugLocation)s summary<span class="BlockHeaderIcon"></span></div>
      <div class="Content">
        <table>
          <tr><td>BugId:           </td><td><span class="Important"><b>%(sId)s</b></span></td></tr>
%(sOptionalUniqueStackId)s
%(sOptionalInstruction)s
          <tr><td>Description:     </td><td><span class="Important">%(sBugDescription)s</span></td></tr>
          <tr><td>Security impact: </td><td>%(sSecurityImpact)s</td></tr>
%(sOptionalIntegrityLevel)s
%(sOptionalMemoryUsage)s
          <tr><td>Location:        </td><td><span class="Important">%(sBugLocation)s</span></td></tr>
%(sOptionalSource)s
%(sOptionalApplicationArguments)s
        </table>
        <br/>
        %(sProductHeader)s
        %(sLicenseHeader)s
      </div>
    </div>
%(sBlocks)s
    <div class="Footer Block">
      %(sProductFooter)s
      %(sLicenseFooter)s
    </div>
  </body>
</html>
""").strip("\r\n");
