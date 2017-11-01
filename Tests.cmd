@ECHO OFF
SETLOCAL
SET _NT_SYMBOL_PATH=

:: If the user wants to run a full test-suite, new reports will be generated so the old ones must be deleted so as to
:: not leave old reports intermingled with the new ones.
IF "%~1" == "--full" (
  DEL "Tests\Reports\*" /Q
  :: If you can add the x86 and x64 binaries of python to the path, or add links to the local folder, tests will be run
  :: in both
  WHERE PYTHON_X86 2>&1 >nul
  IF ERRORLEVEL 0 (
    WHERE PYTHON_X64 2>&1 >nul
    IF ERRORLEVEL 0 (
      GOTO :TEST_BOTH_ISAS
    )
  )
)

IF DEFINED PYTHON (
  CALL :CHECK_PYTHON
  IF ERRORLEVEL 1 EXIT /B 1
) ELSE (
  REM Try to detect the location of python automatically
  FOR /F "usebackq delims=" %%I IN (`where "python" 2^>nul`) DO SET PYTHON="%%~I"
  IF NOT DEFINED PYTHON (
    REM Check if python is found in its default installation path.
    SET PYTHON="%SystemDrive%\Python27\python.exe"
    CALL :CHECK_PYTHON
    IF ERRORLEVEL 1 EXIT /B 1
  )
)

%PYTHON% "%~dpn0\%~n0.py" %*
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

:CHECK_PYTHON
  REM Make sure path is quoted and check if it exists.
  SET PYTHON="%PYTHON:"=%"
  IF NOT EXIST %PYTHON% (
    ECHO - Cannot find Python at %PYTHON%, please set the "PYTHON" environment variable to the correct path.
    EXIT /B 1
  )
  EXIT /B 0

