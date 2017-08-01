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
        max-width: 80em;
      }
      h1, h2, h3, h4, h5 {
        font-weight: 700;
      }
      a {
        color: inherit;
        text-decoration: none;
        margin-bottom: -1px;
      }
      :link {
        border-bottom: 1px dotted rgba(0,0, 238, 0.25);
      }
      :link:hover, :link:active {
        border-bottom: 1px solid rgba(0,0, 238, 1);
      }
      :visited {
        border-bottom: 1px dotted rgba(85, 26, 139, 0.25);
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
      h1 {
        padding: 0.5em 1em 0.5em 1em;
        color: rgba(255, 251, 247, 1);
        background-color: rgba(22, 19, 16, 1);
        font-size: 120%%;
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
      .Block {
        padding: 1em;
        border: 1px solid rgba(22, 19, 16, 0.2);
        border-radius: 0.5em;
        background-color: rgba(255, 251, 247, 1);
        box-shadow: 0 1em   2em rgba(22, 19, 16, 0.2),
                    0 1em   1em rgba(22, 19, 16, 0.05),
                    0 1em 0.5em rgba(22, 19, 16, 0.05);
        margin-bottom: 1em;
        display: block;
      }
      .Content {
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
      .BinaryInformation, .Disassembly, .Memory, .Registers, .Stack {
        white-space: pre;
      }
      .DisassemblyInformation {
      }
      .DisassemblyAddress {
        color: grey;
      }
      .DisassemblyOpcode {
        color: grey;
      }
      .DisassemblyInstruction {
      }
      .MemoryAddress {
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
      .MemoryPointerSymbol {
        padding-left: 0.5em;
      }
      .MemoryRemarks {
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
      <h1 class="BlockHeader">BugId %(sId)s @ %(sBugLocation)s summary<span class="BlockHeaderIcon"></span></h1>
      <div class="Content">
        <table>
          <tr><td>BugId:           </td><td><span class="Important"><b>%(sId)s</b></span></td></tr>
          <tr><td>Location:        </td><td><span class="Important">%(sBugLocation)s</span></td></tr>
%(sOptionalSource)s
          <tr><td>Description:     </td><td><span class="Important">%(sBugDescription)s</span></td></tr>
          <tr><td>Version:         </td><td>%(sBinaryVersion)s</td></tr>
          <tr><td>Security impact: </td><td>%(sSecurityImpact)s</td></tr>
%(sOptionalIntegrityLevel)s
%(sOptionalApplicationArguments)s
        </table>
        <br/>
        <a href="https://github.com/SkyLined/BugId">BugId</a> version <b>%(sBugIdVersion)s</b>. You may not use this
        version of BugId for commercial purposes. Please contact the author if you wish to use BugId commercially.
        Contact and licensing information can be found at the bottom of this report.
      </div>
    </div>
%(sBlocks)s
    <div class="Footer Block">
      <a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/">
        <img alt="Creative Commons License" style="vertical-align: middle; float: left;"
            original-src="https://i.creativecommons.org/l/by-nc/4.0/88x31.png"
            src="data:image/png;base64,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"/>
      </a>
      This report was generated using <a href="https://github.com/SkyLined/BugId">BugId v%(sBugIdVersion)s</a>
        by <a href="mailto:bugid@skylined.nl">SkyLined</a>.<br/>
      BugId is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/">
        Creative Commons Attribution-NonCommercial 4.0 International License</a>.<br/>
      Please contact the author if you wish to use BugId commercially.
    </div>
  </body>
</html>
""").strip("\r\n");
