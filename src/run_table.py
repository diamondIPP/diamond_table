# --------------------------------------------------------
#       RUN-TABLE
# created on October 14th 2016 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from src.utils import *
import src.html as html
from src.info import DUTRunPlan
from src.info import Data, Run


class RunTable(html.File):

    def __init__(self, website):

        super().__init__()
        self.Website = website

    @staticmethod
    def header():
        main = [(n, *html.opts(rs=2)) for n in ['Run', f'HV {html.small("[V]")}', f'Flux {html.small(f"[kHz/cm{html.sup(2)}]", html.style(transform="none"))}',
                                                f'Current {html.small("[nA]", html.style(transform="none"))}', 'Hit Map']]
        main += [('Signal', *html.opts(cs=5)), ('Pulser', *html.opts(cs=4))]
        main += [(n, *html.opts(rs=2)) for n in ['Good Events', 'Start Time', 'Duration', 'Comment']]
        aux = ['Distr.', '2DMap', 'Pulse Height [au]', 'Pedestal [au]', 'Noise [1&sigma;]', 'Pulse Height [au]', 'Sigma', 'Pedestal [au]', 'Noise [1&sigma;]']
        return [main, aux]

    def title(self, rp: DUTRunPlan):
        return f'{rp.Name} ({self.link(dirname(rp.RelDir), rp.TCString)}): {rp.Type.title()} of {self.link(dirname(dirname(rp.RelDir)), rp.DUT.Name)}, ' \
               f'Irradiation: {html.irr2str(rp.Irradiation, unit=True)}, Position: {rp.Position.title()}'

    @staticmethod
    def prep_figures(run: Run, redo=False):
        html.prep_figures(run.RelDir, run.Number, redo)

    @update_pbar
    def build(self, rp: DUTRunPlan):
        self.set_filename(rp.Dir, 'index.html')
        self.set_header(self.Website.get_header(f'{rp.DUT.Name} {rp.ShortName}'))
        self.set_body('\n'.join([self.Website.NavBar.get(), html.table(self.title(rp), self.header(), self.body(rp))]))
        self.save()

    @quiet
    def build_all(self):
        info('creating run tables for runplans')
        self.PBar.start(sum(len(rps) for rps in Data.DUTRunPlans.values()), counter=True)
        [self.build(rp) for rps in Data.DUTRunPlans.values() for rp in rps]

    @quiet
    def build_tc(self, tc):
        [self.build(rp) for rp in Data.DUTRunPlans[tc]]

    def body(self, rp: DUTRunPlan):
        rows = []
        for run in rp.Runs:
            self.prep_figures(run)
            flux, cur, ph, ped, noise, pph, psig, pped, pnoise, ev = run.prep_data()
            s_ = [f'{i:{form}f}' if i else '-' for i, form in [(flux, .0), (cur, .1), (ph, .1), (ped, .1), (noise, .2), (pph, .1), (psig, .2), (pped, .2), (pnoise, .2)]]
            row = [run.Number, run.Bias]
            row += [self.rlink(run, name, s_[i]) for i, name in enumerate(['FluxProfile', 'Current'])]
            row += [self.rlink(run, n, html.fig_icon()) for n in ['HitMap', 'SignalDistribution', 'SignalMap2D']]
            row += [self.rlink(run, name, s_[i]) for i, name in enumerate(['PulseHeight5000', 'PedestalDistributionFitAllCuts'], 2)] + [s_[4]]
            row += [self.rlink(run, name, s_[i]) for i, name in enumerate(['PulserPulseHeight', 'PulserDistributionFit', 'PedestalDistributionFitPulserBeamOn'], 5)]
            rows.append(row + s_[8:] + [make_ev_str(ev), run.StartTime, run.Duration, (run.Comment[:10], html.style(left=True))])
        return rows

    def rlink(self, run, htmlname, target, **kwargs):
        return self.link(join(run.RelDir, f'{htmlname}.html'), target, **prep_kw(kwargs, new_tab=True, colour=None))


class FullRunTable(html.File):

    def __init__(self, website):

        super().__init__()
        self.Website = website
        self.Dir = join('content', 'beamtests')

    @update_pbar
    def build(self, tc):
        self.set_filename(join(self.Dir, tc, 'index.html'))
        self.set_header(self.Website.get_header(f'Runs {tc}'))
        self.set_body('\n'.join([self.Website.NavBar.get(), html.table(self.title(tc), self.header(tc), self.body(tc))]))
        self.save()

    @quiet
    def build_all(self):
        info('creating single run tables ...')
        self.PBar.start(len(Data.TestCampaigns), counter=True)
        for tc in Data.TestCampaigns:
            self.build(tc)

    @staticmethod
    def title(tc):
        return f'All Runs for {tc2str(tc, short=False)}'

    @staticmethod
    def header(tc):
        max_duts = Data.find_max_duts(tc)
        main = [(name, *html.opts(rs=2)) for name in ['Run', 'Type', f'Flux {html.small(f"[kHz/cm{html.sup(2)}]")}', 'FS11', 'FS13', 'Total Events', 'Start Time', 'Duration']]
        main += [(f'DUT{i}', *html.opts(cs=2)) for i in range(1, max_duts + 1)] + [('Comment', *html.opts(rs=2))]
        return [main, ['Name', 'Bias [V]'] * max_duts]

    @staticmethod
    def body(tc):
        rows = []
        for run_nr, dic in Data.RunInfos[tc].items():
            runs = [Run(tc, run_nr, dut_nr) for dut_nr in Run.get_dut_nrs(tc, run_nr)]
            row = [run_nr, runs[0].get_type(), runs[0].get_flux_str(), runs[0].get_fs11(), runs[0].get_fs13(), runs[0].get_ev_str(), runs[0].StartTime, runs[0].Duration]
            row += [word for run in runs for word in [run.DUTName, make_bias_str(run.Bias)]] + [''] * 2 * (3 - len(runs))
            rows.append(row + [(runs[0].Comment, html.style(left=True))])
        return rows
