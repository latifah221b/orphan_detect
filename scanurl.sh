#!/bin/bash
FILES="tobeScanned_urls/*"
for f in $FILES
do

mkdir -p scan_output/${f:2:4}

echo "Processing $f file..."
n=1
while read url; do
  ./wapiti/venv/bin/python ./wapiti/bin/wapiti -u $url --scop page --scan-force insane  --output "scan_output/${f:2:4}/$n"  --format json
n=$((n+1))
done < $f
done