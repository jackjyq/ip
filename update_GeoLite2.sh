#!/bin/bash
# https://www.tecmint.com/download-and-extract-tar-files-with-one-command/
rm -rf GeoLite2
mkdir GeoLite2
curl "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=NQ8j3yBTmaHi2E7i&suffix=tar.gz"  | tar -xz -C GeoLite2 --strip-components=1
