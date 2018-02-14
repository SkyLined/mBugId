@ECHO OFF
SETLOCAL
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

IF EXIST "%~dp0\..\mProductVersionAndLicense\Version.py" (
  %PYTHON% "%~dp0\..\mProductVersionAndLicense\Version.py" update --product="%~dp0."
) ELSE IF EXIST "%~dp0\modules\mProductVersionAndLicense\Version.py" (
  %PYTHON% "%~dp0\modules\mProductVersionAndLicense\Version.py" update --product="%~dp0."
) ELSE (
  ECHO - Cannot find mProductVersionAndLicense folder!
  EXIT /B 1
);

ENDLOCAL & EXIT /B %ERRORLEVEL%

:CHECK_PYTHON
  REM Make sure path is quoted and check if it exists.
  SET PYTHON="%PYTHON:"=%"
  IF NOT EXIST %PYTHON% (
    ECHO - Cannot find Python at %PYTHON%, please set the "PYTHON" environment variable to the correct path.
    EXIT /B 1
  )
  EXIT /B 0
