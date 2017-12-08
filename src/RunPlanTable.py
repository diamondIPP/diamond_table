# --------------------------------------------------------
#       RUN-TABLE FUNCTIONS
# created on December 8th 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

import HTMLTable
from Table import Table, dirname
from Utils import *


class RunPlanTable(Table):

    def __init__(self):
        Table.__init__(self)

    def build_all(self):
        for tc in self.TestCampaigns:
            self.build_table(make_tc_str(tc))

    def build_table(self, tc):

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
