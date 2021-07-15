#!/usr/bin/env python
# --------------------------------------------------------
#       module to build the homepage of the website
# created on December 20th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

import src.html as html
from src.info import Data, join, tc2str


class Home(html.File):

    def __init__(self, website):

        super().__init__(join('content', 'index.html'))
        self.Website = website
        self.Title = 'Beam Test taken at PSI using the digital ETH telescope'

    def build(self):
        self.set_header(self.Website.get_header('Home', 'dia_home.png'))
        self.set_body('\n'.join([self.Website.NavBar.get(), html.table(self.Title, self.header(), self.body())]))
        self.save()

    @staticmethod
    def header():
        return ['Beam Test', 'DUT Types', 'DUTs', 'Important Results']

    def body(self):
        rows = []
        for tc in Data.TestCampaigns:
            row = [self.link(join('content', 'beamtests', tc, 'RunPlans.html'), tc2str(tc, short=False))]
            row += [(', '.join(Data.find_dut_types(tc)), html.style(left=True))]
            row += [(', '.join(self.link(join(Data.DUTs[dut].RelDir, tc), dut) for dut in Data.TCDUTs[tc]), html.style(left=True)), html.NoIcon]
            rows.append(row)
        return rows


if __name__ == '__main__':
    pass
