#!/bin/bash

mkdir -p gen
pushd gen

for C1 in "red" "orange" "yellow" "green"  "blue" "indigo" "violet" "white"
do
 for C2 in "red" "orange" "yellow" "green"  "blue" "indigo" "violet" "white"
 do
  for C3 in "red" "orange" "yellow" "green"  "blue" "indigo" "violet" "white"
  do
KEYWORDS="$C1 $C2 $C3"
TITLE="$KEYWORDS"
NAME=$(echo $TITLE | sed 's/ /_/g' | sed 's/white[_]*//g')
FILENAME="img_$NAME.jpg"
echo "now $FILENAME"

convert -size 100x60 xc:white  \
          -draw "fill $C1  circle 41,39 44,57
                 fill $C2   circle 59,39 56,57
                 fill $C3    circle 50,21 50,3  "  "$FILENAME"

exiv2 -M"set Iptc.Application2.Headline Test image $TITLE" "$FILENAME"
exiv2 -M"set Xmp.dc.description Generated and automatically tagged image $FILENAME" "$FILENAME"
exiv2 -M"set Xmp.dc.subject generated $KEYWORDS" "$FILENAME"


exiv2 -M"set Exif.GPSInfo.GPSLatitude 4/1 15/1 33/1" -M"set Exif.GPSInfo.GPSLatitudeRef N" "$FILENAME"
exiv2 -M"set Exif.GPSInfo.GPSLongitude 4/1 15/1 33/1" -M"set Exif.GPSInfo.GPSLongitudeRef E" "$FILENAME"

  done
 done
done

popd gen
