import re;

rbSymbolOrAddress = re.compile(
  rb"\A\s*"                                      # optional whitespace
  rb"(?:"                                       # either {
    rb"(?:0x)?"                                 #   optional { "0x" }
    rb"([0-9`a-f]+)"                            #   <<<address>>>
  rb"|"                                         # } or {
    rb"<Unloaded_"                              #   "<Unloaded_"
    rb"(.*)"                                    #   <<<module file name>>>
    rb">"                                       #   ">"
    rb"(?:"                                     #   optional{
      rb"\+0x0*" rb"([0-9`a-f]+?)"              #     "+0x" "0"... <<<hex offset in unloaded module>>>
    rb")?"                                      #   }
  rb"|"                                         # } or {
    rb"(\w+)"                                   #   <<<cdb module id>>>
    rb"(?:"                                     #   optional either {
      rb"\+0x0*" rb"([0-9`a-f]+?)"              #     "+0x" "0"... <<<hex offset in module>>>
    rb"|"                                       #   } or {
      rb"!" rb"(.+?)"                           #     "!" <<<function name>>>
      rb"(?:"                                   #     optional {
      rb"([\+\-])" rb"0x0*" rb"([0-9`a-f]+?)"   #       ["+" or "-"] "0x" "0"... <<<hex offset in function>>>
      rb")?"                                    #     }
    rb")?"                                      #   }
  rb")"                                         # }
  rb"\s*\Z"                                     # optional whitespace
);
