@ECHO OFF
SETLOCAL

IF "%~1" == "--full" GOTO :RUN_FULL_TESTS

IF DEFINED PYTHON (
  CALL :CHECK_PYTHON "%PYTHON:"=%"
  IF ERRORLEVEL 1 (
    ECHO - The environment variable PYTHON is defined as %PYTHON% but that is not an existing file.
    EXIT /B 1
  )
  GOTO :RUN_CHECKED_PYTHON
)
IF DEFINED PYTHON_X86 (
  CALL :CHECK_PYTHON "%PYTHON_X86:"=%"
  IF ERRORLEVEL 1 (
    ECHO - The environment variable PYTHON_X86 is defined as %PYTHON_X86% but that is not an existing file.
    EXIT /B 1
  )
  GOTO :RUN_CHECKED_PYTHON
)
IF DEFINED PYTHON_X64 (
  CALL :CHECK_PYTHON "%PYTHON_X64:"=%"
  IF ERRORLEVEL 1 (
    ECHO - The environment variable PYTHON_X64 is defined as %PYTHON_X64% but that is not an existing file.
    EXIT /B 1
  )
  GOTO :RUN_CHECKED_PYTHON
)
IF DEFINED PYTHON3 (
  CALL :CHECK_PYTHON "%PYTHON3:"=%"
  IF ERRORLEVEL 1 (
    ECHO - The environment variable PYTHON3 is defined as %PYTHON3% but that is not an existing file.
    EXIT /B 1
  )
  GOTO :RUN_CHECKED_PYTHON
)
IF DEFINED PYTHON3_X86 (
  CALL :CHECK_PYTHON "%PYTHON3_X86:"=%"
  IF ERRORLEVEL 1 (
    ECHO - The environment variable PYTHON3_X86 is defined as %PYTHON3_X86% but that is not an existing file.
    EXIT /B 1
  )
  GOTO :RUN_CHECKED_PYTHON
)
IF DEFINED PYTHON3_X64 (
  CALL :CHECK_PYTHON "%PYTHON3_X64:"=%"
  IF ERRORLEVEL 1 (
    ECHO - The environment variable PYTHON3_X64 is defined as %PYTHON3_X64% but that is not an existing file.
    EXIT /B 1
  )
  GOTO :RUN_CHECKED_PYTHON
)
REM Try to detect the location of python automatically
FOR /F "usebackq delims=" %%I IN (`where "python" 2^>nul`) DO (
  CALL :CHECK_PYTHON "%%~fI"
  IF NOT ERRORLEVEL 1 GOTO :RUN_CHECKED_PYTHON
)
REM Try to detect the location of python automatically
FOR /F "usebackq delims=" %%I IN (`where "python3" 2^>nul`) DO (
  CALL :CHECK_PYTHON "%%~fI"
  IF NOT ERRORLEVEL 1 GOTO :RUN_CHECKED_PYTHON
)
REM Check if python is found in its default installation path.
FOR /D %%I IN ("%LOCALAPPDATA%\Programs\Python\*") DO (
  CALL :CHECK_PYTHON "%%~fI\python.exe"
  IF NOT ERRORLEVEL 1 GOTO :RUN_CHECKED_PYTHON
)
ECHO - Cannot find python.exe, please set the "PYTHON" environment variable to the
ECHO   correct path, or add Python to the "PATH" environment variable.
EXIT /B 1

:CHECK_PYTHON
  REM Make sure path is quoted and check if it exists.
  SET CHECKED_PYTHON="%~1"
  IF NOT EXIST %CHECKED_PYTHON% EXIT /B 1
  EXIT /B 0

:RUN_CHECKED_PYTHON
  ECHO + Running tests using %CHECKED_PYTHON%...
  CALL %CHECKED_PYTHON% "%~dpn0.py" %*
  IF ERRORLEVEL 1 GOTO :ERROR
  
  ECHO + Running tests using %CHECKED_PYTHON% with redirected output...
  ECHO.|CALL %CHECKED_PYTHON% "%~dpn0.py" %* >nul
  IF ERRORLEVEL 1 GOTO :ERROR
  
  ECHO + Done.
  ENDLOCAL
  EXIT /B 0

:RUN_FULL_TESTS
  CALL :CHECK_PYTHON "PYTHON3_X86"
  IF ERRORLEVEL 1 (
    CALL :CHECK_PYTHON "%PYTHON3_X86:"=%"
    IF ERRORLEVEL 1 (
      ECHO - Python3 for x86 could not be found.
      EXIT /B 1
    )
  )
  ECHO + Running tests using %CHECKED_PYTHON%...
  CALL %CHECKED_PYTHON% "%~dpn0.py" %*
  IF ERRORLEVEL 1 GOTO :ERROR
  
  ECHO + Running tests using %CHECKED_PYTHON% with redirected output...
  ECHO.|CALL %CHECKED_PYTHON% "%~dpn0.py" %* >nul
  IF ERRORLEVEL 1 GOTO :ERROR
  
  CALL :CHECK_PYTHON "PYTHON3_X64"
  IF ERRORLEVEL 1 (
    CALL :CHECK_PYTHON "%PYTHON3_X64:"=%"
    IF ERRORLEVEL 1 (
      ECHO - Python3 for x86 could not be found.
      EXIT /B 1
    )
  )
  GOTO :RUN_CHECKED_PYTHON

:ERROR
  ECHO   - Failed with error %ERRORLEVEL%!
  ENDLOCAL
  EXIT /B %ERRORLEVEL%
