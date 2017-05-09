@ECHO OFF
SET _NT_SYMBOL_PATH=
IF "%~1" == "--full" (
  DEL "Tests\Reports\*" /Q
)
PYTHON Tests\Tests.py %*