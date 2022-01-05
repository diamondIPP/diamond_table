#!/usr/bin/env python
# --------------------------------------------------------
#       script to create all the html files for the complete website
# created on December 20th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------


import src.html as html
import src.info as data
import src.structure as structure
from src.dut_table import DUTTable
from src.home import Home
from src.nav_bar import NavBar
from src.run_table import RunTables, FullRunTable
from src.runplan_table import RunPlanTable, DiaRunPlanTable
from src.utils import *


class Website(html.File):

    def __init__(self, config='main.ini'):

        super().__init__()

        self.Title = 'PSI Diamonds'
        self.Header = self.make_header()
        self.Config = Configuration(join(BaseDir, 'config', config))
        self.Icon = self.Config.get('Home Page', 'icon')
        self.TextSize = self.Config.get('Home Page', 'text size')
        self.Color = self.Config.get('Home Page', 'color')
        self.Count = 0
        self.StartTime = time()

        # MODULES
        self.NavBar = NavBar()
        self.Home = Home(self)
        self.RunTables = RunTables(self)
        self.DUTTable = DUTTable(self)
        self.FullRunTable = FullRunTable(self)
        self.RunPlanTable = RunPlanTable(self)
        self.DiaRunPlanTable = DiaRunPlanTable(self)

    def run(self, tc=None):
        while True:
            print_banner(f'starting iteration ({self.Count:04d}), running for {get_elapsed_time(self.StartTime, hrs=True)}', color='red')
            self.build() if tc is None else self.build_tc(tc)
            self.Count += 1

    def build(self, redo=False):
        t = info('building website ...')
        if data.update() or redo:
            structure.make_dirs()
            self.FullRunTable.build_all()
            self.RunTables.build_all()
            self.RunPlanTable.build_all()
            self.DiaRunPlanTable.build_all()
            self.DUTTable.build_all()
            self.Home.build()
            self.NavBar.build()
        print(f'Done! ({get_elapsed_time(t)})')

    def build_tc(self, tc):
        self.RunTables.build_tc(tc)
        self.FullRunTable.build(tc)
        self.RunPlanTable.build(tc)
        self.DiaRunPlanTable.build_tc(tc)
        self.NavBar.build()

    @staticmethod
    def make_header():
        f = html.File()
        f.add_comment('Required meta tags')
        f.add_line('<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">')
        f.add_line('<link href="https://fonts.googleapis.com/css?family=Roboto:300,400&display=swap" rel="stylesheet">')
        f.add_line()
        f.add_lines([f'<link rel="stylesheet" href="{join("/css-t16", n)}">' for n in [join('fonts', 'icomoon', 'style.css'), join('css', 'owl.carousel.min.css')]])
        f.add_line()
        f.add_comment('Bootstrap CSS')
        f.add_line('<link rel="stylesheet" href="/psi2/config/bootstrap.min.css">')
        f.add_line()
        f.add_comment('Style')
        f.add_line('<link rel="stylesheet" href="/psi2/config/style.css">')
        f.add_line('<link rel="stylesheet" href="/psi2/config/nav.css">')
        f.add_line()
        f.add_comment('Java Scripts')
        f.add_lines([html.script(f'/css-t16/js/{s}') for s in ['jquery-3.3.1.min.js', 'popper.min.js', 'bootstrap.min.js', 'main.js']])
        f.add_line(html.script('/psi2/config/nav.js'))
        f.add_line()
        f.add_line('<link rel="icon" href="{icon}">')
        f.add_line('<title> {title} </title>')
        return f.get_text()

    def get_header(self, title=None, icon=None):
        return self.Header.format(icon=html.path('figures', choose(icon, self.Icon)), title=choose(title, self.Title))

    def create_location(self):
        self.set_filename(BaseDir, 'content', 'Location.html')
        self.set_header(self.get_header(f'Location'))
        self.set_body('\n'.join([self.NavBar.get(), html.empty_line(3), html.heading('Paul Scherrer Institut (PSI)', 2), html.image(join('figures', 'PSIAir.jpg'), w=1200)]))
        self.save()

    def create_boards(self):
        self.set_filename(BaseDir, 'content', 'AmpBoards.html')
        self.set_header(self.get_header(f'Amplifier Boards'))
        rows = sorted([[str(nr), option] for option in self.Config.options('Boards') for nr in self.Config.get_list('Boards', option)])
        self.set_body('\n'.join([self.NavBar.get(), html.table('Pad Amplifier Boards', ['Nr.', 'Pulser Type'], rows, html.style(left=True))]))
        self.save()


if __name__ == '__main__':

    from argparse import ArgumentParser

    p = ArgumentParser()
    p.add_argument('-t', action='store_true')
    p.add_argument('-d', nargs='?', default=None)
    p.add_argument('-tc', nargs='?', default=None)
    args = p.parse_args()

    z = Website()
    r = data.RunPlan('08', '201708')
    c = data.TestCampaigns['201708']
    run = c.runplan_runs[-18]
    if not args.t:
        z.run(args.tc)
