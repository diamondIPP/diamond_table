# --------------------------------------------------------
#       RUN-TABLE FUNCTIONS
# created on December 8th 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

import HTMLTable
from Table import Table, dirname
from Utils import *
from numpy import mean


class RunPlanTable(Table):

    def __init__(self):
        Table.__init__(self)

    def create_tc_overview(self):
        print_banner('CREATING TESTCAMPAIGN RUNPLAN TABLES')
        self.start_pbar(len(self.TestCampaigns))
        for i, tc in enumerate(self.TestCampaigns, 1):
            if tc != make_tc_str(self.TestCampaign, long_=False) and self.TestCampaign is not None:
                continue
            self.build_tc_table(make_tc_str(tc))
            self.ProgressBar.update(i)
        self.ProgressBar.finish()

    def build_tc_table(self, tc):

        html_file = join(self.Dir, 'BeamTests', make_tc_str(tc, long_=False), 'RunPlans.html')
        f = open(html_file, 'w')
        tit = 'All Run Plans for the Test Campaign in {tc}'.format(tc=make_tc_str(tc))
        write_html_header(f, tit, bkg=self.BkgCol)

        def is_main_plan(runplan):
            return runplan.isdigit()

        def n_sub_plans(runplan):
            return sum(1 for plan in self.DiaScans.RunPlans[tc] if runplan in plan)

        def max_diamonds():
            return max(self.DiaScans.get_n_diamonds(tc, plan) for plan in self.DiaScans.RunPlans[tc])

        header = ['#rs2#Run Plan',
                  '#rs2#Sub Plan',
                  '#rs2#Run Type',
                  '#rs2#Runs',
                  '#cs3#Front Pad',
                  '#cs3#Back Pad']
        rows = [[center_txt(txt) for txt in ['Diamond', 'Detector', 'Bias [V]'] * max_diamonds()]]

        for i, (rp, info) in enumerate(sorted(self.DiaScans.RunPlans[tc].iteritems()), 1):
            row = ['#rs{n}#{rp}'.format(n=n_sub_plans(rp), rp=center_txt(rp))] if is_main_plan(rp) else []
            row += [rp]
            row += [info['type']]
            row += ['{min} - {max}'.format(min=str(min(info['runs'])).zfill(3), max=str(max(info['runs'])).zfill(3))]
            if is_main_plan(rp):
                for dia, bias in zip(self.DiaScans.get_rp_diamonds(tc, rp), self.DiaScans.get_rp_biases(tc, rp)):
                    if dia == 'None':
                        row += ['#cs3#']
                    else:
                        dia_link = make_link(join('..', '..', 'Diamonds', dia, 'BeamTests', make_tc_str(tc, 0), 'RunPlan{rp}'.format(rp=make_rp_string(rp)), 'index.html'), dia)
                        row += ['#rs{n}#{i}'.format(n=n_sub_plans(rp), i=i) for i in [dia_link, center_txt(self.get_info(dia, tc, 'type')), right_txt(make_bias_str(bias))]]
            rows.append(row)
        f.write(add_bkg(HTMLTable.table(rows, header_row=header), color=self.BkgCol))
        f.write(self.create_home_button(dirname(html_file)))
        f.write('\n\n\n</body>\n</html>\n')
        f.close()

    def create_dia_overview(self):
        print_banner('CREATING DIAMOND RUNPLAN TABLES')
        self.start_pbar(len(self.Diamonds))
        for i, dia in enumerate(self.Diamonds, 1):
            if dia != self.Diamond and self.Diamond is not None:
                continue
            rps = self.DiaScans.find_dia_run_plans(dia)
            path = '{dat}{dia}/BeamTests/'.format(dat=self.DataPath, dia=dia)
            for tc, plans in rps.iteritems():
                if tc != self.TestCampaign and self.TestCampaign is not None:
                    continue
                tc_string = make_tc_str(tc, long_=False)
                sub_path = '{path}{tc}'.format(path=path, tc=tc_string)
                create_dir(sub_path)
                self.build_dia_table(sub_path, plans, tc)
                for rp, ch in plans:
                    rp_path = '{path}/RunPlan{rp}'.format(path=sub_path, rp=make_rp_string(rp))
                    create_dir(rp_path)
                    self.copy_index_php(rp_path)
            self.ProgressBar.update(i)
        self.ProgressBar.finish()

    def build_dia_table(self, path, plans, tc):
        html_file = '{path}/index.html'.format(path=path)
        f = open(html_file, 'w')
        tit = 'Run Plans for {dia} for the Test Campaign in {tc}'.format(dia=path.split('/')[4], tc=make_tc_str(tc))
        write_html_header(f, tit, bkg=self.BkgCol)
        header = ['#rs2#Nr.',
                  '#rs2#Type',
                  '#rs2#Position',
                  '#rs2#Diamond<br>Attenuator',
                  '#rs2#Pulser<br>Attenuator',
                  '#rs2#Runs',
                  '#rs2#Bias [V]',
                  '#rs2#Leakage<br>Current',
                  '#cs4#Pulser',
                  '#cs3#Signal',
                  '#rs2#Start',
                  '#rs2#Duration']
        rows = [[center_txt(txt) for txt in ['Type', 'Mean', 'Corr.', 'Ped.', 'Pulse Height', 'Ped.', 'Noise [&sigma;]']]]
        # rps = {rp: (bias, ch) for bias, rps in rp_dict.iteritems() for rp, ch in rps.iteritems()}

        def make_pic_link(pic_name, text, use_name=True, ftype='pdf'):
            return [make_link(join(rp_dir, '{p}.{t}'.format(p=pic_name, t=ftype)), text, path=path, center=True, use_name=use_name)]

        # for i, (rp, (bias, ch)) in enumerate(sorted(rps.iteritems()), 1):
        for i, (rp, ch) in enumerate(plans, 1):
            runs = self.DiaScans.get_runs(rp, tc)
            info = self.DiaScans.RunInfos[tc][str(runs[0])]
            rp_dir = 'RunPlan{rp}'.format(rp=make_rp_string(rp))
            name = '{first}-{last}'.format(first=runs[0], last=runs[-1])
            volt_scan = self.DiaScans.RunPlans[tc][rp]['type'] == 'voltage scan'
            rows.append([make_link('RunPlan{rp}/index.php'.format(rp=make_rp_string(rp)), str(make_rp_string(rp)), path=path, center=True)])
            rows[i] += [self.DiaScans.RunPlans[tc][rp]['type']]                                                 # Run Plan Type
            rows[i] += [center_txt(self.DiaScans.get_dia_position(tc, rp, ch))]                                                 # Diamond Position
            rows[i] += self.DiaScans.get_attenuators(tc, rp, ch)                                                # Diamond Attenuators
            rows[i] += self.DiaScans.get_attenuators(tc, rp, ch, pulser=True)                                   # Pulser Attenuators
            rows[i] += [make_link('RunPlan{rp}/index.html'.format(rp=make_rp_string(rp)), name, path=path)]     # Runs
            rows[i] += [right_txt(make_bias_str(self.DiaScans.get_biases(rp, tc, ch)))]                         # Bias
            rows[i] += make_pic_link('PhPulserCurrent', 'Plot', use_name=False)                                 # Leakage Current
            rows[i] += [info['pulser'] if 'pulser' in info else '']                                             # Pulser Type
            if volt_scan:
                rows[i] += make_pic_link('PulserVoltageScan', 'Plot', False)                                    # Pulser Pulse Height
                rows[i] += [center_txt('-')]                                                                    # Pulser Pulse Height (corrected)
                rows[i] += make_pic_link('PulserPedestalMeanVoltage', 'Plot', use_name=False)
                rows[i] += make_pic_link('SignalVoltageScan', 'Plot', False)
                rows[i] += make_pic_link('PedestalMeanVoltage', 'Plot', False)
                rows[i] += make_pic_link('PedestalSigmaVoltage', self.get_noise(runs, tc, ch))
            else:
                rows[i] += make_pic_link('CombinedPulserPulseHeights', self.get_pulser(runs, tc, ch))           # Pulser Pulse Height
                rows[i] += [self.get_pulser_mean(runs, tc, rp, ch)]                                             # Pulser Pulse Height (corrected)
                rows[i] += make_pic_link('PulserPedestalMeanFlux', 'Plot', use_name=False)                      # Pulser Pedestal
                rows[i] += make_pic_link('CombinedPulseHeights', self.get_signal(runs, tc, ch))
                rows[i] += make_pic_link('PedestalMeanFlux', 'Plot', use_name=False)                            # Signal Pedestal
                rows[i] += make_pic_link('PedestalSigmaFlux', self.get_noise(runs, tc, ch))                     # Noise
            rows[i] += [conv_time(self.DiaScans.RunInfos[tc][str(runs[0])]['starttime0'])]                      # Start Time
            rows[i] += [self.DiaScans.calc_duration(tc, rp)]                                                    # Duration

        f.write(add_bkg(HTMLTable.table(rows, header_row=header), color=self.BkgCol))
        f.write(self.create_home_button(path))
        f.write('\n\n\n</body>\n</html>\n')
        f.close()

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
