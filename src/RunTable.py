# --------------------------------------------------------
#       RUN-TABLE FUNCTIONS
# created on October 14th 2016 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from collections import OrderedDict

import HTMLTable
from Table import Table
from Utils import *


class RunTable(Table):

    def __init__(self):
        Table.__init__(self)

    def create_overview(self):
        for dia in self.Diamonds:
            for tc, plans in self.DiaScans.find_dia_run_plans(dia).iteritems():
                for rp, ch in plans:
                    path = '{dat}{dia}/BeamTests/{tc}'.format(dat=self.DataPath, dia=dia, tc=make_tc_str(tc, 0))
                    runs = self.DiaScans.get_runs(rp, tc)
                    self.build_table(path, rp, tc, dia, runs, ch)
                    for run in runs:
                        run_path = '{path}/{run}'.format(path=path, run=run)
                        create_dir(run_path)
                        self.copy_index_php(run_path)

    def build_table(self, path, rp, tc, dia, runs, ch):
        # if not tc == '201508' or not dia == 'II6-79':
        if dia == 'None':
            return
        if tc == '201707' and dia == 'SiD6' and rp == '02':
            return
        # if not tc > '201612' or dia == 'II6-A2' or dia == 'Si352':
        if not tc == '201705':
            return
        print tc, rp, dia
        html_file = '{path}/RunPlan{rp}/index.html'.format(path=path, rp=make_rp_string(rp))
        f = open(html_file, 'w')
        tit = 'Single Runs for Run Plan {rp} of {dia} for the Test Campaign in {tc}'.format(rp=make_rp_string(rp), tc=make_tc_str(tc), dia=dia)
        write_html_header(f, tit, bkg=self.BkgCol)

        header = ['#rs2#Run',
                  '#rs2#Type',
                  '#rs2#HV [V]',
                  '#rs2#Flux<br>[kHz/cm{0}]'.format(sup(2)),
                  '#rs2#Hit<br>Map',
                  '#cs5#Signal',
                  '#cs4#Pulser',
                  '#rs2#Start Time',
                  '#rs2#Duration',
                  '#rs2#Comments']

        def make_entry(plot_name, value, value2=None):
            value2 = ' ({0})'.format(value2) if value2 is not None else ''
            return [center_txt(make_link(file_name.format(plot_name), '{0}{1}'.format(value, value2), path=path))]

        rows = [[center_txt(txt) for txt in ['Distr.', '2DMap', 'Pulse Height [au]', 'Pedestal [au]', 'Noise [1&sigma;]', 'Pulse Height [au]', 'Sigma',
                                             'Pedestal [au]', 'Noise [1&sigma;]']]]
        for i, run in enumerate(runs, 1):
            info = self.DiaScans.RunInfos[tc][str(run)]
            data = {tag: self.get_pickle(run, tc, ch, tag, form) for tag, form in zip(['PH', 'Pedestal', 'Pulser', 'PulserPed'], ['2.2f', '2.2f', '2.2f', '2.2f'])}
            run_path = '../{run}'.format(run=run)
            file_name = '{path}/{{0}}.png'.format(path=run_path)
            rows.append([make_link('{path}/index.php'.format(path=run_path), run, path=path)])                                              # Run
            rows[i] += [info['runtype']]                                                                                                    # Type
            rows[i] += [make_bias_str(info['dia{ch}hv'.format(ch=ch)])]                                                                     # HV
            rows[i] += [center_txt(self.calc_flux(info))]                                                                                   # Flux
            rows[i] += [center_txt(make_link('{path}/HitMap.pdf'.format(path=run_path), 'Plot', path=path, use_name=False))]                # Hit Map
            rows[i] += [center_txt(make_link('{path}/SignalDistribution.pdf'.format(path=run_path), 'Plot', path=path, use_name=False))]    # Distribution
            rows[i] += [center_txt(make_link('{path}/SignalMap2D.pdf'.format(path=run_path), 'Plot', path=path, use_name=False))]           # Signal Map
            rows[i] += make_entry('PulseHeight10000', data['PH'].Parameter(0), data['PH'].ParError(0))                                      # PH
            rows[i] += make_entry('Pedestal_aball_cuts', data['Pedestal'].Parameter(1))                                                     # Pedestal
            rows[i] += make_entry('Pedestal_aball_cuts', data['Pedestal'].Parameter(2))                                                     # Pedestal Noise
            rows[i] += make_entry('PulserDistributionFit', data['Pulser'].Parameter(1), data['Pulser'].ParError(1))                         # Pulser
            rows[i] += make_entry('PulserDistributionFit', data['Pulser'].Parameter(2))                                                     # Pulser Sigma
            rows[i] += make_entry('Pedestal_abPulserBeamOn', data['PulserPed'].Parameter(1))                                                # Pulser Pedestal
            rows[i] += make_entry('Pedestal_abPulserBeamOn', data['PulserPed'].Parameter(2))                                                # Pulser Ped Noise
            rows[i] += [conv_time(info['starttime0']), self.DiaScans.calc_duration(tc, run), info['comments'][:50]]                                     # comments
        f.write(add_bkg(HTMLTable.table(rows, header_row=header), color=self.BkgCol))
        f.write(self.create_home_button(join(path, 'index.php')))
        f.write('\n\n\n</body>\n</html>\n')
        f.close()

    def build_full_table(self, tc, path):
        html_file = '{path}/index.html'.format(path=path)
        f = open(html_file, 'w')
        tit = 'All Runs for the Beam Test Campaign in {tc}'.format(tc=make_tc_str(tc, long_=False))
        write_html_header(f, tit, bkg=self.BkgCol)
        header = ['Run', 'Type', 'Flux<br>[kHz/cm{0}]'.format(sup(2)), 'FS11', 'FSH13', 'Start Time', 'Duration', 'Dia I', 'HV I [V]', 'Dia II', 'HV II [V]', 'Comments']
        rows = []
        tc = make_tc_str(tc)
        if tc not in self.DiaScans.RunInfos:
            return
        runs = self.DiaScans.RunInfos[tc]
        sorted_runs = OrderedDict(sorted({int(run): data for run, data in runs.iteritems()}.iteritems()))
        for i, (run, data) in enumerate(sorted_runs.iteritems()):
            rows.append([run])
            # Type - Flux - FS11 - FS13 - Start - Duration
            rows[i] += [self.get_runtype(data), center_txt(self.calc_flux(data)), data['fs11'], data['fs13'], conv_time(data['starttime0']), self.DiaScans.calc_duration(tc, run)]
            rows[i] += [k for j in [(self.DiaScans.load_diamond(data['dia{ch}'.format(ch=ch)]), make_bias_str(data['dia{ch}hv'.format(ch=ch)])) for ch in xrange(1, 3)] for k in j]
            rows[i] += [data['comments'][:100]]
        f.write(add_bkg(HTMLTable.table(rows, header_row=header), self.BkgCol))
        f.write('\n\n\n</body>\n</html>\n')
        f.close()
