#!/usr/bin/python

from sys import argv
from json import load, dump

path = argv[1] if len(argv) > 1 else ''


f = open(path, 'r+')
runinfo = load(f)
new_runinfo = {}
for key, item in runinfo.iteritems():
    new_key = str(key.split('00')[-1])
    if new_key:
        new_runinfo[new_key] = runinfo[key]
    try:
        item['dia1hv'] = item.pop('hv dia1')
        item['dia2hv'] = item.pop('hv dia2')
        item['dia1'] = item.pop('diamond 1')
        item['dia2'] = item.pop('diamond 2')
    except KeyError:
        pass
f.seek(0)
dump(new_runinfo, f, indent=2, sort_keys=True)
f.truncate()
f.close()