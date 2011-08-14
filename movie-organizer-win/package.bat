rmdir /S /Q install
mkdir install
mkdir install\movie-organizer
copy src\dist\*.* install\movie-organizer
mkdir install\movie-organizer\res
copy src\dist\res\*.* install\movie-organizer\res\
copy progs\Autorun.inf install\
copy progs\movie-organizer.exe install\
copy progs\README.txt install\
xcopy /S progs\VLC install\VLC\
mkdir install\Movies
pause
