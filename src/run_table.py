# --------------------------------------------------------
#       RUN-TABLE
# created on October 14th 2016 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from src.utils import *
import src.html as html
import src.info as data
from operator import itemgetter
from typing import Any


class RunTables(html.File):

    def __init__(self, website):
        super().__init__()
        self.Website = website
        self.PixRT = PixRunTable(self.Website)
        self.PadRT = PadRunTable(self.Website)

    def set_verbose(self, status):
        super().set_verbose(status)
        self.PixRT.set_verbose(status)
        self.PadRT.set_verbose(status)

    def get_run_table(self, rp: data.RunPlan):
        return self.PixRT if rp.is_pixel else self.PadRT

    @quiet
    def build_all(self):
        info('creating run tables for runplans')
        PBAR.start(len(data.TestCampaigns), counter=True)
        [self.build_tc(tc) for tc in data.TestCampaigns]

    @update_pbar
    @quiet
    def build_tc(self, tc):
        tc = data.TestCampaigns[tc]
        run_table = lambda run, i: PixRunTable if 'pixel' in tc.DUTTypes[run.DUTs[i]] else PadRunTable
        rows = {run.Number: [run_table(run, i).row(self.rlink, run, i) for i in range(run.NDUTs)] for run in tc.runplan_runs}  # only create rows once ...
        for rp in tc.RunPlans:
            for i in range(rp.NDUTs):
                self.get_run_table(rp).build(rp, i, rows=RunTable.rowgetter(rp, i)(rows))

    def rlink(self, d, htmlname, target, **kwargs):
        return self.link(join(d, f'{htmlname}.html'), target, **prep_kw(kwargs, new_tab=True, colour=None))


class RunTable(html.File):

    Add2Header = []
    Add2SubHeader = []

    def __init__(self, website):
        super().__init__()
        self.Website = website

    def build(self, rp: data.RunPlan, dut_nr, rows: Any = None):
        self.set_filename(rp.RelDirs[dut_nr], 'index.html')
        self.set_header(self.Website.get_header(f'{rp.DUTs[dut_nr].Name} {rp.ShortName}'))
        rows = self.rows(self.rlink, rp, dut_nr) if rows is None else rows
        self.set_body('\n'.join([self.Website.NavBar.get(), html.table(self.title(rp, dut_nr), self.header, rows)]))
        self.save()

    @property
    def header(self):
        main = [(n, *html.opts(rs=2)) for n in ['Run', f'HV {html.small("[V]")}', f'Flux {html.small(f"[kHz/cm{html.sup(2)}]", html.style(transform="none"))}',
                                                f'Current {html.small("[nA]", html.style(transform="none"))}', 'Hit Map']]
        main += self.Add2Header + [(n, *html.opts(rs=2)) for n in ['Good Events', 'Start Time', 'Duration', 'Comment']]
        return [main, ['Distr.', '2DMap'] + self.Add2SubHeader]

    def title(self, rp: data.RunPlan, dut_nr):
        d = dirname(rp.RelDirs[dut_nr])
        return f'{rp.Name} ({self.link(d, rp.TCString)}): {rp.Type.title()} of {self.link(dirname(d), rp.DUTs[dut_nr].Name)}, ' \
               f'Irradiation: {html.irr2str(rp.get_irradiation(dut_nr), unit=True)}, Position: {rp.Positions[dut_nr].title()}'

    @classmethod
    def row(cls, f, run: data.Run, dut_nr):
        d = run.RelDirs[dut_nr]
        values = run.FullData[dut_nr]
        row = [f(d, 'plots', run.Number), run.Biases[dut_nr]]
        row += [f(d, name, values[i]) for i, name in enumerate(['FluxProfile', 'Current'])]
        row += [f(d, n, html.fig_icon()) for n in ['HitMap', 'SignalDistribution', 'SignalMap2D']]
        return row + cls.add2row(f, d, values) + [values[9], run.StartTime, run.Duration, (run.Comment[:10], html.style(left=True))]

    @staticmethod
    def add2row(f, d, values):
        return []

    @classmethod
    def rows(cls, f, run_plan: data.RunPlan, dut_nr):
        tc = data.TestCampaigns[run_plan.TC]
        return [cls.row(f, tc.Runs[run], dut_nr) for run in run_plan.RunNumbers]

    @staticmethod
    def rowgetter(rp: data.RunPlan, dut_nr):
        return (lambda x: [x[rp.RunNumbers[0]][dut_nr]]) if rp.Size == 1 else lambda x: [r[dut_nr] for r in itemgetter(*rp.RunNumbers)(x)]

    def rlink(self, d, htmlname, target, **kwargs):
        return self.link(join(d, f'{htmlname}.html'), target, **prep_kw(kwargs, new_tab=True, colour=None))


class PadRunTable(RunTable):

    Add2Header = [('Signal', *html.opts(cs=5)), ('Pulser', *html.opts(cs=4))]
    Add2SubHeader = ['Pulse Height [mV]', 'Pedestal [mV]', 'Noise [1&sigma;]', 'Pulse Height [mV]', 'Sigma', 'Pedestal [mV]', 'Noise [1&sigma;]']

    @staticmethod
    def add2row(f, d, values):
        row = [f(d, name, values[i]) for i, name in enumerate(['PulseHeight5000', 'PedestalDistributionFitAllCuts'], 2)] + [values[4]]
        return row + [f(d, name, values[i]) for i, name in enumerate(['PulserPulseHeight', 'PulserDistributionFit', 'PedestalDistributionFitPulserBeamOn'], 5)] + [values[8]]


class PixRunTable(RunTable):

    Add2Header = [('Pulse Height', *html.opts(cs=3)), ('Efficiency', *html.opts(rs=2))]
    Add2SubHeader = ['Value [mV]']

    @staticmethod
    def add2row(f, d, values):
        return [f(d, name, values[i]) for i, name in [(2, 'PulseHeightNone'), (5, 'HitEff')]]


class FullRunTable(html.File):

    def __init__(self, website):

        super().__init__()
        self.Website = website
        self.Dir = join('content', 'beamtests')

    @update_pbar
    def build(self, tc):
        tc = data.TestCampaigns[tc]
        self.set_filename(join(self.Dir, tc.ID, 'index.html'))
        self.set_header(self.Website.get_header(f'Runs {tc}'))
        self.set_body('\n'.join([self.Website.NavBar.get(), html.table(self.title(tc), self.header, self.body(tc))]))
        self.save()

    @quiet
    def build_all(self):
        info('creating single run tables ...')
        PBAR.start(len(data.TestCampaigns), counter=True)
        for tc in data.TestCampaigns:
            self.build(tc)

    @staticmethod
    def title(tc: data.TestCampaign):
        return f'All Runs for {tc}'

    @property
    def header(self):
        return ['Runs', 'Type', 'FS11', 'FS13', 'Total Events', 'Start Time', 'Duration', 'DUT', 'Data', f'HV {html.small("[V]")}', f'I {html.small("[nA]", html.style(transform="none"))}',
                f'Flux {html.small(f"[kHz/cm{html.sup(2)}]", html.style(transform="none"))}', f'Pulse Height {html.small("[mV]", html.style(transform="none"))}', 'Ped / Eff', 'Good Events',
                'Comments']

    def body(self, tc: data.TestCampaign):
        rows = []
        for run in tc.Runs.values():
            for i in range(run.NDUTs):
                row = [] if i else [(v, *html.opts(rs=run.NDUTs)) for v in [run.Number, run.Type, run.FS11, run.FS13, run.EventStr, run.StartTime, run.Duration]]
                row += [(run.DUTs[i], html.style(nowrap=True)), self.link(join(run.RelDirs[i], 'plots.html'), html.LinkIcon, use_name=False), data.make_bias_str(run.Biases[i])] + run.get_short_data(i)
                rows.append(row + ([] if i else [(run.Comment, html.style(left=True), *html.opts(rs=run.NDUTs))]))
        return rows
