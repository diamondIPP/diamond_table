#!/usr/bin/env python
# --------------------------------------------------------
#       Script to create all html tables created by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from make_website import Website
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('tc', nargs='?', default=None)
parser.add_argument('dia', nargs='?', default=None)
args = parser.parse_args()

w = Website()
w.Diamond = args.dia
w.TestCampaign = args.tc
# w.update()
w.build()
