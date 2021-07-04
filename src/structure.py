#!/usr/bin/env python
# --------------------------------------------------------
#       file structure for the website
# created on December 20th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------


from src.info import Data, RunPlan
from src.utils import create_dir, Dir, join


class Structure:

    Dir = join(Dir, 'content')

    @staticmethod
    def make_diamond_dirs():
        d1 = create_dir(Structure.Dir, 'diamonds')
        for dut in Data.DUTs.keys():
            d2 = create_dir(d1, dut)
            for tc in Data.find_tcs(dut):
                d3 = create_dir(d2, tc)
                rps = Data.find_runplans(dut, tc)
                for rp in rps:
                    create_dir(d3, RunPlan.make_str(rp))
                for run in Data.find_runs(rps, tc):
                    create_dir(d3, str(run))

    @staticmethod
    def make_beamtest_dirs():
        d1 = create_dir(Structure.Dir, 'beamtests')
        for tc in Data.TestCampaigns:
            create_dir(d1, tc)

    @staticmethod
    def make_dirs():
        create_dir(Structure.Dir, 'duts')
        Structure.make_beamtest_dirs()
        Structure.make_diamond_dirs()


if __name__ == '__main__':

    d = Data()
    z = Structure()
