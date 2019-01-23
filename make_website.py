#!/usr/bin/env python
# --------------------------------------------------------
#       script to create all the html files for the complete website
# created on December 20th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from sys import path
path.append('src')

from homepage import HomePage
from Utils import *
from ConfigParser import ConfigParser
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


class Website:

    def __init__(self):

        self.Dir = dirname(realpath(__file__))
        self.Config = self.load_config()
        self.HomePage = HomePage(self.Config, 'default')
        self.BkgCol = 'lightgrey'  # TODO FIX

        self.Diamond = None
        # in string format! Aug16
        self.TestCampaign = None

    def load_config(self):
        conf = ConfigParser()
        conf.read(join(self.Dir, 'conf.ini'))
        return conf

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
        for tc in self.HomePage.get_testcampaigns():
            if tc > '201505':
                self.update_run_log(tc)

    def update(self):
        self.update_run_plans()
        self.update_irradiation_file()
        self.update_diamond_aliases()
        self.update_masks()
        self.update_run_logs()

    def create_home(self):
        h = HomePage(self.Config, 'HomePage')
        body = '{}\n'.format(make_lines(3))
        body += '{}\n'.format(head(bold('Complete Set of Data Taken at Beam Tests at PSI ...')))
        body += '  <script type="text/javascript">\n'
        body += '    load_home();\n'
        body += '  </script>\n'
        h.set_body(indent(body, 2))
        h.create()

    def create_location(self):
        h = HomePage(self.Config, 'Location')
        body = '{}\n'.format(make_lines(3))
        body += '{}\n'.format(head(bold('Paul Scherrer Institut (PSI)')))
        body += make_figure(join('figures', 'PSIAir.jpg'), 'PSI-Air', width=1200)
        h.set_body(indent(body, 2))
        h.create()

    def create_boards(self):
        h = HomePage(self.Config, 'AmpBoards')
        body = '{}\n'.format(make_lines(3))
        body += '{}\n'.format(head(bold('Diamond Amplifier Boards')))
        rows = sorted([[center_txt(nr), option] for option in self.Config.options('Boards') for nr in loads(self.Config.get('Boards', option))])
        body += add_bkg(HTMLTable.table(rows, header_row=['Nr', 'Pulser Type'], ), self.BkgCol)
        h.set_body(body)
        h.create()

    def create_old(self):
        h = HomePage(self.Config, 'Old')
        table = OldTable()
        h.set_body(table.get_body())
        h.create()

    def create_years(self):
        for year in self.HomePage.get_years():
            if year.isdigit():
                h = HomePage(self.Config, year)
                table = YearTable(year)
                h.set_body(table.get_body())
                h.create()
                
    def create_dia_runplans(self):
        table = RunPlanTable()
        print_banner('CREATING DIAMOND RUNPLAN TABLES')
        diamonds = [dia for dia in table.Diamonds if dia == self.Diamond or self.Diamond is None]
        test_campaigns = [str_to_tc(tc) for tc in table.TestCampaigns if tc == self.TestCampaign or self.TestCampaign is None]
        table.start_pbar(len(diamonds))
        for i, dia in enumerate(diamonds, 1):
            for tc in test_campaigns:
                dia_scans = table.DiaScans.get_tc_diamond_scans(dia, tc)
                if not dia_scans:
                    continue  # continue if the diamond was not measured during this campaign
                h = HomePage(self.Config)
                h.set_file_path(join(dirname(dia_scans[0].Path), 'index.html'))
                h.set_body(table.get_dia_body(dia_scans))
                h.create()
                self.create_runs(dia_scans)
            table.ProgressBar.update(i)
        table.ProgressBar.finish()

    def create_dias(self):
        table = DiaTable()
        print_banner('CREATING SINGLE DIAMOND TABLES')
        diamonds = [dia for dia in table.Diamonds if dia == self.Diamond or self.Diamond is None]
        table.start_pbar(len(diamonds))
        for i, dia in enumerate(diamonds, 1):
            dia_scans = table.DiaScans.get_diamond_scans(dia)
            h = HomePage(self.Config)
            h.set_file_path(join('Diamonds', dia, 'index.html'))
            h.set_body(table.get_body(dia_scans))
            h.create()
            table.ProgressBar.update(i)
        table.ProgressBar.finish()

    def create_runs(self, dia_scans):
        table = RunTable()
        print_banner('CREATING RUN TABLES FOR {}'.format(dia_scans[0].TestCampaign))
        for dia_scan in dia_scans:
            if dia_scan.TestCampaign < '201508':
                continue
            h = HomePage(self.Config)
            h.set_file_path(join(dia_scan.Path, 'index.html'))
            h.set_body(table.get_body(dia_scan))
            h.create()

    def create_full_runs(self):
        table = RunTable()
        print_banner('CREATING FULL RUN TABLES')
        test_campaigns = [str_to_tc(tc) for tc in table.TestCampaigns if tc == self.TestCampaign or self.TestCampaign is None]
        for tc in test_campaigns:
            h = HomePage(self.Config)
            h.set_file_path(join('BeamTests', tc_to_str(tc), 'index.html'))
            h.set_body(table.get_tc_body(tc))
            h.create()

    def create_full_runplans(self):
        table = RunPlanTable()
        print_banner('CREATING FULL RUNPLAN TABLES')
        test_campaigns = [str_to_tc(tc) for tc in table.TestCampaigns if tc == self.TestCampaign or self.TestCampaign is None]
        for tc in test_campaigns:
            h = HomePage(self.Config)
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
    args = p.parse_args()

    w = Website()
    if not args.t:
        w.update()
        w.build()
