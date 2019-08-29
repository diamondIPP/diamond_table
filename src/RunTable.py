# --------------------------------------------------------
#       RUN-TABLE FUNCTIONS
# created on October 14th 2016 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------


import HTMLTable
from Table import Table
from Utils import *
from DiaScan import DiaScan


class RunTable(Table):

    def __init__(self):
        Table.__init__(self)

    def get_body(self, dia_scan):
        txt = make_lines(3)
        rp, dia, tc = dia_scan.RunPlanStr, dia_scan.Diamond, tc_to_str(dia_scan.TestCampaign, short=False)
        dia_link = make_abs_link(join('Diamonds', dia, 'index.html'), dia, colour='darkblue')
        tc_link = make_abs_link(join('BeamTests', tc_to_str(dia_scan.TestCampaign), 'RunPlans.html'), tc, colour='darkblue')
        txt += head(bold('Single Runs for Run Plan {rp} of {dia} for the Test Campaign in {tc}'.format(rp=rp, dia=dia_link, tc=tc_link)))
        txt += self.build(dia_scan)
        return txt

    def get_tc_body(self, tc):
        txt = make_lines(3)
        txt += head(bold('All Runs for the Beam Test Campaign in {tc}'.format(tc=tc_to_str(tc, short=False))))
        txt += self.build_tc(tc)
        return txt

    def build(self, dc):

        header = ['#rs2#Run',
                  '#rs2#Type',
                  '#rs2#HV [V]',
                  '#rs2#Flux<br>[kHz/cm{0}]'.format(sup(2)),
                  '#rs2#Current<br>[nA]',
                  '#rs2#Hit<br>Map',
                  '#cs5#Signal',
                  '#cs4#Pulser',
                  '#rs2#Events',
                  '#rs2#Start Time',
                  '#rs2#Duration',
                  '#rs2#Comments']

        def make_pic_link(pic_name, name, use_name=True, ftype='pdf'):
            return [make_abs_link(join(run_path, '{}.{}'.format(pic_name, ftype)), name, center=True, use_name=use_name, warn=dc.Diamond not in self.Exclude)]

        rows = [[center_txt(txt) for txt in ['Distr.', '2DMap', 'Pulse Height [au]', 'Pedestal [au]', 'Noise [1&sigma;]', 'Pulse Height [au]', 'Sigma',
                                             'Pedestal [au]', 'Noise [1&sigma;]']]]
        for run in dc.Runs:
            run_info = dc.RunInfos[str(run)]
            run_path = join(dirname(dc.Path), str(run))
            self.copy_index_php(run_path)
            run_html = join(run_path, 'index.html') if file_exists(join(self.Dir, run_path, 'index.html')) else join(run_path, 'index.php')
            row = [make_abs_link(run_html, run, warn=dc.Diamond not in self.Exclude)]                                   # Run
            row += [dc.Type]                                                                                            # Type
            row += [right_txt(make_bias_str(dc.get_run_bias(run)))]                                                     # Bias
            row += [center_txt(dc.get_run_flux(run))]                                                                   # Flux
            row += make_pic_link('Currents{}_{}_{}'.format(dc.TestCampaign, run, dc.Channel), dc.get_run_current(run))  # Current
            row += make_pic_link('HitMap', 'Plot', use_name=False)                                                      # Hit Map
            row += make_pic_link('SignalDistribution', 'Plot', use_name=False)                                          # Distribution
            row += make_pic_link('SignalMap2D', 'Plot', use_name=False)                                                 # Signal Map
            row += make_pic_link('PulseHeight10000', dc.get_run_ph(run))                                                # PH
            row += make_pic_link('PedestalDistributionFitAllCuts', dc.get_run_ped(run))                                 # Pedestal
            row += make_pic_link('PedestalDistributionFitAllCuts', dc.get_run_noise(run))                               # Pedestal Noise
            row += make_pic_link('PulserDistributionFit', dc.get_run_pul(run))                                          # Pulser
            row += make_pic_link('PulserDistributionFit', dc.get_run_pul(run, sigma=True))                              # Pulser Sigma
            row += make_pic_link('PedestalDistributionFitPulserBeamOn', dc.get_run_ped(run, pulser=True))               # Pulser Pedestal
            row += make_pic_link('PedestalDistributionFitPulserBeamOn', dc.get_run_noise(run, pulser=True))             # Pulser Pedestal Noise
            row += [center_txt(dc.get_run_events(run))]                                                                 # Events
            row += [dc.get_run_start(run), dc.calc_run_duration(run), run_info['comments'][:80]]                        # Start, Duration, Comments
            rows.append(row)
        return add_bkg(HTMLTable.table(rows, header_row=header), color=self.BkgCol)

    def build_tc(self, tc):

        run_info = self.DiaScans.RunInfos[tc]
        max_channels = get_max_channels(run_info)
        header = ['#rs2#Run',
                  '#rs2#Type',
                  '#rs2#Flux<br>[kHz/cm{0}]'.format(sup(2)),
                  '#rs2#FS11',
                  '#rs2#FSH13',
                  '#rs2#Events',
                  '#rs2#Start Time',
                  '#rs2#Duration']
        header += ['#cs2#{}'.format(txt) for txt in (['Front', 'Middle', 'Back'] if max_channels == 3 else ['Front', 'Back'])]
        header += ['#rs2#Comments']

        rows = [[center_txt(txt) for txt in ['Dia', 'HV [V]'] * max_channels]]
        for run, data in sorted(run_info.iteritems(), key=lambda (key, v): (int(key), v)):
            row = [center_txt(run)]
            row += [center_txt(data['runtype'])]
            row += [center_txt(calc_flux(data))]
            row += [right_txt(data['fs11'])]
            row += [right_txt(data['fs13'])]
            row += [center_txt(self.get_run_events(data))]
            row += [center_txt(conv_time(data['starttime0']))]
            row += [self.DiaScans.calc_duration(tc, int(run))]
            for channel in get_dia_channels(data):
                dia = self.DiaScans.load_diamond(data['dia{}'.format(channel)])
                row += [make_abs_link(join('Diamonds', dia, 'index.html'), dia, warn=dia not in self.Exclude)]
                row += [make_bias_str(data['dia{}hv'.format(channel)])]
                if channel == '1' and max_channels != len(get_dia_channels(data)):
                    row += ['', ''] * (max_channels - len(get_dia_channels(data)))
            row += [data['comments'][:100]]
            rows.append(row)
        return add_bkg(HTMLTable.table(rows, header_row=header), self.BkgCol)

    @staticmethod
    def get_run_events(run_info):
        if 'events' in run_info:
            n = run_info['events']
            return '{:1.1f}M'.format(n / 1e6) if n > 1e6 else '{:1.0f}k'.format(n / 1e3)
        return '?'


if __name__ == '__main__':
    z = RunTable()
    s = DiaScan('201508', '05', '1')
