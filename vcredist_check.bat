@echo off
echo Checking for Visual C++ Redistributable...

reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" /v Version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Visual C++ Redistributable 2015-2022 is not installed.
    echo Downloading Visual C++ Redistributable...
    powershell -Command "(New-Object Net.WebClient).DownloadFile('https://aka.ms/vs/17/release/vc_redist.x64.exe', 'vc_redist.x64.exe')"
    echo Installing Visual C++ Redistributable...
    vc_redist.x64.exe /quiet /norestart
    del vc_redist.x64.exe
) else (
    echo Visual C++ Redistributable is already installed.
)

echo Starting TscanSDK...
start TscanSDK.exe 