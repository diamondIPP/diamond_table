# --------------------------------------------------------
#       RUN-TABLE
# created on October 14th 2016 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from src.utils import *
import src.html as html
from src.info import TestCampaigns, TestCampaign, RunPlan, Run, make_bias_str
from operator import itemgetter


class RunTable(html.File):

    def __init__(self, website):

        super().__init__()
        self.Website = website

    @quiet
    def build_all(self):
        info('creating run tables for runplans')
        PBAR.start(len(TestCampaigns), counter=True)
        [self.build_tc(tc) for tc in TestCampaigns]

    def build(self, rp: RunPlan, dut_nr, rows):
        self.set_filename(rp.RelDirs[dut_nr], 'index.html')
        self.set_header(self.Website.get_header(f'{rp.DUTs[dut_nr].Name} {rp.ShortName}'))
        self.set_body('\n'.join([self.Website.NavBar.get(), html.table(self.title(rp, dut_nr), self.header, rows)]))
        self.save()

    @update_pbar
    @quiet
    def build_tc(self, tc):
        tc = TestCampaigns[tc]
        rows = {run.Number: [self.row(run, i) for i in range(run.NDUTs)] for run in tc.runplan_runs}
        for rp in tc.RunPlans:
            for i in range(rp.NDUTs):
                self.build(rp, i, RunTable.rowgetter(rp, i)(rows))

    @property
    def header(self):
        main = [(n, *html.opts(rs=2)) for n in ['Run', f'HV {html.small("[V]")}', f'Flux {html.small(f"[kHz/cm{html.sup(2)}]", html.style(transform="none"))}',
                                                f'Current {html.small("[nA]", html.style(transform="none"))}', 'Hit Map']]
        main += [('Signal', *html.opts(cs=5)), ('Pulser', *html.opts(cs=4))]
        main += [(n, *html.opts(rs=2)) for n in ['Good Events', 'Start Time', 'Duration', 'Comment']]
        aux = ['Distr.', '2DMap', 'Pulse Height [au]', 'Pedestal [au]', 'Noise [1&sigma;]', 'Pulse Height [au]', 'Sigma', 'Pedestal [au]', 'Noise [1&sigma;]']
        return [main, aux]

    def title(self, rp: RunPlan, dut_nr):
        d = dirname(rp.RelDirs[dut_nr])
        return f'{rp.Name} ({self.link(d, rp.TCString)}): {rp.Type.title()} of {self.link(dirname(d), rp.DUTs[dut_nr].Name)}, ' \
               f'Irradiation: {html.irr2str(rp.get_irradiation(dut_nr), unit=True)}, Position: {rp.Positions[dut_nr].title()}'

    def row(self, run: Run, dut_nr):
        d = run.RelDirs[dut_nr]
        data = run.FullData[dut_nr]
        row = [run.Number, run.Biases[dut_nr]]
        row += [self.rlink(d, name, data[i]) for i, name in enumerate(['FluxProfile', 'Current'])]
        row += [self.rlink(d, n, html.fig_icon()) for n in ['HitMap', 'SignalDistribution', 'SignalMap2D']]
        row += [self.rlink(d, name, data[i]) for i, name in enumerate(['PulseHeight5000', 'PedestalDistributionFitAllCuts'], 2)] + [data[4]]
        row += [self.rlink(d, name, data[i]) for i, name in enumerate(['PulserPulseHeight', 'PulserDistributionFit', 'PedestalDistributionFitPulserBeamOn'], 5)]
        return row + [*data[8:], run.StartTime, run.Duration, (run.Comment[:10], html.style(left=True))]

    @staticmethod
    def rowgetter(rp: RunPlan, dut_nr):
        return (lambda x: [x[rp.RunNumbers[0]][dut_nr]]) if rp.Size == 1 else lambda x: [r[dut_nr] for r in itemgetter(*rp.RunNumbers)(x)]

    def rlink(self, d, htmlname, target, **kwargs):
        return self.link(join(d, f'{htmlname}.html'), target, **prep_kw(kwargs, new_tab=True, colour=None))


class FullRunTable(html.File):

    def __init__(self, website):

        super().__init__()
        self.Website = website
        self.Dir = join('content', 'beamtests')

    @update_pbar
    def build(self, tc):
        tc = TestCampaigns[tc]
        self.set_filename(join(self.Dir, tc.ID, 'index.html'))
        self.set_header(self.Website.get_header(f'Runs {tc}'))
        self.set_body('\n'.join([self.Website.NavBar.get(), html.table(self.title(tc), self.header, self.body(tc))]))
        self.save()

    @quiet
    def build_all(self):
        info('creating single run tables ...')
        PBAR.start(len(TestCampaigns), counter=True)
        for tc in TestCampaigns:
            self.build(tc)

    @staticmethod
    def title(tc: TestCampaign):
        return f'All Runs for {tc}'

    @property
    def header(self):
        return ['Runs', 'Type', 'FS11', 'FS13', 'Total Events', 'Start Time', 'Duration', 'DUT', f'HV {html.small("[V]")}', f'I {html.small("[nA]", html.style(transform="none"))}',
                f'Flux {html.small(f"[kHz/cm{html.sup(2)}]", html.style(transform="none"))}', f'Pulse Height {html.small("[mV]", html.style(transform="none"))}', 'Ped', 'Good Events', 'Comments']

    @staticmethod
    def body(tc: TestCampaign):
        rows = []
        for run in tc.Runs.values():
            for i in range(run.NDUTs):
                # html.prep_figures(run.RelDirs[i], run.Number)
                row = [] if i else [(v, *html.opts(rs=run.NDUTs)) for v in [run.Number, run.Type, run.FS11, run.FS13, run.EventStr[i], run.StartTime, run.Duration]]
                row += [(run.DUTs[i], html.style(nowrap=True)), make_bias_str(run.Biases[i])] + run.get_short_data(i)
                rows.append(row + ([] if i else [(run.Comment, html.style(left=True), *html.opts(rs=run.NDUTs))]))
        return rows
