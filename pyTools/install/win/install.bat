conda config --add channels https://conda.binstar.org/groakat
conda install -y videotagger

REM create shortcut

@echo off

set SCRIPT="%TEMP%\%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"

echo Set oWS = WScript.CreateObject("WScript.Shell") >> %SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\VideoTagger.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "videotagger.exe" >> %SCRIPT%
echo oLink.IconLocation = "%USERPROFILE%\Anaconda\Lib\site-packages\pyTools\icon\3d186778-48ba-11e4-8ece-d88fa9171785.ico" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%

cscript /nologo %SCRIPT%
del %SCRIPT%