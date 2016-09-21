#!/usr/bin/env python

from make import DiamondTable
from sys import argv

z = DiamondTable()
copy_all = False if len(argv) <= 1 else argv[1]
rp = argv[2] if len(argv) > 2 else None
print 'copy all: {0}'.format('TRUE' if copy_all else 'FALSE')
print 'run plan:', rp
z.copy_pics(copy_all, rp)
