#!/usr/bin/env python
# --------------------------------------------------------
#       Diamond Table
# created on April 25th 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

import HTMLTable
from Table import Table
from Utils import make_tc_str, join, write_html_header, add_bkg, make_link, make_bias_str, make_rp_string, center_txt, right_txt, conv_time, print_banner, make_runs_str, log_warning
from numpy import mean


class DiaTable(Table):

    def __init__(self):
        Table.__init__(self)

    def create_all(self):
        print_banner('CREATING SINGLE DIAMOND TABLES')
        self.start_pbar(len(self.Diamonds))
        for i, dia in enumerate(self.Diamonds, 1):
            self.build_table(dia)
            self.ProgressBar.update(i)
        self.ProgressBar.finish()

    def build_table(self, dia):
        html_file = join(self.DataPath, dia, 'index.html')
        f = open(html_file, 'w')
        tit = 'Overview of all RunPlans for Diamond {d}'.format(d=dia)
        write_html_header(f, tit, bkg=self.BkgCol)

        header = ['#rs2#Beam Test',
                  '#rs2#Nr. ',
                  '#rs2#Position',
                  '#rs2#Type',
                  '#rs2#Runs',
                  '#cs2#Attenuators',
                  '#rs2#Bias [V]',
                  '#rs2#Leakage<br>Current',
                  '#cs3#Pulser',
                  '#cs2#Signal',
                  '#rs2#Start',
                  '#rs2#Duration']
        rows = [[center_txt(text) for text in ['Diamond', 'Pulser', 'Type', 'Mean', 'Ped.', 'Distr.', 'Ped.']]]
        run_plans = self.DiaScans.find_dia_run_plans(dia)
        path = join(self.DataPath, dia)

        def make_pic_link(pic_name, name, use_name=True):
            return [make_link(join(rp_target, pic_name), name, path=path, center=True, use_name=use_name)]

        for tc, plans in sorted(run_plans.iteritems()):
            row = ['#rs{n}#{tc}'.format(n=len(plans), tc=center_txt(make_tc_str(tc)))]                                          # Test Campaign
            for rp, ch in sorted(plans):
                rp_info = self.DiaScans.RunPlans[tc][rp]
                run_info = self.DiaScans.RunInfos[tc][str(rp_info['runs'][0])]
                rp_target = join('BeamTests', make_tc_str(tc, 0), 'RunPlan{r}'.format(r=make_rp_string(rp)))
                row = row if rp == plans[0][0] else []
                row += [make_link(join(rp_target, 'index.php'), name=make_rp_string(rp), path=path)]                            # Nr
                row += [center_txt(self.DiaScans.get_dia_position(tc, rp, ch))]                                                 # Position
                row += [center_txt(rp_info['type'])]                                                                            # Type
                row += [make_link(join(rp_target, 'index.html'), make_runs_str(rp_info['runs']), path=path)]                    # Runs
                if 'attenuators' in self.DiaScans.RunPlans[tc][rp]:                                                             # Attenuators
                    row += [center_txt(self.DiaScans.RunPlans[tc][rp]['attenuators']['dia{ch}'.format(ch=ch)])]
                    if 'pulser' in self.DiaScans.RunPlans[tc][rp]['attenuators']:                                               # Pulser Attenuators
                        log_warning('Add pulser attenuator for each channel for rp {rp} in {tc}'.format(rp=rp, tc=tc))
                        row += [center_txt(self.DiaScans.RunPlans[tc][rp]['attenuators']['pulser'])]
                    else:
                        row += [center_txt(self.DiaScans.RunPlans[tc][rp]['attenuators']['pulser{ch}'.format(ch=ch)])]
                else:
                    log_warning('Add  attenuators for rp {rp} in {tc}'.format(rp=rp, tc=tc))
                    row += [center_txt('?'), center_txt('?')]
                row += [right_txt(make_bias_str(self.DiaScans.get_biases(rp, tc, ch)))]                                         # Bias
                row += [make_link(join(rp_target, 'PhPulserCurrent.png'), 'Plot', path=path, use_name=False, center=True)]      # Leakage Current
                row += make_pic_link('CombinedPulserPulseHeights.png', run_info['pulser'] if 'pulser' in run_info else '?')     # Pulser Type
                row += make_pic_link('CombinedPulserPulseHeights.png', self.get_pulser_mean(rp_info['runs'], tc, rp, ch))       # Pulser Mean
                row += make_pic_link('Pedestal_FluxPulserBeamOn.png', 'Plot', use_name=False)                                   # Pulser Pedestals
                row += make_pic_link('CombinedPulseHeights.png', 'Plot', use_name=False)                                        # Signal PH
                row += make_pic_link('Pedestal_Flux.png', 'Plot', use_name=False)                                               # Signal Pedestal
                row += [conv_time(self.DiaScans.RunInfos[tc][str(rp_info['runs'][0])]['starttime0'])]                           # Start Time
                row += [self.DiaScans.calc_duration(tc, rp)]                                                                    # Duration
                rows.append(row)
        f.write(add_bkg(HTMLTable.table(rows, header_row=header), color=self.BkgCol))
        f.write('\n\n\n</body>\n</html>\n')
        f.close()

    def get_pulser_mean(self, runs, tc, rp, ch):
        if tc <= '201505':
            return center_txt('?')
        try:
            att_string = 'None'
            if 'attenuators' in self.DiaScans.RunPlans[tc][rp]:
                att_string = self.DiaScans.RunPlans[tc][rp]['attenuators']['pulser' if 'pulser' in self.DiaScans.RunPlans[tc][rp]['attenuators'] else 'pulser{c}'.format(c=ch)]
            attenuations = att_string.split('+') if att_string.lower() not in ['unknown', 'none'] else ['0']
            db = sum(int(att.lower().split('db')[0]) for att in attenuations)
            att = 10 ** (db / 20.)
            pulser_mean = mean([self.get_pickle(run, tc, ch, 'Pulser').Parameter(1) for run in runs])
            return center_txt('{:2.2f}'.format(pulser_mean * att))
        except (TypeError, ValueError):
            return center_txt('?')


if __name__ == '__main__':
    z = DiaTable()
    z.build_table('S129')
