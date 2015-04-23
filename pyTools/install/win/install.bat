conda config --add channels https://conda.binstar.org/groakat
conda install -y videotagger

REM install simple bat call

copy %USERPROFILE%\Anaconda\Lib\site-packages\pyTools-0.1.0-py2.7.egg\pyTools\install\win\videotagger.bat %USERPROFILE%\Anaconda\Scripts\

REM create shortcut

@echo off

set SCRIPT="%TEMP%\%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"

echo Set oWS = WScript.CreateObject("WScript.Shell") >> %SCRIPT%
echo sLinkFile = "%USERPROFILE%\Desktop\VideoTagger.lnk" >> %SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
echo oLink.TargetPath = "%USERPROFILE%\Anaconda\Scripts\videotagger.bat" >> %SCRIPT%
echo oLink.IconLocation = "%USERPROFILE%\Anaconda\Lib\site-packages\pyTools-0.1.0-py2.7.egg\pyTools\icon\3d186778-48ba-11e4-8ece-d88fa9171785.ico" >> %SCRIPT%
echo oLink.Save >> %SCRIPT%

cscript /nologo %SCRIPT%
del %SCRIPT%

pause