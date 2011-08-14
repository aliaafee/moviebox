mkdir src
mkdir src\dist
mkdir src\dist\res
copy /Y ..\res\*.* src\dist\res
copy ..\license.txt src\dist\
copy /Y ..\movie-organizer\*.py src\
copy /Y setup.py src\
copy /Y dlls\msvcp90.dll src\
cd src
C:\Python27\python.exe setup.py py2exe
del dist\movie-organizer.exe
ren dist\__main__.exe movie-organizer.exe
pause
