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
        txt += head(bold('Single Runs for Run Plan {rp} of {dia} for the Test Campaign in {tc}'.format(rp=rp, dia=dia, tc=tc)))
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
                  '#rs2#Hit<br>Map',
                  '#cs5#Signal',
                  '#cs4#Pulser',
                  '#rs2#Start Time',
                  '#rs2#Duration',
                  '#rs2#Comments']

        def make_pic_link(pic_name, name, use_name=True, ftype='pdf'):
            return [make_abs_link(join(run_path, '{}.{}'.format(pic_name, ftype)), name, center=True, use_name=use_name)]

        rows = [[center_txt(txt) for txt in ['Distr.', '2DMap', 'Pulse Height [au]', 'Pedestal [au]', 'Noise [1&sigma;]', 'Pulse Height [au]', 'Sigma',
                                             'Pedestal [au]', 'Noise [1&sigma;]']]]
        for run in dc.Runs:
            info = dc.RunInfos[str(run)]
            run_path = join(dirname(dc.Path), str(run))
            create_dir(join(self.Dir, run_path))
            self.copy_index_php(run_path)
            row = [make_abs_link(join(run_path, 'index.php'), run)]                                             # Run
            row += [dc.Type]                                                                                    # Type
            row += [right_txt(make_bias_str(dc.Bias))]                                                          # Bias
            row += [center_txt(self.calc_flux(info))]                                                           # Flux
            row += make_pic_link('HitMap', 'Plot', use_name=False)                                              # Hit Map
            row += make_pic_link('SignalDistribution', 'Plot', use_name=False)                                  # Distribution
            row += make_pic_link('SignalMap2D', 'Plot', use_name=False)                                         # Signal Map
            row += make_pic_link('PulseHeight10000', dc.get_run_ph(run))                                        # PH
            row += make_pic_link('PedestalDistributionFitAllCuts', dc.get_run_ped(run))                         # Pedestal
            row += make_pic_link('PedestalDistributionFitAllCuts', dc.get_run_noise(run))                       # Pedestal Noise
            row += make_pic_link('PulserDistributionFit', dc.get_run_pul(run))                                  # Pulser
            row += make_pic_link('PulserDistributionFit', dc.get_run_pul(run, sigma=True))                      # Pulser Sigma
            row += make_pic_link('PedestalDistributionFitPulserBeamOn', dc.get_run_ped(run, pulser=True))       # Pulser Pedestal
            row += make_pic_link('PedestalDistributionFitPulserBeamOn', dc.get_run_noise(run, pulser=True))     # Pulser Pedestal Noise
            row += [conv_time(info['starttime0']), dc.calc_run_duration(run), info['comments']]                 # Start, Duration, Comments
            rows.append(row)
        return add_bkg(HTMLTable.table(rows, header_row=header), color=self.BkgCol)

    def build_tc(self, tc):

        info = self.DiaScans.RunInfos[tc]
        max_channels = get_max_channels(info)
        header = ['#rs2#Run',
                  '#rs2#Type',
                  '#rs2#Flux<br>[kHz/cm{0}]'.format(sup(2)),
                  '#rs2#FS11',
                  '#rs2#FSH13',
                  '#rs2#Start Time',
                  '#rs2#Duration']
        header += ['#cs2#{}'.format(txt) for txt in (['Front', 'Middle', 'Back'] if max_channels == 3 else ['Front', 'Back'])]
        header += ['#rs2#Comments']

        rows = [[center_txt(txt) for txt in ['Dia', 'HV [V]'] * max_channels]]
        for run, data in sorted(info.iteritems(), key=lambda (key, v): (int(key), v)):
            row = [center_txt(run)]
            row += [center_txt(data['runtype'])]
            row += [center_txt(self.calc_flux(data))]
            row += [right_txt(data['fs11'])]
            row += [right_txt(data['fs13'])]
            row += [center_txt(conv_time(data['starttime0']))]
            row += [self.DiaScans.calc_duration(tc, int(run))]
            for channel in get_dia_channels(data):
                dia = self.DiaScans.load_diamond(data['dia{}'.format(channel)])
                row += [make_abs_link(join('Diamonds', dia, 'index.html'), dia)]
                row += [make_bias_str(data['dia{}hv'.format(channel)])]
                if channel == '1' and max_channels != len(get_dia_channels(data)):
                    row += ['', '']
            row += [data['comments'][:100]]
            rows.append(row)
        return add_bkg(HTMLTable.table(rows, header_row=header), self.BkgCol)


if __name__ == '__main__':
    z = RunTable()
    s = DiaScan('201508', '05', '1')
