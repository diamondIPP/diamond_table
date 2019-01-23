# --------------------------------------------------------
#       RUN-TABLE FUNCTIONS
# created on December 8th 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

import HTMLTable
from Table import Table
from Utils import *


class RunPlanTable(Table):

    def __init__(self):
        Table.__init__(self)

    def create_tc_overview(self):
        print_banner('CREATING TESTCAMPAIGN RUNPLAN TABLES')
        self.start_pbar(len(self.TestCampaigns))
        for i, tc in enumerate(self.TestCampaigns, 1):
            self.build_tc_table(str_to_tc(tc))
            self.ProgressBar.update(i)
        self.ProgressBar.finish()

    def get_tc_body(self, tc):
        txt = make_lines(3)
        txt += head(bold('Run Plan Ovierview for the Test Campaign in {tc}'.format(tc=tc_to_str(tc, short=False))))
        txt += self.build_tc_table(tc)
        return txt

    def get_dia_body(self, dia_scans):
        dia, tc = dia_scans[0].Diamond, dia_scans[0].TestCampaign
        txt = make_lines(3)
        dia_link = make_abs_link(join('Diamonds', dia, 'index.html'), dia, colour='darkblue')
        tc_link = make_abs_link(join('BeamTests', tc_to_str(tc), 'RunPlans.html'), tc_to_str(tc, short=False), colour='darkblue')
        txt += head(bold('Run Plans for {dia} for the Test Campaign in {tc}'.format(dia=dia_link, tc=tc_link)))
        txt += self.build_dia_table(dia_scans)
        return txt

    def build_tc_table(self, tc):

        run_info = self.DiaScans.RunPlans[tc]
        max_channels = get_max_channels(self.DiaScans.RunInfos[tc])

        def is_main_plan(runplan):
            return runplan.isdigit()

        def n_sub_plans(runplan):
            return sum(1 for plan in run_info if runplan in plan)

        header = ['#rs2#Run Plan',
                  '#rs2#Sub Plan',
                  '#rs2#Run Type',
                  '#rs2#Runs',
                  '#rs2#Events']
        header += ['#cs4#{}'.format(txt) for txt in (['Front', 'Middle', 'Back'] if max_channels == 3 else ['Front', 'Back'])]
        rows = [[center_txt(txt) for txt in ['Info', 'Diamond', 'Detector', 'Bias [V]'] * max_channels]]

        for i, (rp, data) in enumerate(sorted(run_info.iteritems()), 1):
            row = ['#rs{n}#{rp}'.format(n=n_sub_plans(rp), rp=center_txt(rp))] if is_main_plan(rp) else []
            row += [center_txt(make_rp_string(rp))]
            row += [center_txt(data['type'])]
            row += [center_txt('{:03d} - {:03d}'.format(data['runs'][0], data['runs'][-1]))]
            row += [center_txt(self.get_events(self.DiaScans.RunInfos[tc], data['runs']))]
            dias, biases = self.DiaScans.get_rp_diamonds(tc, rp), self.DiaScans.get_rp_biases(tc, rp)
            for dia, bias in zip(dias, biases):
                tc_dir = join('Diamonds', dia, 'BeamTests', tc_to_str(tc))
                row += [make_abs_link(join(tc_dir, 'RunPlan{}'.format(make_rp_string(rp)), 'index.html'), 'Runs', center=True)]
                if is_main_plan(rp):
                    if dia == 'None':
                        row += ['#ds4-{}#{}'.format(n_sub_plans(rp), center_txt('-'))]
                    else:
                        dia_link = make_abs_link(join(tc_dir, 'index.html'), dia, center=True)
                        row += ['#rs{n}#{i}'.format(n=n_sub_plans(rp), i=i) for i in [dia_link, center_txt(self.get_info(dia, tc, 'type')), right_txt(make_bias_str(bias))]]
                        if dias.index(dia) == 0 and max_channels != len(dias):
                            row += ['#ds4-{}#{}'.format(n_sub_plans(rp), center_txt('-'))]
            rows.append(row)
        return add_bkg(HTMLTable.table(rows, header_row=header), color=self.BkgCol)

    def build_dia_table(self, dia_scans):
        header = ['#rs2#Nr.',
                  '#rs2#Type',
                  '#rs2#Digitiser',
                  '#rs2#Position',
                  '#rs2#Diamond<br>Attenuator',
                  '#rs2#Pulser<br>Attenuator',
                  '#rs2#Runs',
                  '#rs2#Bias [V]',
                  '#rs2#Flux<br>[kHz/cm{0}]'.format(sup(2)),
                  '#rs2#Leakage<br>Current',
                  '#cs4#Pulser',
                  '#cs4#Signal',
                  '#rs2#Events',
                  '#rs2#Start',
                  '#rs2#Duration']
        rows = [[center_txt(txt) for txt in ['Type', 'Mean', 'Corr.', 'Ped.', 'Pulse Height', 'Corr', 'Ped.', 'Noise [&sigma;]']]]  # sub header
        path = dirname(dia_scans[0].Path)
        create_dir(join(self.Dir, path))

        def make_pic_link(pic_name, text, use_name=True, ftype='pdf'):
            return [make_abs_link(join(dc.Path, '{}.{}'.format(pic_name, ftype)), text, center=True, use_name=use_name)]

        for dc in dia_scans:
            rp_str = make_rp_string(dc.RunPlan)
            create_dir(join(self.Dir, dc.Path))
            self.copy_index_php(dc.Path)
            row = [make_abs_link(join(dc.Path, 'index.php'), rp_str, center=True)]                  # Nr
            row += [center_txt(dc.Type)]                                                            # Run Plan Type
            row += [center_txt(dc.Digitiser)]                                                       # Digitiser
            row += [center_txt(dc.DiaPosition)]                                                     # Diamond Position
            row += [center_txt(dc.Attenuator)]                                                      # Diamond Attenuators
            row += [center_txt(dc.PulserAttenuator)]                                                # Pulser Attenuators
            row += [make_abs_link(join(dc.Path, 'index.html'), dc.get_runs_str(), center=True)]     # Runs
            row += [right_txt(make_bias_str(dc.Bias))]                                              # Bias
            row += [right_txt(dc.get_flux_str())]                                                   # Flux
            row += make_pic_link('PhPulserCurrent', 'Plot', use_name=False)                         # Leakage Current
            row += [dc.PulserType]                                                                  # Pulser Type
            if dc.Type == 'voltage scan':
                row += make_pic_link('PulserVoltageScan', 'Plot', False)                            # Pulser Pulse Height
                row += [center_txt('-')]                                                            # Pulser Pulse Height (corrected)
                row += make_pic_link('PulserPedestalMeanVoltage', 'Plot', use_name=False)
                row += make_pic_link('SignalVoltageScan', 'Plot', False)
                row += [center_txt('-')]                                                            # makes no sense for Voltage Scan
                row += make_pic_link('PedestalMeanVoltage', 'Plot', False)
                row += make_pic_link('PedestalSigmaVoltage', dc.get_noise())
            else:
                row += make_pic_link('CombinedPulserPulseHeights', dc.get_pulser())                 # Pulser Pulse Height
                row += [dc.get_corrected_pulser()]                                                  # Pulser Pulse Height (corrected)
                row += make_pic_link('PulserPedestalMeanFlux', 'Plot', use_name=False)              # Pulser Pedestal
                row += make_pic_link('CombinedPulseHeights', dc.get_signal())                       # Pulse Height
                row += [dc.get_corrected_signal()]                                                  # Pulse Height (corrected)
                row += make_pic_link('PedestalMeanFlux', 'Plot', use_name=False)                    # Signal Pedestal
                row += make_pic_link('PedestalSigmaFlux', dc.get_noise())                           # Noise
            row += [center_txt(dc.Events)]                                                          # Events
            row += [t_to_str(dc.StartTime)]                                                         # Start Time
            row += [dc.Duration]                                                                    # Duration
            rows.append(row)

        return add_bkg(HTMLTable.table(rows, header_row=header), color=self.BkgCol)

    @staticmethod
    def get_events(run_info, runs):
        if all('events' in run_info[str(run)] for run in runs):
            n = sum(run_info[str(run)]['events'] for run in runs)
            return '{:1.1f}M'.format(n / 1e6)
        return '?'


if __name__ == '__main__':
    z = RunPlanTable()
    z.Diamond = 'S129'
    z.TestCampaign = '201508'
