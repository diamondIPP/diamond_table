#!/usr/bin/env python
# --------------------------------------------------------
#       module for RunPlan selection tables
# created on January 11th 2021 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from src.utils import join, load_json, BaseDir, make_list
import src.html as html
import src.info as data


class Selection(html.File):

    Dir = join('content', 'selections')
    Data = load_json(join(BaseDir, 'data', 'selection.json'))

    def __init__(self, website):
        super().__init__()
        self.Website = website

    @staticmethod
    def update():
        Selection.Data = load_json(join(BaseDir, 'data', 'selection.json'))

    @staticmethod
    def copy_data():
        return data.copy_from_server(join(data.ServerSoft, 'Runinfos', 'selection.json'))

    def build(self, redo=False):
        if Selection.copy_data() or redo:
            Selection.update()
            self.set_filename(join(Selection.Dir, 'index.html'))
            self.set_header(self.Website.get_header(f'Run Plan Selections'))
            self.set_body('\n'.join([self.Website.NavBar.get(), html.table('Run Plan Selections', self.header, self.body)]))
            self.save()

    @property
    def header(self):
        return ['Name', 'Data', ('DUT', html.style(left=True)), ('Beam Tests', html.style(left=True))]

    @property
    def body(self):
        rs = []
        for key, d1 in self.Data.items():
            duts = set([data.TestCampaigns[tc].get_runplan(rp).DUTs[i - 1] for tc, d0 in d1.items() for rp, l0 in d0.items() for i in make_list(l0) if tc in data.TestCampaigns])
            r = [key, self.link(join(self.Dir, key, 'plots.html'), html.LinkIcon, use_name=False, warn=False)]
            rs.append(r + [(', '.join(self.link(dut.RelDir, dut.Name, new_tab=True) for dut in duts), html.style(left=True)), (', '.join(d1.keys()), html.style(left=True))])
        return rs
