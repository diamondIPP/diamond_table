# --------------------------------------------------------
#       DUT-TABLE
# created on July 3rd 2021 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

import src.html as html
from src.utils import BaseDir, join
import src.info as data
from typing import List


class DUTTable(html.File):

    def __init__(self, website):

        super().__init__()
        self.Website = website
        self.NavBar = self.Website.NavBar

    def build(self, duts: List[data.DUT], filename, type_=''):
        self.set_filename(BaseDir, 'content', 'duts', f'{filename}.html')
        self.set_header(self.Website.get_header(f'{filename} Detectors'))
        self.set_body('\n'.join([self.Website.NavBar.get(), html.table(self.title(f'{filename} {type_}s'), self.header(), self.body(duts))]))
        self.save()

    def build_all(self):
        self.build([data.DUTs[n] for n in self.NavBar.get_sccvd_dias()], 'scCVD', 'Diamond')
        self.build([data.DUTs[n] for n in self.NavBar.get_pcvd_dias()], 'pCVD', 'Diamond')
        self.build([data.DUTs[n] for n in self.NavBar.get_si_detectors()], 'Si', 'Diode')

    @staticmethod
    def header():
        return ['Name', 'Manufacturer', f'Thickness {html.div("[&micro;m]", html.style(transform="none"))}', 'DUT Types', 'Irradiations', 'Beam Tests', 'Comment']

    @staticmethod
    def title(sensor_type):
        return f'All measured {sensor_type}'

    def body(self, duts: List[data.DUT]):
        rows = []
        for dut in duts:
            row = [self.link(dut.RelDir, dut.Name), self.link_manufacturer(dut), dut.Thickness, dut.get_types(), dut.get_irradiations(), self.link_tcs(dut),
                   (dut.Comment, html.style(left=True))]
            rows.append(row)
        return rows

    def link_manufacturer(self, dut: data.DUT):
        man = dut.Manufacturer
        return self.link(self.Website.Config.get_value('Manufacturers', man, default=man), man, new_tab=True)

    def link_tcs(self, dut: data.DUT):
        return ', '.join(self.link(join(dut.RelDir, tc), tc) for tc in dut.rp_tcs)
