#!/usr/bin/env python
# --------------------------------------------------------
#       Script to copy all files from analysis to kinder!
# created on September 15th 2016 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from argparse import ArgumentParser
from os import system
from os.path import realpath

parser =  ArgumentParser()
parser.add_argument('-a', '--all', action='store_true')
parser.add_argument('rp',  nargs='?', default=None)
args = parser.parse_args()

print 'copying log_files...'
execfile('copy_logs.py')
print 'copying pickle files and creating data.json...'
execfile('picklecopy.py')
print 'copying{1} pics for {0}...'.format('run ' + args.rp if args.rp is not None else 'all runs', ' all' if args.all else '')
dir =  '/'.join(realpath(__file__).split('/')[:-1])
print dir
system('{dir}/copy_files.py {0} {1}'.format(args.all, args.rp if args.rp is not None else '', dir=dir))