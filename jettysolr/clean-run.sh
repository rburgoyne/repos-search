#!/bin/bash

echo "All 'data' dirs:"
find .. -type d -name data

rm -Rfv ../solrhome/svnhead/data
rm -Rfv ../solrhome/svnrev/data

./run.sh
