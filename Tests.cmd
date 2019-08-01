@ECHO OFF
SETLOCAL
SET _NT_SYMBOL_PATH=

REM If the user wants to run a full test-suite, new reports will be generated so the old ones must be deleted so as to
REM not leave old reports intermingled with the new ones.
IF "%~1" == "--all" (
  IF EXIST "Tests\Reports\*" (
    DEL "Tests\Reports\*" /Q
  )
  REM If you can add the x86 and x64 binaries of python to the path, or add links to the local folder, tests will be run
  REM in both
  WHERE PYTHON_X86 >nul 2>&1
  IF NOT ERRORLEVEL 0 (
    ECHO - PYTHON_X86 was not found; not testing both x86 and x64 ISAs.
  ) ELSE (
    WHERE PYTHON_X64 >nul 2>&1
    IF NOT ERRORLEVEL 0 (
      ECHO - PYTHON_X64 was not found; not testing both x86 and x64 ISAs.
    ) ELSE (
      GOTO :TEST_BOTH_ISAS
    )
  )
)

WHERE PYTHON 2>&1 >nul
IF ERRORLEVEL 1 (
  ECHO - PYTHON was not found!
  EXIT /B 1
)

CALL PYTHON "%~dpn0\%~n0.py" %*
IF ERRORLEVEL 1 GOTO :ERROR
ENDLOCAL
EXIT /B 0

:TEST_BOTH_ISAS
  ECHO * Running tests in x86 build of Python...
  CALL PYTHON_X86 "%~dpn0\%~n0.py" %*
  IF ERRORLEVEL 1 GOTO :ERROR
  ECHO * Running tests in x64 build of Python...
  CALL PYTHON_X64 "%~dpn0\%~n0.py" %*
  IF ERRORLEVEL 1 GOTO :ERROR
  ENDLOCAL
  EXIT /B 0

:ERROR
  ECHO    - Error %ERRORLEVEL%
  EXIT /B %ERRORLEVEL%
