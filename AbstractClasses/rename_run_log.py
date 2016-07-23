#!/usr/bin/python

from sys import argv
from json import load, dump
from datetime import datetime
from collections import OrderedDict

path = argv[1] if len(argv) > 1 else ''
f = open(path, 'r+')
runinfo = load(f)
new_runinfo = OrderedDict()


def find_for_in_comment(info, new_info):
    for name in ['for1', 'for2']:
        if name not in info or info[name] == 0:
            for cmt in info['comments'].split('\r\n'):
                cmt = cmt.replace(':', '')
                cmt = cmt.split(' ')
                if str(cmt[0].lower()) == name:
                    new_info[name] = int(cmt[1])

runinfo = {int(key): value for key, value in runinfo.iteritems()}
for key, item in sorted(runinfo.iteritems()):
    new_key = str(key)
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
dump(new_runinfo, f, indent=2)
f.truncate()
f.close()