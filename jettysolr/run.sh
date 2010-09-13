#!/bin/sh

# Runs jetty with solr.war
# and solr.home pointing to Repos Search cores 

PORT=8080
echo "Jetty port: $PORT"

JETTY=$(pwd)
echo "Jetty with solr 1.4 webapp: $JETTY"

SEARCHHOME=$(pwd)/../solrhome
echo "solr.home: $SEARCHHOME"

cd $JETTY
echo "Use Ctrl+C to stop Jetty"
java -Djetty.port=$PORT -Dsolr.solr.home=$SEARCHHOME -jar start.jar
# java -Djetty.port=$PORT -Dsolr.solr.home=$SEARCHHOME -jar start.jar etc/jetty.xml etc/jetty-ajp.xml
cd ..