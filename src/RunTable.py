# --------------------------------------------------------
#       RUN-TABLE FUNCTIONS
# created on October 14th 2016 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from Table import Table
from Utils import *
import HTML
from collections import OrderedDict


class RunTable(Table):

    def __init__(self):
        Table.__init__(self)

    def create_overview(self):
        for dia in self.Diamonds:
            rps = self.DiaScans.find_diamond_runplans(dia)
            for tc, item in rps.iteritems():
                rps = {rp: ch for rps in item.itervalues() for rp, ch in rps.iteritems()}
                for rp, ch in sorted(rps.iteritems()):
                    path = '{dat}{dia}/BeamTests/{tc}'.format(dat=self.DataPath, dia=dia, tc=make_tc_str(tc, 0))
                    runs = self.DiaScans.get_runs(rp, tc)
                    self.build_table(path, rp, tc, dia, runs, ch)
                    for run in runs:
                        run_path = '{path}/{run}'.format(path=path, run=run)
                        create_dir(run_path)
                        self.copy_index_php(run_path)

    def build_table(self, path, rp, tc, dia, runs, ch):
        if not tc == '201610':
            return
        html_file = '{path}/RunPlan{rp}/index.html'.format(path=path, rp=make_rp_string(rp))
        f = open(html_file, 'w')
        tit = 'Single Runs for Run Plan {rp} of {dia} for the Test Campaign in {tc}'.format(rp=make_rp_string(rp), tc=make_tc_str(tc), dia=dia)
        write_html_header(f, tit, bkg=self.BkgCol)
        header = ['Run',
                  'Type',
                  'HV [V]',
                  'Flux<br>[kHz/cm{0}]'.format(sup(2)),
                  'Distr.',
                  'Pulse Height [au]',
                  'Pedestal<br>(Sigma) [au]',
                  'Pul. [au]',
                  'Ped. [au]',
                  'Start Time',
                  'Duration',
                  'Comments']
        rows = []
        i = 0
        for run in runs:
            info = self.DiaScans.RunInfos[tc][str(run)]
            # data = self.Data[tc][str(run)][str(ch)] if str(run) in self.Data[tc] else [None] * 5
            data = self.get_new_pickle(run, tc, ch, dia)
            if not hasattr(data[0], 'Pars'):
                continue
            data = [(data[l].Parameter(j), data[l].ParError(j) if not l else data[l].Parameter(2)) if data[l] is not None else (None, None) for l, j in enumerate([0, 1, 1])]
            run_path = '../{run}'.format(run=run)
            file_names = ['{path}/{name}.png'.format(name=name, path=run_path) for name in ['PulseHeight10000', 'Pedestal_aball_cuts', 'PulserDistributionFit']]
            rows.append([make_link('{path}/index.php'.format(path=run_path), run, path=path)])
            rows[i] += [info['runtype'], make_bias_str(info['dia{ch}hv'.format(ch=ch)]), center_txt(self.calc_flux(info))]  # HV and Flux
            rows[i] += [center_txt(make_link('{path}/SignalDistribution.png'.format(path=run_path), 'Plot', path=path, use_name=False))]  # Distribution
            rows[i] += [center_txt(make_link(file_names[n], '{0} &plusmn {1}'.format(*[dig_str(data[n][k], '5.2f') for k in xrange(2)]))) for n in xrange(3)]   # PH / Ped / Pulser
            rows[i] += [make_link('{path}/Pedestal_abPulserBeamOn.png'.format(path=run_path), 'Plot', path=path, use_name=False)]
            rows[i] += [conv_time(info['starttime0']), self.calc_duration(info), info['comments'][:50]]
            i += 1
        f.write(add_bkg(HTML.table(rows, header_row=header), color=self.BkgCol))
        f.write('\n\n\n</body>\n</html>\n')
        f.close()

    def build_full_table(self, tc, path):
        html_file = '{path}/index.html'.format(path=path)
        f = open(html_file, 'w')
        tit = 'All Runs for the Beam Test Campaign in {tc}'.format(tc=make_tc_str(tc, txt=False))
        write_html_header(f, tit, bkg=self.BkgCol)
        header = ['Run', 'Type', 'Flux<br>[kHz/cm{0}]'.format(sup(2)), 'FS11', 'FSH13', 'Start Time', 'Duration', 'Dia I', 'HV I [V]', 'Dia II', 'HV II [V]', 'Comments']
        rows = []
        if make_tc_str(tc) not in self.DiaScans.RunInfos:
            return
        runs = self.DiaScans.RunInfos[make_tc_str(tc)]
        sorted_runs = OrderedDict(sorted({int(run): data for run, data in runs.iteritems()}.iteritems()))
        for i, (run, data) in enumerate(sorted_runs.iteritems()):
            rows.append([run])
            # Type - Flux - FS11 - FS13 - Start - Duration
            rows[i] += [self.get_runtype(data), center_txt(self.calc_flux(data)), data['fs11'], data['fs13'], conv_time(data['starttime0']), self.calc_duration(data)]
            rows[i] += [k for j in [(self.DiaScans.load_diamond(data['dia{ch}'.format(ch=ch)]), make_bias_str(data['dia{ch}hv'.format(ch=ch)])) for ch in xrange(1, 3)] for k in j]
            rows[i] += [data['comments'][:100]]
        f.write(add_bkg(HTML.table(rows, header_row=header), self.BkgCol))
        f.write('\n\n\n</body>\n</html>\n')
        f.close()
