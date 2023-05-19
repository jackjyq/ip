#!/bin/bash
# https://www.tecmint.com/download-and-extract-tar-files-with-one-command/
mkdir ip_data
cd ip_data
mkdir GeoLite2
curl "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=NQ8j3yBTmaHi2E7i&suffix=tar.gz" | tar -xz -C GeoLite2 --strip-components=1
mkdir ip2region
curl "https://github.com/lionsoul2014/ip2region/raw/master/data/ip2region.xdb" -o ./ip2region/ip2region.xdb --user-agent "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.42"
