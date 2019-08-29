#!/usr/bin/env python
# --------------------------------------------------------
#       script to create all the html files for the complete website
# created on December 20th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from sys import path
path.append('src')

from homepage import HomePage
from Utils import *
from os.path import dirname, realpath
from YearTable import YearTable
from json import loads
import HTMLTable
from OldTable import OldTable
from RunPlanTable import RunPlanTable
from DiaTable import DiaTable
from RunTable import RunTable
from time import time
from os import system
from argparse import ArgumentParser
from PicturePage import PicturePage


class Website:

    def __init__(self, dia=None, tc=None):

        self.Dir = dirname(realpath(__file__))
        self.HomePage = HomePage(filename='default')
        self.Config = self.HomePage.Config
        self.BkgCol = 'lightgrey'  # TODO FIX

        self.Diamond = RunPlanTable().load_diamond(dia)
        # in string format! Aug16
        self.TestCampaign = RunPlanTable().load_test_campaign(tc)

    def get_diamonds(self):
        t = RunPlanTable()
        if self.Diamond is None:
            return t.Diamonds if self.TestCampaign is None else t.DiaScans.get_tc_diamonds(tc=str_to_tc(self.TestCampaign))
        return [self.Diamond]

    def update_run_plans(self):
        cmd = 'rsync -aP mutter:/home/reichmann/software/RatePadAnalysis/Runinfos/run_plans.json {}'.format(join(self.Dir, 'data'))
        system(cmd)

    def update_irradiation_file(self):
        cmd = 'rsync -aP mutter:/home/reichmann/software/RatePadAnalysis/Runinfos/irradiation.json {}'.format(join(self.Dir, 'data'))
        system(cmd)

    def update_diamond_aliases(self):
        cmd = 'rsync -aP mutter:/home/reichmann/software/RatePadAnalysis/Configuration/DiamondAliases.cfg {}'.format(join(self.Dir, 'data'))
        system(cmd)

    def update_masks(self):
        cmd = 'rsync -aP mutter:/scratch2/psi/psi*/masks/*.msk {}'.format(join(self.Dir, 'masks'))
        system(cmd)

    def update_run_log(self, tc):
        psi_dir = 'psi_{}_{}'.format(tc[:4], tc[4:])
        cmd = 'rsync -aP mutter:/scratch2/psi/{}/run_log.json {}'.format(psi_dir, join(self.Dir, 'data', 'run_log{}.json'.format(tc)))
        system(cmd)

    def update_run_logs(self):
        for tc in self.HomePage.TestCampaigns:
            if tc > '201505':
                self.update_run_log(tc)

    def update(self):
        self.update_run_plans()
        self.update_irradiation_file()
        self.update_diamond_aliases()
        self.update_masks()
        self.update_run_logs()

    @staticmethod
    def create_home():
        h = HomePage('HomePage')
        body = '{}\n'.format(make_lines(3))
        body += '{}\n'.format(head(bold('Complete Set of Data Taken at Beam Tests at PSI ...')))
        body += '  <script type="text/javascript">\n'
        body += '    load_home();\n'
        body += '  </script>\n'
        h.set_body(indent(body, 2))
        h.create()

    @staticmethod
    def create_location():
        h = HomePage('Location')
        body = '{}\n'.format(make_lines(3))
        body += '{}\n'.format(head(bold('Paul Scherrer Institut (PSI)')))
        body += make_figure(join('figures', 'PSIAir.jpg'), 'PSI-Air', width=1200)
        h.set_body(indent(body, 2))
        h.create()

    def create_boards(self):
        h = HomePage('AmpBoards')
        body = '{}\n'.format(make_lines(3))
        body += '{}\n'.format(head(bold('Diamond Amplifier Boards')))
        rows = sorted([[center_txt(nr), option] for option in self.Config.options('Boards') for nr in loads(self.Config.get('Boards', option))])
        body += add_bkg(HTMLTable.table(rows, header_row=['Nr', 'Pulser Type'], ), self.BkgCol)
        h.set_body(body)
        h.create()

    @staticmethod
    def create_old():
        h = HomePage('Old')
        table = OldTable()
        h.set_body(table.get_body())
        h.create()

    def create_years(self):
        for year in self.HomePage.get_years():
            if year.isdigit():
                h = HomePage(year)
                table = YearTable(year)
                h.set_body(table.get_body())
                h.create()
                
    def create_dia_runplans(self):
        table = RunPlanTable()
        print_banner('CREATING DIAMOND RUNPLAN TABLES')
        diamonds = self.get_diamonds()
        test_campaigns = [str_to_tc(tc) for tc in table.TestCampaigns] if self.TestCampaign is None else [str_to_tc(self.TestCampaign)]
        for dia in diamonds:
            for tc in test_campaigns:
                dia_scans = table.DiaScans.get_tc_diamond_scans(dia, tc)
                if not dia_scans:
                    continue  # continue if the diamond was not measured during this campaign
                h = HomePage()
                h.set_file_path(join(dirname(dia_scans[0].Path), 'index.html'))
                h.set_body(table.get_dia_body(dia_scans))
                h.create()
                self.create_runs(dia_scans)
                self.create_picture_pages(dia_scans)

    def create_dias(self):
        table = DiaTable()
        print_banner('CREATING SINGLE DIAMOND TABLES')
        diamonds = self.get_diamonds()
        table.start_pbar(len(diamonds))
        for i, dia in enumerate(diamonds, 1):
            dia_scans = table.DiaScans.get_diamond_scans(dia)
            h = HomePage()
            h.set_file_path(join('Diamonds', dia, 'index.html'))
            h.set_body(table.get_body(dia_scans))
            h.create()
            table.ProgressBar.update(i)
        table.ProgressBar.finish()

    @staticmethod
    def create_picture_pages(dia_scans):
        for dia_scan in dia_scans:
            page = PicturePage(dia_scan)
            page.make()

    @staticmethod
    def create_runs(dia_scans):
        table = RunTable()
        dia = dia_scans[0].Diamond
        dias = table.Diamonds
        print_banner('CREATING RUN TABLES FOR {} ({}/{}) in {}'.format(dia, dias.index(dia), len(dias), tc_to_str(dia_scans[0].TestCampaign, short=False)))
        for dia_scan in dia_scans:
            if dia_scan.TestCampaign < '201508':
                continue
            h = HomePage()
            h.set_file_path(join(dia_scan.Path, 'index.html'))
            h.set_body(table.get_body(dia_scan))
            h.create()

    def create_full_runs(self):
        table = RunTable()
        print_banner('CREATING FULL RUN TABLES')
        test_campaigns = [str_to_tc(tc) for tc in table.TestCampaigns if tc == self.TestCampaign or self.TestCampaign is None]
        for tc in test_campaigns:
            h = HomePage()
            h.set_file_path(join('BeamTests', tc_to_str(tc), 'index.html'))
            h.set_body(table.get_tc_body(tc))
            h.create()

    def create_full_runplans(self):
        table = RunPlanTable()
        print_banner('CREATING FULL RUNPLAN TABLES')
        test_campaigns = [str_to_tc(tc) for tc in table.TestCampaigns if tc == self.TestCampaign or self.TestCampaign is None]
        for tc in test_campaigns:
            h = HomePage()
            h.set_file_path(join('BeamTests', tc_to_str(tc), 'RunPlans.html'))
            h.set_body(table.get_tc_body(tc))
            h.create()

    def build(self):
        t = time()
        self.create_home()
        self.create_location()
        self.create_old()
        self.create_years()
        self.create_boards()
        self.create_dia_runplans()
        self.create_dias()
        self.create_full_runs()
        self.create_full_runplans()
        print 'This took {}'.format(time() - t)


if __name__ == '__main__':

    p = ArgumentParser()
    p.add_argument('-t', action='store_true')
    p.add_argument('-d', nargs='?', default=None)
    p.add_argument('-tc', nargs='?', default=None)
    args = p.parse_args()

    w = Website(args.d, args.tc)
    if not args.t:
        # w.update()
        w.build()
