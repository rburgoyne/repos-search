@echo off
rem Runs jetty with solr.war

set PORT=8080
echo Jetty port: %PORT%
set JETTY=%cd%
echo Jetty with solr 1.4 webapp: "%JETTY%"

cd "%JETTY%"
cd ..
cd solrhome
set SEARCHHOME=%cd%
echo solr.home: "%SEARCHHOME%"
cd "%JETTY%"

echo "Use Ctrl+C to stop Jetty"
java -Djetty.port=%PORT% -Dsolr.solr.home="%SEARCHHOME%" -jar start.jar
