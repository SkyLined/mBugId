gsCP437 = (
  "\u0000"
  "\u263A"
  "\u263B"
  "\u2665"
  "\u2666"
  "\u2663"
  "\u2660"
  "\u2022"
  "\u25D8"
  "\u25CB"
  "\u25D9"
  "\u2642"
  "\u2640"
  "\u266A"
  "\u266B"
  "\u263C"
  "\u25BA"
  "\u25C4"
  "\u2195"
  "\u203C"
  "\u00B6"
  "\u00A7"
  "\u25AC"
  "\u21A8"
  "\u2191"
  "\u2193"
  "\u2192"
  "\u2190"
  "\u221F"
  "\u2194"
  "\u25B2"
  "\u25BC"
  "\u0020"
  "\u0021"
  "\u0022"
  "\u0023"
  "\u0024"
  "\u0025"
  "\u0026"
  "\u0027"
  "\u0028"
  "\u0029"
  "\u002A"
  "\u002B"
  "\u002C"
  "\u002D"
  "\u002E"
  "\u002F"
  "\u0030"
  "\u0031"
  "\u0032"
  "\u0033"
  "\u0034"
  "\u0035"
  "\u0036"
  "\u0037"
  "\u0038"
  "\u0039"
  "\u003A"
  "\u003B"
  "\u003C"
  "\u003D"
  "\u003E"
  "\u003F"
  "\u0040"
  "\u0041"
  "\u0042"
  "\u0043"
  "\u0044"
  "\u0045"
  "\u0046"
  "\u0047"
  "\u0048"
  "\u0049"
  "\u004A"
  "\u004B"
  "\u004C"
  "\u004D"
  "\u004E"
  "\u004F"
  "\u0050"
  "\u0051"
  "\u0052"
  "\u0053"
  "\u0054"
  "\u0055"
  "\u0056"
  "\u0057"
  "\u0058"
  "\u0059"
  "\u005A"
  "\u005B"
  "\u005C"
  "\u005D"
  "\u005E"
  "\u005F"
  "\u0060"
  "\u0061"
  "\u0062"
  "\u0063"
  "\u0064"
  "\u0065"
  "\u0066"
  "\u0067"
  "\u0068"
  "\u0069"
  "\u006A"
  "\u006B"
  "\u006C"
  "\u006D"
  "\u006E"
  "\u006F"
  "\u0070"
  "\u0071"
  "\u0072"
  "\u0073"
  "\u0074"
  "\u0075"
  "\u0076"
  "\u0077"
  "\u0078"
  "\u0079"
  "\u007A"
  "\u007B"
  "\u007C"
  "\u007D"
  "\u007E"
  "\u2302"
  "\u00C7"
  "\u00FC"
  "\u00E9"
  "\u00E2"
  "\u00E4"
  "\u00E0"
  "\u00E5"
  "\u00E7"
  "\u00EA"
  "\u00EB"
  "\u00E8"
  "\u00EF"
  "\u00EE"
  "\u00EC"
  "\u00C4"
  "\u00C5"
  "\u00C9"
  "\u00E6"
  "\u00C6"
  "\u00F4"
  "\u00F6"
  "\u00F2"
  "\u00FB"
  "\u00F9"
  "\u00FF"
  "\u00D6"
  "\u00DC"
  "\u00A2"
  "\u00A3"
  "\u00A5"
  "\u20A7"
  "\u0192"
  "\u00E1"
  "\u00ED"
  "\u00F3"
  "\u00FA"
  "\u00F1"
  "\u00D1"
  "\u00AA"
  "\u00BA"
  "\u00BF"
  "\u2310"
  "\u00AC"
  "\u00BD"
  "\u00BC"
  "\u00A1"
  "\u00AB"
  "\u00BB"
  "\u2591"
  "\u2592"
  "\u2593"
  "\u2502"
  "\u2524"
  "\u2561"
  "\u2562"
  "\u2556"
  "\u2555"
  "\u2563"
  "\u2551"
  "\u2557"
  "\u255D"
  "\u255C"
  "\u255B"
  "\u2510"
  "\u2514"
  "\u2534"
  "\u252C"
  "\u251C"
  "\u2500"
  "\u253C"
  "\u255E"
  "\u255F"
  "\u255A"
  "\u2554"
  "\u2569"
  "\u2566"
  "\u2560"
  "\u2550"
  "\u256C"
  "\u2567"
  "\u2568"
  "\u2564"
  "\u2565"
  "\u2559"
  "\u2558"
  "\u2552"
  "\u2553"
  "\u256B"
  "\u256A"
  "\u2518"
  "\u250C"
  "\u2588"
  "\u2584"
  "\u258C"
  "\u2590"
  "\u2580"
  "\u03B1"
  "\u00DF"
  "\u0393"
  "\u03C0"
  "\u03A3"
  "\u03C3"
  "\u00B5"
  "\u03C4"
  "\u03A6"
  "\u0398"
  "\u03A9"
  "\u03B4"
  "\u221E"
  "\u03C6"
  "\u03B5"
  "\u2229"
  "\u2261"
  "\u00B1"
  "\u2265"
  "\u2264"
  "\u2320"
  "\u2321"
  "\u00F7"
  "\u2248"
  "\u00B0"
  "\u2219"
  "\u00B7"
  "\u221A"
  "\u207F"
  "\u00B2"
  "\u25A0"
  "\u00A0"
);
def fsCP437FromBytesString(sbData):
  return "".join(gsCP437[uByte] for uByte in sbData);
  
def fsCP437FromByte(uByte):
  return gsCP437[uByte];

asCP437HTML = [
  " ",         "&#9786;",   "&#9787;",   "&#9829;",   "&#9830;",   "&#9827;",   "&#9824;",   "&#8226;",
  "&#9688;",   "&#9675;",   "&#9689;",   "&#9794;",   "&#9792;",   "&#9834;",   "&#9835;",   "&#9788;",
  "&#9658;",   "&#9668;",   "&#8597;",   "&#8252;",   "&#182;",    "&#167;",    "&#9644;",   "&#8616;",
  "&#8593;",   "&#8595;",   "&#8594;",   "&#8592;",   "&#8735;",   "&#8596;",   "&#9650;",   "&#9660;",
  " ",         "!",         "&quot;",    "#",         "$",         "%",         "&amp;",     "'",
  "(",         ")",         "*",         "+",         ",",         "-",         ".",         "/",
  "0"  ,       "1",         "2",         "3",         "4",         "5",         "6",         "7",
  "8",         "9",         ":",         ";",         "&lt;",      "=",         "&gt;",      "?",
  "@",         "A",         "B",         "C",         "D",         "E",         "F",         "G",
  "H",         "I",         "J",         "K",         "L",         "M",         "N",         "O",
  "P",         "Q",         "R",         "S",         "T",         "U",         "V",         "W",
  "X",         "Y",         "Z",         "[",         "\\",        "]",         "^",         "_",
  "`",         "a",         "b",         "c",         "d",         "e",         "f",         "g",
  "h",         "i",         "j",         "k",         "l",         "m",         "n",         "o",
  "p",         "q",         "r",         "s",         "t",         "u",         "v",         "w",
  "x",         "y",         "z",         "{",         "|",         "}",         "~",         "&#8962;",
  "&#199;",    "&#252;",    "&#233;",    "&#226;",    "&#228;",    "&#224;",    "&#229;",    "&#231;",
  "&#234;",    "&#235;",    "&#232;",    "&#239;",    "&#238;",    "&#236;",    "&#196;",    "&#197;",
  "&#201;",    "&#230;",    "&#198;",    "&#244;",    "&#246;",    "&#242;",    "&#251;",    "&#249;",
  "&#255;",    "&#214;",    "&#220;",    "&#162;",    "&#163;",    "&#165;",    "&#8359;",   "&#402;",
  "&#225;",    "&#237;",    "&#243;",    "&#250;",    "&#241;",    "&#209;",    "&#170;",    "&#186;",
  "&#191;",    "&#8976;",   "&#172;",    "&#189;",    "&#188;",    "&#161;",    "&#171;",    "&#187;",
  "&#9617;",   "&#9618;",   "&#9619;",   "&#9474;",   "&#9508;",   "&#9569;",   "&#9570;",   "&#9558;",
  "&#9557;",   "&#9571;",   "&#9553;",   "&#9559;",   "&#9565;",   "&#9564;",   "&#9563;",   "&#9488;",
  "&#9492;",   "&#9524;",   "&#9516;",   "&#9500;",   "&#9472;",   "&#9532;",   "&#9566;",   "&#9567;",
  "&#9562;",   "&#9556;",   "&#9577;",   "&#9574;",   "&#9568;",   "&#9552;",   "&#9580;",   "&#9575;",
  "&#9576;",   "&#9572;",   "&#9573;",   "&#9561;",   "&#9560;",   "&#9554;",   "&#9555;",   "&#9579;",
  "&#9578;",   "&#9496;",   "&#9484;",   "&#9608;",   "&#9604;",   "&#9612;",   "&#9616;",   "&#9600;",
  "&#945;",    "&#946;",    "&#915;",    "&#960;",    "&#931;",    "&#963;",    "&#956;",    "&#964;",
  "&#934;",    "&#920;",    "&#937;",    "&#948;",    "&#8734;",   "&#966;",    "&#949;",    "&#8745;",
  "&#8801;",   "&#177;",    "&#8805;",   "&#8804;",   "&#8992;",   "&#8993;",   "&#247;",    "&#8776;",
  "&#176;",    "&#8729;",   "&#183;",    "&#8730;",   "&#8319;",   "&#178;",    "&#9632;",   " ",
];
def fsCP437HTMLFromBytesString(sbData, u0TabStop = None):
  if u0TabStop is None:
    return "".join(asCP437HTML[uByte] for uByte in sbData);
  sOutput = "";
  uOutputIndex = 0;
  for uByte in sbData:
    if uByte == 9:
      # Add at least one space, then pad the output up to the tab stop.
      while 1:
        sOutput += " ";
        uOutputIndex += 1;
        if uOutputIndex % u0TabStop == 0:
          break;
    else:
      sOutput += asCP437HTML[uByte];
  return sOutput;

def fsCP437HTMLFromChar(sChar):
  uChar = ord(sChar);
  return asCP437HTML[uChar] if uChar < 0x100 else "&#%d;" % uChar;

def fsCP437HTMLFromString(sData, u0TabStop = None):
  sOutput = "";
  if u0TabStop is None:
    return "".join(fsCP437HTMLFromChar(sChar) for sChar in sData);
  uOutputIndex = 0;
  for sChar in sData:
    if sChar == "\t":
      # Add at least one space, then pad the output up to the tab stop.
      while 1:
        sOutput += " ";
        uOutputIndex += 1;
        if uOutputIndex % u0TabStop == 0:
          break;
    else:
      sOutput += fsCP437HTMLFromChar(sChar);
  return sOutput;
    
