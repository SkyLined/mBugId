@ECHO OFF
chcp 65001 >nul
:: Administrator prompt text is white on blue for clarity
FSUTIL dirty query %SystemDrive% >nul
:: If we are already elevated, just change color, execute command, and exit
IF ERRORLEVEL 1 (
  ECHO • Restarting with elevated privileges....
  POWERSHELL Start-Process -Verb "RunAs" -FilePath %ComSpec% -ArgumentList @^('/C', '%~f0'^) >nul
  IF ERRORLEVEL 1 GOTO :ERROR
) ELSE (
  ECHO • Enabling page heap for the testing binary...
  "%WinDir%\System32\reg.exe" ADD "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\BugIdTests.exe" /v "GlobalFlag" /t REG_SZ /d "0x02109870" /f >nul
  IF ERRORLEVEL 1 GOTO :ERROR
  ECHO ✓ Page heap is now enabled for the testing binary.
)
EXIT /B 0

:TURN_PAGEHEAP_ON_FOR
  IF ERRORLEVEL 1 (
    ECHO ✘ Cannot enable page heap for %~1!
    EXIT /B 1
  )

  ECHO ✓ Enabled page heap for %~1.
  EXIT /B 0

:ERROR 
  ECHO ✘ Error %ERRORLEVEL%!
  EXIT /B 1