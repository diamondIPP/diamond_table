#!/usr/bin/env python
# --------------------------------------------------------
#       Script to create all html tables created by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from make import DiamondTable, Table
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('tc', nargs='?', default=None)
parser.add_argument('dia', nargs='?', default=None)
args = parser.parse_args()

a = Table()
a.set_global_vars(args.tc, args.dia)
t = DiamondTable()

t.DiaTable.create_all()
t.RunPlanTable.create_tc_overview()
# t.create_overview()
t.RunPlanTable.create_dia_overview()
t.RunTable.create_overview()
