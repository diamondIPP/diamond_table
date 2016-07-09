#!/usr/bin/python

from sys import argv
from json import load, dump

path = argv[1] if len(argv) > 1 else ''
f = open(path, 'r+')
runinfo = load(f)
new_runinfo = {}

def find_for_in_comment(info, new_info):
    for name in ['for1', 'for2']:
        if not name in info:
            for cmt in info['user comments'].split('\r\n'):
                cmt = cmt.replace(':', '')
                cmt = cmt.split(' ')
                if str(cmt[0].lower()) == name:
                    new_runinfo[name] = int(cmt[1])


for key, item in runinfo.iteritems():
    new_key = str(key.split('00')[-1])
    if new_key:
        new_runinfo[new_key] = runinfo[key]
    find_for_in_comment(item, new_runinfo[new_key])
    try:
        item['maskfile'] = item.pop('mask')
        item['runtype'] = item.pop('type')
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