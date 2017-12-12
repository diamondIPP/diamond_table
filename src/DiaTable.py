#!/usr/bin/env python
# --------------------------------------------------------
#       Diamond Table
# created on April 25th 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

import HTMLTable
from Table import Table
from Utils import make_tc_str, join, write_html_header, add_bkg, make_link, make_bias_str, make_rp_string, center_txt, right_txt, conv_time, print_banner
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

        header = ['#rs2#Beam Test', '#rs2#Nr. ', '#rs2#Type', '#rs2#Runs', '#cs2#Attenuators', '#rs2#Bias [V]', '#rs2#Leakage<br>Current', '#cs3#Pulser', '#cs2#Signal', '#rs2#Start', '#rs2#Duration']
        rows = [[center_txt(text) for text in ['Diamond', 'Pulser', 'Type', 'Mean', 'Ped.', 'Distr.', 'Ped.']]]
        run_plans = self.DiaScans.find_diamond_runplans(dia)
        path = join(self.DataPath, dia)

        def make_pic_link(pic_name, name, use_name=True):
            return [make_link(join(rp_target, pic_name), name, path=path, center=True, use_name=use_name)]

        i_row = 1
        for tc, dic in sorted(run_plans.iteritems()):
            tc_plans = {rp: (ch, bias) for bias, rps in dic.iteritems() for rp, ch in rps.iteritems()}

            rows += [['#rs{n}#{tc}'.format(n=len(tc_plans), tc=center_txt(make_tc_str(tc)))]]
            for rp, (ch, bias) in sorted(tc_plans.iteritems()):
                print dia, tc, rp
                runs = self.DiaScans.get_runs(rp, tc)
                rp_target = join('BeamTests', make_tc_str(tc, 0), 'RunPlan{r}'.format(r=make_rp_string(rp)))
                rows += [[]] if len(rows[-1]) > 1 else []
                rows[i_row] += [make_link(join(rp_target, 'index.php'), name=make_rp_string(rp), path=path, center=True)]       # Nr
                rows[i_row] += [center_txt(self.DiaScans.RunPlans[tc][rp]['type'])]                                             # Type
                rows[i_row] += [make_link(join(rp_target, 'index.html'), '{b}-{e}'.format(b=runs[0], e=runs[-1]), path=path)]   # Runs
                if 'attenuators' in self.DiaScans.RunPlans[tc][rp]:                                                             # Attenuators
                    rows[i_row] += [center_txt(self.DiaScans.RunPlans[tc][rp]['attenuators']['dia{ch}'.format(ch=ch)])]
                    if 'pulser' in self.DiaScans.RunPlans[tc][rp]['attenuators']:
                        rows[i_row] += [center_txt(self.DiaScans.RunPlans[tc][rp]['attenuators']['pulser'.format(ch=ch)])]
                    else:
                        rows[i_row] += [center_txt(self.DiaScans.RunPlans[tc][rp]['attenuators']['pulser{ch}'.format(ch=ch)])]
                else:
                    rows[i_row] += [center_txt('?'), center_txt('?')]
                rows[i_row] += [right_txt(make_bias_str(bias))]
                rows[i_row] += [make_link(join(rp_target, 'PhPulserCurrent.png'), 'Plot', path=path, use_name=False, center=True)]
                info = self.DiaScans.RunInfos[tc][str(runs[0])]
                rows[i_row] += make_pic_link('CombinedPulserPulseHeights.png', info['pulser'] if 'pulser' in info else '?')
                rows[i_row] += make_pic_link('CombinedPulserPulseHeights.png', self.get_pulser_mean(runs, tc, rp, ch))
                rows[i_row] += make_pic_link('Pedestal_FluxPulserBeamOn.png', 'Plot', use_name=False)
                rows[i_row] += make_pic_link('CombinedPulseHeights.png', 'Plot', use_name=False)
                rows[i_row] += make_pic_link('Pedestal_Flux.png', 'Plot', use_name=False)
                runs = self.DiaScans.get_runs(rp, tc)
                rows[i_row] += [conv_time(self.DiaScans.RunInfos[tc][str(runs[0])]['starttime0'])]
                rows[i_row] += [self.calc_duration(self.DiaScans.RunInfos[tc][str(runs[0])], self.DiaScans.RunInfos[tc][str(runs[-1])])]
                i_row += 1
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
        except Exception:
            return center_txt('?')

if __name__ == '__main__':
    z = DiaTable()
    z.build_table('S129')