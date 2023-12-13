#!/bin/bash
# https://www.tecmint.com/download-and-extract-tar-files-with-one-command/
curl "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key=NQ8j3yBTmaHi2E7i&suffix=tar.gz" | tar -xz -C ./ip_data/GeoLite2 --strip-components=1
