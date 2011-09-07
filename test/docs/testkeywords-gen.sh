#!/bin/bash

mkdir -p gen
pushd gen

# http://wiki.openstreetmap.org/wiki/Photo_mapping
if [ ! -e ./geoexif.py ]
then
 wget http://www.sethoscope.net/geophoto/geoexif.py
 chmod u+x geoexif.py
fi

for C1 in "green" "red" "blue" "white"
do
 for C2 in "green" "red" "blue" "white"
 do
  for C3 in "green" "red" "blue" "white"
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

exiv2 -M"set Iptc.Application2.Headline Test image $title" "$FILENAME"
exiv2 -M"set Xmp.dc.description Generated and automatically tagged image $FILENAME" "$FILENAME"
exiv2 -M"set Xmp.dc.subject generated $title" "$FILENAME"

python geoexif.py -l 10.50 -n -21.00 "$FILENAME"

  done
 done
done

rm geoexif.py

popd gen
