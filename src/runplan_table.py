# --------------------------------------------------------
#       RUN-TABLE FUNCTIONS
# created on December 8th 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from src.utils import *
import src.html as html
from src.info import Data, DUT, DUTRunPlan


class RunPlanTable(html.File):

    def __init__(self, website):
        super().__init__()
        self.Website = website

    def build(self, tc):
        self.set_filename(Dir, 'content', 'beamtests', tc, 'RunPlans.html')
        self.set_header(self.Website.get_header(f'Run Plans {tc2str(tc)}'))
        self.set_body('\n'.join([self.Website.NavBar.get(), html.table(self.title(tc), self.header(tc), self.body(tc), html.style(nowrap=True))]))
        self.save()

    @quiet
    def build_all(self):
        info('creating runplan tables for beam tests ...')
        for tc in Data.TestCampaigns:
            self.build(tc)

    @staticmethod
    def title(tc):
        return f'Run Plans for the Beamtest in {tc2str(tc, short=False)}'

    @staticmethod
    def header(tc):
        max_duts = Data.find_max_duts(tc)
        main = [(n, *html.opts(rs=2)) for n in ['Nr.', 'Digitiser', 'Amplifier', 'DUT Type', 'Sub Plan', 'Type', 'Runs', 'Total Events']]
        main += [(f'DUT {i}', *html.opts(cs=3)) for i in range(1, max_duts + 1)]
        return [main, ['Data', 'Name', 'Bias [V]'] * max_duts]

    def body(self, tc):
        rows = []
        for rp in Data.RunPlans[tc]:
            row = [(v, *html.opts(rs=rp.get_n_sub())) for v in [rp.Tag, rp.Digitiser, rp.Amplifier, rp.DUTs[0].get_type(tc)]] if rp.is_main() else []
            row += [(rp.Tag.lstrip('0'), html.style(colour=html.Good if rp.is_complete() else None)), rp.Type, rp.get_runs_str(), rp.get_ev_str()]
            row += [w for i, dut in enumerate(rp.DUTs, 1) for w in [self.link(rp.get_dir(dut), html.LinkIcon), self.link(join(dut.RelDir, tc), dut.Name), rp.get_bias_str(i)]]
            rows.append(row)
        return rows


class DiaRunPlanTable(html.File):

    def __init__(self, website):
        super().__init__()
        self.Website = website

    @update_pbar
    def build(self, dut: DUT):
        tc_bodies = {tc: self.build_tc(tc, dut) for tc in Data.find_tcs(dut.Name)}
        self.set_filename(dut.Dir, 'index.html')
        self.set_header(self.Website.get_header(f'Run Plans - {dut.Name}'))
        self.set_body('\n'.join([self.Website.NavBar.get(), html.table(self.title(dut), self.header(), self.body(dut, tc_bodies))])) if len(tc_bodies) else do_nothing()
        self.save()

    def build_tc(self, tc, dut: DUT):
        self.set_filename(dut.Dir, tc, 'index.html')
        self.set_header(self.Website.get_header(f'Run Plans - {dut.Name} ({tc})'))
        body = self.tc_body(tc, dut)
        self.set_body('\n'.join([self.Website.NavBar.get(), html.table(self.tc_title(tc, dut), self.tc_header(), body, html.style(nowrap=True))]))
        self.save()
        return body

    @quiet
    def build_all_tc(self, tc):
        [self.build_tc(tc, Data.DUTs[name]) for name in Data.TCDUTs[tc]]

    @quiet
    def build_all(self):
        info('creating runplan tables for DUTs ...')
        duts = [Data.DUTs[dut] for dut in self.Website.NavBar.used(Data.DUTs)]
        self.PBar.start(len(duts), counter=True)
        for dut in duts:
            self.build(dut)

    @staticmethod
    def prep_figures(rp: DUTRunPlan, redo=False):
        html.prep_figures(rp.RelDir, rp.ShortName, redo)

    def tc_title(self, tc, dut: DUT):
        return f'Run Plans for {self.link(dut.RelDir, dut.Name)} in {tc2str(tc, short=False)}'

    @staticmethod
    def title(dut: DUT):
        return f'Run Plans for {dut.Name}'

    @staticmethod
    def header():
        main, aux = DiaRunPlanTable.tc_header()
        return [[(n, *html.opts(rs=2)) for n in ['Beam Test', 'Irrad.']] + main, aux]

    @staticmethod
    def tc_header():
        main = [(n, *html.opts(rs=2)) for n in ['Nr.', 'Pos.', 'Digi-tiser', 'Amp']] + [('Atte-nuators', *html.opts(cs=2))] + [('HV [V]', *html.opts(rs=2))]
        main += [(n, *html.opts(rs=2)) for n in ['Sub Plan', 'Runs', f'Flux {html.small(f"[kHz/cm{html.sup(2)}]", html.style(transform="none"))}',
                                                 f'Cur. {html.small("[nA]", html.style(transform="none"))}']]
        main += [('Signal', *html.opts(cs=3)), ('Pulser', *html.opts(cs=2))] + [(n, *html.opts(rs=2)) for n in ['Good Events', 'Start Time', 'Duration']]
        return [main, ['DUT', 'Pulser', 'PH', 'Ped', '&sigma;', 'PH', '&sigma;']]

    def tc_body(self, tc, dut: DUT):
        rows = []
        for rp in [r for r in Data.DUTRunPlans[tc] if r.DUT.Name == dut.Name]:
            self.prep_figures(rp)
            row = [(v, *html.opts(rs=rp.get_n_sub())) for v in [rp.Tag, rp.Position, rp.Digitiser, rp.Amplifier] + rp.get_attenuators() + [rp.get_bias_str()]] if rp.is_main() else []
            row += [self.link(rp.RelDir, rp.Tag.lstrip('0')), rp.get_runs_str(), self.rplink(rp, 'FluxProfile', rp.get_flux_str())]
            row += [self.rplink(rp, n, rp.get_mean(i)) for i, n in enumerate(['Currents', 'PulseHeightFlux', 'PedestalFlux', 'NoiseFlux', 'PulserPH', 'PulserSigma'], 1)]
            row += [rp.get_ev_str(), rp.StartTime, rp.Duration]
            rows.append(row)
        return rows

    def body(self, dut: DUT, tc_bodies):
        rows = []
        for tc, body in tc_bodies.items():
            a = self.tc_body(tc, dut)
            tc_info = f'{html.link(join(dut.RelDir, tc), tc2str(tc, short=False))}<br><br>({dut.get_type(tc)}{f",<br>pulser: {dut.get_pulser(tc)})" if dut.get_pulser(tc) else ")"}'
            a[0] = [(n, *html.opts(rs=len(a))) for n in [tc_info, irr2str(dut.get_irradiation(tc))]] + a[0]
            rows += a
        return rows

    def rplink(self, rp: DUTRunPlan, htmlname, target, **kwargs):
        return self.link(join(rp.RelDir, f'{htmlname}.html'), target, **prep_kw(kwargs, new_tab=True, colour=None))


if __name__ == '__main__':
    pass
