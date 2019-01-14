# --------------------------------------------------------
#       RUN-TABLE FUNCTIONS
# created on December 8th 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

import HTMLTable
from Table import Table
from Utils import *
from numpy import mean


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
        txt += head(bold('Run Plans for {dia} for the Test Campaign in {tc}'.format(dia=dia, tc=tc_to_str(tc, short=False))))
        txt += self.build_dia_table(dia_scans)
        return txt

    def build_tc_table(self, tc):

        info = self.DiaScans.RunPlans[tc]
        max_channels = get_max_channels(self.DiaScans.RunInfos[tc])

        def is_main_plan(runplan):
            return runplan.isdigit()

        def n_sub_plans(runplan):
            return sum(1 for plan in info if runplan in plan)

        header = ['#rs2#Run Plan',
                  '#rs2#Sub Plan',
                  '#rs2#Run Type',
                  '#rs2#Runs']
        header += ['#cs3#{}'.format(txt) for txt in (['Front', 'Middle', 'Back'] if max_channels == 3 else ['Front', 'Back'])]
        rows = [[center_txt(txt) for txt in ['Diamond', 'Detector', 'Bias [V]'] * max_channels]]

        for i, (rp, data) in enumerate(sorted(info.iteritems()), 1):
            row = ['#rs{n}#{rp}'.format(n=n_sub_plans(rp), rp=center_txt(rp))] if is_main_plan(rp) else []
            row += [center_txt(make_rp_string(rp))]
            row += [center_txt(data['type'])]
            row += [center_txt('{:03d} - {:03d}'.format(data['runs'][0], data['runs'][-1]))]
            dias, biases = self.DiaScans.get_rp_diamonds(tc, rp), self.DiaScans.get_rp_biases(tc, rp)
            if is_main_plan(rp):
                for dia, bias in zip(dias, biases):
                    if dia == 'None':
                        row += [''] * 3
                    else:
                        dia_link = make_abs_link(join('Diamonds', dia, 'BeamTests', tc_to_str(tc), 'RunPlan{}'.format(make_rp_string(rp)), 'index.html'), dia, center=True)
                        row += ['#rs{n}#{i}'.format(n=n_sub_plans(rp), i=i) for i in [dia_link, center_txt(self.get_info(dia, tc, 'type')), right_txt(make_bias_str(bias))]]
                        if dias.index(dia) == 0 and max_channels != len(dias):
                            row += [''] * 3
            elif max_channels != len(dias):
                row += [''] * 3
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
                  '#rs2#Leakage<br>Current',
                  '#cs4#Pulser',
                  '#cs4#Signal',
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
            row += [t_to_str(dc.StartTime)]                                                         # Start Time
            row += [dc.Duration]                                                                    # Duration
            rows.append(row)

        return add_bkg(HTMLTable.table(rows, header_row=header), color=self.BkgCol)

    def get_pulser_mean(self, runs, tc, rp, ch):
        if tc < '201505':
            return center_txt('?')
        try:
            att_string = 'None'
            if 'attenuators' in self.DiaScans.RunPlans[tc][rp]:
                att_string = self.DiaScans.RunPlans[tc][rp]['attenuators']['pulser' if 'pulser' in self.DiaScans.RunPlans[tc][rp]['attenuators'] else 'pulser{c}'.format(c=ch)]
            if att_string == 'None':
                return center_txt('-')
            attenuations = att_string.split('+') if att_string.lower() not in ['unknown', 'none'] else ['0']
            if '?' in attenuations:
                return center_txt('?')
            db = sum(int(att.lower().split('db')[0]) for att in attenuations)
            att = 10 ** (db / 20.)
            pulser_mean = mean([self.get_pickle(run, tc, ch, 'Pulser').Parameter(1) for run in runs])
            return center_txt('{:2.2f}'.format(pulser_mean * att))
        except TypeError:
            return center_txt('?')

    def get_pickle_mean(self, runs, tc, ch, name, par):
        if tc < '201508':
            return center_txt('?')
        try:
            signal, sigma = calc_mean([float(self.get_pickle(run, tc, ch, name).Parameter(par)) for run in runs])
        except (TypeError, ValueError, ReferenceError):
            return center_txt('?')
        return center_txt('{:2.2f} ({:.2f})'.format(signal, sigma))

    def get_noise(self, runs, tc, ch):
        return self.get_pickle_mean(runs, tc, ch, 'Pedestal', 2)

    def get_signal(self, runs, tc, ch):
        return self.get_pickle_mean(runs, tc, ch, 'PH', 0)

    def get_pulser(self, runs, tc, ch):
        return self.get_pickle_mean(runs, tc, ch, 'Pulser', 1)


if __name__ == '__main__':
    z = RunPlanTable()
    z.Diamond = 'S129'
    z.TestCampaign = '201508'
