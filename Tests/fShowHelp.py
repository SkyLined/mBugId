INFO = 0xFF0F;
NORMAL = 0xFF07;

def fShowHelp(oConsole):
  oConsole.fOutput("Usage:");
  oConsole.fOutput(" ", INFO, "Tests [Arguments] [ISA [test command line arguments]]");
  oConsole.fOutput("Where:");
  oConsole.fOutput(" ", INFO, "ISA", NORMAL, " (optional)");
  oConsole.fOutput(" ", "Select an Instruction Set Architecture to run tests for.");
  oConsole.fOutput(" ", "Valid values: ", INFO, "x86", NORMAL, " and ", INFO, "x64", NORMAL, ".");
  oConsole.fOutput(" ", INFO, "test command line arguments", NORMAL, " (optional)");
  oConsole.fOutput(" ", "Provide command line arguments to pass to Tests\\bin\\Tests_*.exe.");
  oConsole.fOutput(" ", "If provided, a single test is run with the given command line arguments,");
  oConsole.fOutput(" ", "instead of the normal test suit.");
  oConsole.fOutput(" ", "(Run ", INFO, "Tests\\bin\\Tests_*.exe --help", NORMAL, " for more details)");
  oConsole.fOutput(" ", "Valid values: ", INFO, "x86", NORMAL, " and ", INFO, "x64", NORMAL, ".");
  oConsole.fOutput("Arguments:");
  oConsole.fOutput(" ", INFO, "--quick");
  oConsole.fOutput(" ", "Run shortened suite of basic tests.");
  oConsole.fOutput(" ", INFO, "--full");
  oConsole.fOutput(" ", "Run full suite of extended tests.");
  oConsole.fOutput(" ", INFO, "--reports");
  oConsole.fOutput(" ", "Generate reports for all tests.");
  oConsole.fOutput(" ", INFO, "--show-cdb-io");
  oConsole.fOutput(" ", "Show cdb input/output during each test.");
  oConsole.fOutput(" ", INFO, "--debug");
  oConsole.fOutput(" ", "Output debug messages during each test.");
  oConsole.fOutput(" ", INFO, "--reports");
  oConsole.fOutput(" ", "Generate reports for all tests.");
  