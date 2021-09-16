#!/usr/bin/env python
# --------------------------------------------------------
#       file structure for the website
# created on December 20th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------


import src.info as data
from src.utils import create_dir, BaseDir, join


SDir = join(BaseDir, 'content')


def make_diamond_dirs():
    d1 = create_dir(SDir, 'diamonds')
    for tc in data.TestCampaigns.values():
        for dut in tc.DUTs:
            d2 = create_dir(d1, dut)
            d3 = create_dir(d2, tc.ID)
            for run in tc.get_dut_runs(dut):
                create_dir(d3, str(run))
            for rp in tc.get_dut_runplans(dut):
                create_dir(d3, str(rp))


def make_beamtest_dirs():
    d1 = create_dir(SDir, 'beamtests')
    for tc in data.TestCampaigns:
        create_dir(d1, tc)


def make_dirs():
    create_dir(SDir, 'duts')
    make_beamtest_dirs()
    make_diamond_dirs()
