import os;
from mWindowsAPI import oSystemInfo;

dasPotentialDebuggingToolsPaths_sISA = {"x86": [], "x64": []};

# Add "cdb", "cdb_x86" and "cdb_x64" environment variables if provided:
sDebuggingToolsEnvironmentVariable = os.getenv("DebuggingTools");
if sDebuggingToolsEnvironmentVariable:
  dasPotentialDebuggingToolsPaths_sISA[oSystemInfo.sOSISA].append(sDebuggingToolsEnvironmentVariable.strip('"'));
sDebuggingToolsEnvironmentVariable_x86 = os.getenv("DebuggingTools_x86");
if sDebuggingToolsEnvironmentVariable_x86:
  dasPotentialDebuggingToolsPaths_sISA["x86"].append(sDebuggingToolsEnvironmentVariable_x86.strip('"'));
sDebuggingToolsEnvironmentVariable_x64 = os.getenv("DebuggingTools_x64");
if sDebuggingToolsEnvironmentVariable_x64:
  dasPotentialDebuggingToolsPaths_sISA["x64"].append(sDebuggingToolsEnvironmentVariable_x64.strip('"'));

# Add default installation paths:
sProgramFilesPath_x86 = os.getenv("ProgramFiles(x86)") or os.getenv("ProgramFiles");
sProgramFilesPath_x64 = os.getenv("ProgramW6432");
dasPotentialDebuggingToolsPaths_sISA["x86"].extend([
  os.path.join(sProgramFilesPath_x86, "Windows Kits", "10", "Debuggers", "x86"),
  os.path.join(sProgramFilesPath_x86, "Windows Kits", "8.1", "Debuggers", "x86"),
]);
if oSystemInfo.sOSISA == "x64":
  dasPotentialDebuggingToolsPaths_sISA["x64"].extend([
    os.path.join(sProgramFilesPath_x64, "Windows Kits", "10", "Debuggers", "x64"),
    os.path.join(sProgramFilesPath_x64, "Windows Kits", "8.1", "Debuggers", "x64"),
    os.path.join(sProgramFilesPath_x86, "Windows Kits", "10", "Debuggers", "x64"),
    os.path.join(sProgramFilesPath_x86, "Windows Kits", "8.1", "Debuggers", "x64"),
  ]);

dsDebuggingToolsPath_sISA = {};
for (sISA, asPotentialDebuggingToolsPaths) in dasPotentialDebuggingToolsPaths_sISA.items():
  for sPotentialDebuggingToolsPath in asPotentialDebuggingToolsPaths:
    if os.path.isdir(sPotentialDebuggingToolsPath):
      dsDebuggingToolsPath_sISA[sISA] = sPotentialDebuggingToolsPath;
      break;
