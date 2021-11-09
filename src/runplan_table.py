# --------------------------------------------------------
#       RUN-TABLE FUNCTIONS
# created on December 8th 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from src.utils import *
import src.html as html
import src.info as data


class RunPlanTable(html.File):

    def __init__(self, website):
        super().__init__()
        self.Website = website

    def build(self, tc):
        tc = data.TestCampaigns[tc]
        if tc.RunPlans:
            self.set_filename(BaseDir, 'content', 'beamtests', tc.ID, 'RunPlans.html')
            self.set_header(self.Website.get_header(f'Run Plans {tc}'))
            self.set_body('\n'.join([self.Website.NavBar.get(), html.table(self.title(tc), self.header(tc), self.body(tc), html.style(nowrap=True))]))
            self.save()

    @quiet
    def build_all(self):
        info('creating runplan tables for beam tests ...')
        for tc in data.TestCampaigns:
            self.build(tc)

    @staticmethod
    def title(tc: data.TestCampaign):
        return f'Run Plans for the Beamtest in {tc})'

    @staticmethod
    def header(tc: data.TestCampaign):
        main = [(n, *html.opts(rs=2)) for n in ['Nr.', 'Digitiser', 'Amplifier', 'DUT Type', 'Sub Plan', 'Type', 'Runs', 'Total Events']]
        main += [(f'DUT {i}', *html.opts(cs=3)) for i in range(1, tc.NMaxDUTs + 1)]
        return [main, ['Data', 'Name', 'Bias [V]'] * tc.NMaxDUTs]

    def body(self, tc: data.TestCampaign):
        rows = []
        for rp in tc.RunPlans:
            row = [(v, *html.opts(rs=rp.NSub)) for v in [rp.Tag, rp.Digitiser, rp.Amplifier, rp.DUTType]] if rp.IsMain else []
            row += [(rp.Tag.lstrip('0'), html.style(colour=html.Good if rp.is_complete else None)), rp.Type, rp.RunStr, rp.EventStr]
            row += [w for i, dut in enumerate(rp.DUTs) for w in [self.link(rp.RelDirs[i], html.LinkIcon), self.link(join(dut.RelDir, tc.ID), dut.Name), rp.BiasStr[i]]]
            rows.append(row)
        return rows


class DiaRunPlanTable(html.File):

    def __init__(self, website):
        super().__init__()
        self.Website = website
        self.TCHeader = self.get_tc_header()
        self.MainHeader = self.get_header()

    # ----------------------------------------
    # region HEADER
    def get_header(self):
        main, aux = self.TCHeader
        return [[(n, *html.opts(rs=2)) for n in ['Beam Test', 'Irrad.']] + main, aux]

    @staticmethod
    def get_tc_header():
        main = [(n, *html.opts(rs=2)) for n in ['Nr.', 'Pos.', 'Digi-tiser', 'Amp']] + [('Atte-nuators', *html.opts(cs=2))] + [('HV [V]', *html.opts(rs=2))]
        main += [(n, *html.opts(rs=2)) for n in ['Sub Plan', 'Runs', f'Flux {html.small(f"[kHz/cm{html.sup(2)}]", html.style(transform="none"))}',
                                                 f'Cur. {html.small("[nA]", html.style(transform="none"))}']]
        main += [('Signal', *html.opts(cs=3)), ('Pulser', *html.opts(cs=2))] + [(n, *html.opts(rs=2)) for n in ['Good Events', 'Start Time', 'Duration']]
        return [main, ['DUT', 'Pulser', 'PH', 'Ped', '&sigma;', 'PH', '&sigma;']]
    # endregion HEADER
    # ----------------------------------------

    @quiet
    def build_all(self):
        info('creating runplan tables for DUTs ...')
        duts = [dut for dut in data.DUTs.values() if dut.rp_tcs]
        self.PBar.start(len(duts), counter=True)
        for dut in duts:
            self.build(dut)

    @update_pbar
    def build(self, dut: data.DUT):
        tc_bodies = {tc: self.build_dut_tc(data.TestCampaigns[tc], dut) for tc in dut.tcs}
        if tc_bodies and sum(len(r) for r in tc_bodies.values()):
            self.set_filename(dut.Dir, 'index.html')
            self.set_header(self.Website.get_header(f'Run Plans - {dut.Name}'))
            self.set_body('\n'.join([self.Website.NavBar.get(), html.table(self.title(dut), self.MainHeader, self.body(dut, tc_bodies))]))
            self.save()

    def build_dut_tc(self, tc: data.TestCampaign, dut: data.DUT):
        self.set_filename(dut.Dir, tc.ID, 'index.html')
        self.set_header(self.Website.get_header(f'Run Plans - {dut} ({tc})'))
        rows = [self.row(rp, rp.get_dut_nr(dut)) for rp in tc.get_dut_runplans(dut)]
        if not rows:
            return []
        self.set_body('\n'.join([self.Website.NavBar.get(), html.table(self.tc_title(tc, dut), self.TCHeader, rows, html.style(nowrap=True))]))
        self.save()
        return rows

    @quiet
    def build_tc(self, tc):
        """ only builds the runplan tables for a single beam test. """
        tc = data.TestCampaigns[tc]
        [self.build_dut_tc(tc, data.DUTs[name]) for name in tc.DUTs]

    def tc_title(self, tc: data.TestCampaign, dut: data.DUT):
        return f'Run Plans for {self.link(dut.RelDir, str(dut))} in {tc}'

    @staticmethod
    def title(dut: data.DUT):
        return f'Run Plans for {dut}'

    def row(self, rp: data.RunPlan, i):
        figs = ['FluxProfile', 'Currents', 'PulseHeightFlux', 'PedestalFlux', 'NoiseFlux', 'PulserPH', 'PulserSigma']
        row = [(v, *html.opts(rs=rp.NSub)) for v in [rp.Tag, rp.Positions[i], rp.Digitiser, rp.Amplifier, *rp.get_attenuators(i), rp.BiasStr[i]]] if rp.IsMain else []
        row += [self.link(rp.RelDirs[i], rp.Tag.lstrip('0')), rp.RunStr] + [self.rplink_(rp.RelDirs[i], fig, rp.DataStr[i][j]) for j, fig in enumerate(figs)]
        return row + [rp.DataStr[i][-1], rp.StartTime, rp.Duration]

    @staticmethod
    def body(dut: data.DUT, tc_rows):
        """ Add tc info and irrad to the first row"""
        all_rows = []
        for tc, rows in tc_rows.items():
            if rows:
                tc_info = f'{html.link(join(dut.RelDir, tc), data.TestCampaign.to_str(tc, short=False))}<br><br>({dut.get_type(tc)}{f",<br>pulser: {dut.get_pulser(tc)})" if dut.get_pulser(tc) else ")"}'
                rows[0] = [(n, *html.opts(rs=len(rows))) for n in [tc_info, html.irr2str(dut.get_irradiation(tc))]] + rows[0]
                all_rows += rows
        return all_rows

    def rplink_(self, d, htmlname, target, **kwargs):
        return self.link(join(d, f'{htmlname}.html'), target, **prep_kw(kwargs, new_tab=True, colour=None))


if __name__ == '__main__':
    pass
