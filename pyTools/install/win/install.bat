@echo off

rem +=====================================================================
rem | Initialisation
rem +=====================================================================

for %%i in ("%~dp0..\envs") do (
    set ANACONDA_ENVS=%%~fi
)

if not "%1" == "" (
    if not exist "%ANACONDA_ENVS%\%1\python.exe" (
        echo No environment named "%1" exists in %ANACONDA_ENVS%
        goto :eof
    )
    set ANACONDA_ENV_NAME=%1
    set ANACONDA="%ANACONDA_ENVS%\%1"
    title Anaconda (%ANACONDA_ENV_NAME%^)
) else (
    set ANACONDA_ENV_NAME=
    for %%i in ("%~dp0..") do (
        set ANACONDA=%%~fi
    )
    title Anaconda
)

set ANACONDA_SCRIPTS=%ANACONDA%\Scripts
set "PATH=%ANACONDA%;%ANACONDA_SCRIPTS%;%PATH%"
echo Added %ANACONDA% and %ANACONDA_SCRIPTS% to PATH.

if not "%ANACONDA_ENV_NAME%" == "" (
    echo Activating environment %ANACONDA_ENV_NAME%...
    set PROMPT=[%ANACONDA_ENV_NAME%] $P$G
)

@echo on

conda config --add channels https://conda.binstar.org/groakat
conda install -y videotagger

REM install simple bat call

copy %ANACONDA%\Lib\site-packages\pyTools\install\win\videotagger.bat %ANACONDA%\Scripts\

REM create shortcut

@echo off

set SCRIPT="%TEMP%\%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"

echo Set oWS = WScript.CreateObject("WScript.Shell") >> %SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\VideoTagger.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%ANACONDA%\Scripts\videotagger.bat" >> %SCRIPT%
echo oLink.IconLocation = "%ANACONDA%\Lib\site-packages\pyTools\icon\3d186778-48ba-11e4-8ece-d88fa9171785.ico" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%

cscript /nologo %SCRIPT%
del %SCRIPT%

pause