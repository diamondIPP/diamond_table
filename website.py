#!/usr/bin/env python
# --------------------------------------------------------
#       script to create all the html files for the complete website
# created on December 20th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------


from src.utils import *
from src.nav_bar import NavBar
import src.html as html
from src.info import Data, DUTRunPlan
from src.structure import Structure
from src.run_table import RunTable, FullRunTable
from src.runplan_table import RunPlanTable, DiaRunPlanTable
from src.dut_table import DUTTable


class Website(html.File):

    def __init__(self, config='main.ini'):

        super().__init__()

        self.Title = 'PSI Diamonds'
        self.Config = Configuration(join(Dir, 'config', config))
        self.Icon = html.path('figures', self.Config.get('Home Page', 'icon'))
        self.TextSize = self.Config.get('Home Page', 'text size')
        self.Color = self.Config.get('Home Page', 'color')

        # MODULES
        self.Data = Data()
        self.Structure = Structure()
        self.NavBar = NavBar()
        self.RunTable = RunTable(self)
        self.DUTTable = DUTTable(self)
        self.FullRunTable = FullRunTable(self)
        self.RunPlanTable = RunPlanTable(self)
        self.DiaRunPlanTable = DiaRunPlanTable(self)

    def build(self):
        t = info('building website ...')
        self.Data.update()
        self.Structure.make_dirs()
        self.FullRunTable.build_all()
        self.RunTable.build_all()
        self.RunPlanTable.build_all()
        self.DiaRunPlanTable.build_all()
        self.DUTTable.build_all()
        self.NavBar.build()
        print(f'Done! ({get_elapsed_time(t)})')

    def get_header(self, title=None, icon=None):
        f = html.File()
        f.add_comment('Required meta tags')
        f.add_line('<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">')
        f.add_line('<link href="https://fonts.googleapis.com/css?family=Roboto:300,400&display=swap" rel="stylesheet">')
        f.add_line()
        f.add_line('<link rel="stylesheet" href="/css-t16/fonts/icomoon/style.css">')
        f.add_line('<link rel="stylesheet" href="/css-t16/css/owl.carousel.min.css">')
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
        f.add_line(f'<link rel="icon" href="{choose(icon, self.Icon)}">')
        f.add_line(f'<title> {choose(title, self.Title)} </title>')
        return f.get_text()

    def create_home(self):
        self.set_filename(Dir, 'content', 'index.html')
        self.set_header(self.get_header(f'Home'))
        self.set_body('\n'.join([self.NavBar.get(), html.lines(2), html.heading('Complete Set of Data Taken at Beam Tests at PSI ... <br> What should go here?')]))
        self.save()

    def create_location(self):
        self.set_filename(Dir, 'content', 'Location.html')
        self.set_header(self.get_header(f'Location'))
        self.set_body('\n'.join([self.NavBar.get(), html.lines(2), html.heading('Paul Scherrer Institut (PSI)'), html.image(join('figures', 'PSIAir.jpg'), w=1200)]))
        self.save()

    def create_boards(self):
        self.set_filename(Dir, 'content', 'AmpBoards.html')
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
    r = DUTRunPlan('08.2', '201510', '1')
    if not args.t:
        z.build()
