@ECHO OFF
:: Try to find out where python is installed if it is not provided.
IF NOT DEFINED PYTHON (
  :: See if it's found anywhere in the PATH
  FOR /F "usebackq delims=/" %%I IN (`where python 2^>nul`) DO (
    SET PYTHON=%%I
  )
)
IF NOT DEFINED PYTHON (
  SET PYTHON="%SystemDrive%\Python27\python.exe"
) ELSE (
  SET PYTHON="%PYTHON:"=%"
)
:: Make sure python can be found
IF NOT EXIST %PYTHON% (
  ECHO - Cannot find Python at %PYTHON%, please set the "PYTHON" environment variable to the correct path.
  EXIT /B 1
)
:: If the user wants to run a full test-suite, new reports will be generated so the old ones must be deleted so as to
:: not leave old reports intermingled with the new ones.
IF "%~1" == "--full" (
  DEL "Tests\Reports\*" /Q
)
:: Run tests
%PYTHON% Tests\Tests.py %*