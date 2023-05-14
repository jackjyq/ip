from pprint import pprint

import sh
from whois_parser import WhoisParser

# get whois record
hostname = "120.229.85.185"
whois = sh.Command("whois")
raw_text = whois(hostname)

# parse whois record
parser = WhoisParser()
record = parser.parse(raw_text, hostname=hostname)
pprint(record)
