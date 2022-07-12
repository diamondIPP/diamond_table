#!/usr/bin/env python
# --------------------------------------------------------
#       module for RunPlan selection tables
# created on January 11th 2021 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from src.utils import join, load_json, BaseDir, make_list, Path, create_dir
import src.html as html
import src.info as data


class Selections(html.File):

    Dir = Path('content', 'selections')
    Data = load_json(BaseDir.joinpath('data', 'selection.json'))

    def __init__(self, website):
        super().__init__()
        self.Website = website

    @staticmethod
    def update():
        Selections.Data = load_json(join(BaseDir, 'data', 'selection.json'))

    @staticmethod
    def copy_data():
        return data.copy_from_server(join(data.ServerSoft, 'Runinfos', 'selection.json'))

    def build(self, redo=False):
        if Selections.copy_data() or redo:
            Selections.update()
            self.build_selections()
            self.set_filename(join(Selections.Dir, 'index.html'))
            self.set_header(self.Website.get_header(f'Run Plan Selections'))
            self.set_body('\n'.join([self.Website.NavBar.get(), html.table('Run Plan Selections', self.header, self.body, w='600px')]))
            self.save()

    def build_selections(self):
        for sel, d in self.Data.items():
            Selection(self.Website, verbose=False).build(sel, d)

    @property
    def header(self):
        return ['Name', 'Data', ('DUT', html.style(left=True)), ('Beam Tests', html.style(left=True))]

    @property
    def body(self):
        rs = []
        for key, d1 in self.Data.items():
            duts = set([data.TestCampaigns[tc].get_runplan(rp).DUTs[i - 1] for tc, d0 in d1.items() for rp, l0 in d0.items() for i in make_list(l0) if tc in data.TestCampaigns])
            p = self.Dir.joinpath(key)
            r = [self.link(p.joinpath('sel.html'), key), self.link(p.joinpath('plots.html'), html.LinkIcon, use_name=False, warn=False)]
            rs.append(r + [(', '.join(self.link(dut.RelDir, dut.Name, new_tab=True) for dut in duts), html.style(left=True)), (', '.join(d1.keys()), html.style(left=True))])
        return rs


class Selection(html.File):

    def __init__(self, website, verbose=True):
        super().__init__(verbose=verbose)
        self.Website = website
        self.TabHead = ['Beamtest', 'Runplan', 'Runs', 'DUT Nr.']

    def build(self, name, d):
        self.set_filename(Selections.Dir.joinpath(name, 'sel.html'))
        create_dir(BaseDir.joinpath(self.FileName.parent))
        title = f'Runplan selection {name}'
        self.set_header(self.Website.get_header(title))
        rows = sum([self.tc_rows(tc, d1) for tc, d1 in d.items()], start=[])
        self.set_body('\n'.join([self.Website.NavBar.get(), html.table(title, self.TabHead, rows, w='350px')]))
        self.save()

    def tc_rows(self, tc, d):
        d = list(d.items())
        rows = [[(tc, *html.opts(rs=len(d))), *self.rp_data(tc, *d[0])], *[self.rp_data(tc, *i) for i in d[1:]]]
        rows[-1] = (rows[-1], html.style(hline='1px solid'))
        return rows

    def rp_data(self, tc, rp, dut):
        rp = data.TestCampaigns[tc].get_runplan(rp)
        return [rp.Tag if type(dut) is list else self.link(rp.RelDirs[dut - 1], rp.Tag), rp.RunStr, dut]
