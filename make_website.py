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


class Website:

    def __init__(self):

        self.Dir = dirname(realpath(__file__))
        self.Config = self.load_config()
        self.HomePage = HomePage(self.Config, 'default')
        self.BkgCol = 'lightgrey'  # TODO FIX

    def load_config(self):
        conf = ConfigParser()
        conf.read(join(self.Dir, 'conf.ini'))
        return conf

    def create_home(self):
        h = HomePage(self.Config, 'HomePage')
        body = '{}\n'.format(make_lines(3))
        body += '{}\n'.format(head(bold('Here could be your text ...')))
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
        table.Diamond = 'S129'
        # table.TestCampaign = 'Aug16'
        print_banner('CREATING DIAMOND RUNPLAN TABLES')
        diamonds = [dia for dia in table.Diamonds if dia == table.Diamond or table.Diamond is None]
        test_campaigns = [str_to_tc(tc) for tc in table.TestCampaigns if tc == table.TestCampaign or table.TestCampaign is None]
        table.start_pbar(len(diamonds))
        for i, dia in enumerate(diamonds, 1):
            for tc in test_campaigns:
                dia_scans = table.DiaScans.get_diamond_scans(dia, tc)
                if not dia_scans:
                    continue  # continue if the diamond was not measured during this campaign
                h = HomePage(self.Config)
                h.set_file_path(join(dirname(dia_scans[0].Path), 'index.html'))
                h.set_body(table.get_dia_body(dia_scans))
                h.create()
            table.ProgressBar.update(i)
        table.ProgressBar.finish()

    def build(self):
        self.create_home()
        self.create_location()
        self.create_old()
        self.create_years()
        self.create_boards()


if __name__ == '__main__':

    w = Website()
    # w.build()
    w.create_dia_runplans()