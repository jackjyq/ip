#!/bin/bash
# https://www.tecmint.com/download-and-extract-tar-files-with-one-command/
cd ip_data
mkdir GeoLite2
curl "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=NQ8j3yBTmaHi2E7i&suffix=tar.gz"  | tar -xz -C GeoLite2 --strip-components=1
mkdir ip2region
curl "https://raw.githubusercontent.com/lionsoul2014/ip2region/master/data/ip2region.db" -o ./ip2region/ip2region.db