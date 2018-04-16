@ECHO OFF
IF "%~1" == "" (
  ECHO Usage:
  ECHO %~nx0 ^<path-to-license-file^>
) ELSE IF EXIST "%~dp0\..\mProductDetails\License.cmd" (
  "%~dp0\..\mProductDetails\License.cmd" register --product="%~dp0." --license="%~1"
) ELSE IF EXIST "%~dp0\modules\mProductDetails\License.cmd" (
  "%~dp0\modules\mProductDetails\License.cmd" register --product="%~dp0." --license="%~1"
) ELSE (
  ECHO - Cannot find mProductDetails folder!
  EXIT /B 1
);

EXIT /B %ERRORLEVEL%
