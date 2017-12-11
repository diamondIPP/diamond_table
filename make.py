#!/usr/bin/env python
# cdorfer@ethz.ch


import sys

sys.path.append('src')
import HTMLTable
from json import loads
from glob import glob
from Utils import *
from shutil import copy
from progressbar import Bar, ETA, FileTransferSpeed, Percentage, ProgressBar
from RunTable import RunTable
from Table import Table
from RunPlanTable import RunPlanTable
from os.path import basename, join
from os import system
from numpy import mean
from datetime import datetime

this_year = datetime.now().year
start_year = 2015


class DiamondTable(Table):
    def __init__(self):
        Table.__init__(self)

        self.RunTable = RunTable()
        self.RunPlanTable = RunPlanTable()

    def create_diamond_folders(self):
        for dia in self.Diamonds:
            path = '{dat}{dia}'.format(dat=self.DataPath, dia=dia)
            create_dir(path)
            create_dir('{path}/BeamTests'.format(path=path))

    def build_everything(self):
        self.RunPlanTable.build_all()
        self.create_overview()
        self.create_runplan_overview()
        self.RunTable.create_overview()

    # =====================================================
    # region OVERVIEW
    def create_overview(self):
        print_banner('CREATING DIAMOND TABLES')
        years = range(start_year, this_year + 1)
        self.start_pbar(len(years))
        self.create_diamond_folders()
        for i, year in enumerate(years, 1):
            self.create_year_overview(year)
            self.ProgressBar.update(i)
        self.ProgressBar.finish()

    def create_year_overview(self, year):
        html_file = 'index{y}.html'.format(y=year)
        f = open(html_file, 'w')
        write_html_header(f, 'ETH Diamonds Overview', bkg=self.BkgCol)
        self.build_board_table()

        # single crystal
        f.write('<h3>{ln}\n</h4>'.format(ln=make_link('Diamonds/OLD/index.php', 'Tested before 2015')))
        f.write('<h3>Single Crystal Diamonds:</h3>\n')
        f.write(self.build_diamond_table(year, scvd=True))
        # poly chrystal
        f.write('\n<h3>Poly Crystal Diamonds:</h3>\n')
        f.write(self.build_diamond_table(year))
        # silicon pad
        f.write('\n<h3>Silicon Detectors:</h3>\n')
        f.write(self.build_diamond_table(year, si=True))
        # run overview
        f.write('\n<h3>Full Run Overview:</h3>\n')
        f.write(self.build_tc_table())
        f.write(self.build_legend())
        f.write('\n\n\n</body>\n</html>\n')
        f.close()
        if year == this_year:
            system('cp {f} index.html'.format(f=html_file))

    @staticmethod
    def build_legend():
        string = '<br/>*<br/>    BN  = Board Number\n'
        string += '<br/>         Irr = Irradiation \n'
        string += '<br/>         T   = Thickness \n'
        string += '<br/>         Data Set = Example "1f": Results of the front (f) diamond the first (1) measured set of diamonds during the beam test campaign \n\n'
        return string

    def get_col_titles(self):
        dic = {'Thickness': 'T* [&mu;m]', 'Manufacturer': add_spacings('Manufacturer')}
        cols = []
        for col in self.OtherCols:
            if col in dic:
                cols.append(dic[col])
            else:
                cols.append(col)
        return cols

    def get_diamond_names(self, scvd=False, si=False):
        all_dias = sorted([basename(name) for name in glob('{dat}/*'.format(dat=self.DataPath))])
        scdias = loads(self.Config.get('General', 'single_crystal'))
        si_diodes = loads(self.Config.get('General', 'si-diodes'))
        if scvd:
            return [dia for dia in all_dias if dia in scdias and dia not in self.Exclude]
        elif si:
            return [dia for dia in all_dias if dia in si_diodes and dia not in self.Exclude]
        else:
            return [dia for dia in all_dias if dia not in scdias + self.Exclude + si_diodes]

    def build_diamond_table(self, year, scvd=False, si=False):
        header, first_row = self.build_header(year)
        rows = [first_row]
        dias = self.get_diamond_names(scvd, si)
        for dia in dias:
            row = [make_link(join('Diamonds', dia, 'index.html'), name=dia, path=self.Dir, use_name=True)]
            # general information
            for col in self.OtherCols:
                row.append(self.build_col(col, dia))
            rows.append(row)
            # test campaigns
            for tc in self.TestCampaigns:
                if str(year)[2:] in tc:
                    tc_str = make_tc_str(tc)
                    row += self.make_info_str(tc_str, dia)
                    if not row[-1].startswith('#cs'):
                        target = join('Diamonds', dia, 'BeamTests', tc, 'index.html')
                        row.append(make_link(target, path=self.Dir, name=self.make_set_string(tc, dia)))
        return add_bkg(HTMLTable.table(rows, header_row=header, ), 'lightgrey')

    def make_set_string(self, tc, dia):
        dia_set = []
        for tup in [tuple(self.DiaScans.get_rp_diamonds(make_tc_str(tc), rp)) for rp in sorted(self.DiaScans.RunPlans[make_tc_str(tc)])]:
            dia_set += [tup] if tup not in dia_set else []
        return center_txt(' / '.join(['{i}{j}'.format(i=i, j='f' if not tup.index(dia) else 'b') for i, tup in enumerate(dia_set, 1) if dia in tup]))

    def make_info_str(self, tc_str, dia):
        if tc_str not in load_parser(join(self.DataPath, dia, 'info.conf')).sections():
            return ['#cs4#']
        typ = center_txt(self.get_info(dia, tc_str, 'type'))
        irr = self.get_info(dia, tc_str, 'irradiation')
        irr = center_txt('{0:.1e}'.format(float(irr)) if irr else '0')
        board_number = self.get_info(dia, tc_str, 'boardnumber')
        board_number = center_txt(board_number) if board_number else center_txt('-' if 'pix' in typ else '?')
        return [typ, irr, board_number]

    def build_tc_table(self):
        header = ['Test Campaign', 'Tested Diamonds']
        rows = []
        for tc in self.TestCampaigns:
            path = '{dir}/BeamTests/{dat}'.format(dir=self.Dir, dat=tc)
            create_dir(path)
            self.RunTable.build_full_table(tc, path)
            dias = str(list(self.DiaScans.get_diamonds(make_tc_str(tc)))).strip('[]').replace('\'', '')
            if dias:
                target = 'BeamTests/{tc}/index.html'.format(tc=tc)
                rows.append([make_link(target, make_tc_str(tc, long_=0), path=self.Dir), dias])
        return add_bkg(HTMLTable.table(rows, header_row=header))

    def get_manufacturer(self, dia):
        info_path = join(self.DataPath, dia, 'info.conf')
        f_path = join(self.DataPath, dia, 'Manufacturer', 'info.conf')

        if file_exists(info_path):
            conf = load_parser(info_path)
            return make_link(conf.get('Manufacturer', 'url'), name=conf.get('Manufacturer', 'name'), new_tab=True, center=True)
        elif file_exists(f_path):
            conf = load_parser(f_path)
            return make_link(conf.get('MAIN', 'url'), conf.get('MAIN', 'name'), new_tab=True, center=True)
        else:
            return ''

    def get_thickness(self, dia):
        info_path = join(self.DataPath, dia, 'info.conf')
        if file_exists(info_path):
            conf = load_parser(info_path)
            return center_txt(conf.get('Thickness', 'value')) if 'Thickness' in conf.sections() else center_txt('??')
        else:
            return center_txt('??')

    def build_col(self, col, dia):
        if col == 'Manufacturer':
            return self.get_manufacturer(dia)
        if col == 'Thickness':
            return self.get_thickness(dia)

    def build_header(self, year):
        header_row = ['#rs2#{d}'.format(d=add_spacings('Diamond'))] + ['#rs2#{c}'.format(c=col) for col in self.get_col_titles()]
        header_row += self.create_year_button(year - 1)
        second_row = []
        for date in self.TestCampaigns:
            if str(year)[2:] in date:
                header_row += ['#cs4#{d}'.format(d=make_link(join('BeamTests', date, 'RunPlans.html'), date, path=self.Dir))]
                second_row += [center_txt(txt) for txt in [add_spacings('Type', 2), 'Irr* [neq]', make_link(join('BoardNumbers', 'bn.html'), 'BN*'), 'Data Set*']]
        header_row += self.create_year_button(year + 1, before=False)
        return header_row, second_row

    def build_board_table(self):
        f = open('{dir}/BoardNumbers/bn.json'.format(dir=self.Dir))
        info = load(f)
        f.close()
        f = open('{dir}/BoardNumbers/bn.html'.format(dir=self.Dir), 'w')
        write_html_header(f, 'Diamond Amplifier Boards', bkg=self.BkgCol)
        header = ['Board Number', 'Pulser Type']
        rows = sorted([[center_txt(str(bn)), typ] for typ, bns in info.iteritems() for bn in bns])
        f.write(add_bkg(HTMLTable.table(rows, header_row=header), color=self.BkgCol))
        f.write('\n\n\n</body>\n</html>\n')
        f.close()

    # endregion

    # =====================================================
    # region RUN PLANS
    def create_runplan_overview(self):
        for dia in self.Diamonds:
            rps = self.DiaScans.find_dia_run_plans(dia)
            path = '{dat}{dia}/BeamTests/'.format(dat=self.DataPath, dia=dia)
            for tc, plans in rps.iteritems():
                if tc != '201705':
                    continue
                tc_string = make_tc_str(tc, long_=False)
                sub_path = '{path}{tc}'.format(path=path, tc=tc_string)
                create_dir(sub_path)
                self.build_runplan_table(sub_path, plans, tc)
                for rp, ch in plans:
                    rp_path = '{path}/RunPlan{rp}'.format(path=sub_path, rp=make_rp_string(rp))
                    create_dir(rp_path)
                    self.copy_index_php(rp_path)

    def build_runplan_table(self, path, plans, tc):
        html_file = '{path}/index.html'.format(path=path)
        f = open(html_file, 'w')
        tit = 'Run Plans for {dia} for the Test Campaign in {tc}'.format(dia=path.split('/')[4], tc=make_tc_str(tc))
        write_html_header(f, tit, bkg=self.BkgCol)
        header = ['#rs2#Nr.', '#rs2#Type', '#rs2#Diamond<br>Attenuator', '#rs2#Pulser<br>Attenuator', '#rs2#Runs', '#rs2#Bias [V]', '#rs2#Leakage<br>Current',
                  '#cs4#Pulser', '#cs3#Signal', '#rs2#Start', '#rs2#Duration']
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
            rows[i] += self.get_attenuators(self.DiaScans.RunPlans[tc][rp], ch=ch, pulser=False)                # Diamond Attenuators
            rows[i] += self.get_attenuators(self.DiaScans.RunPlans[tc][rp], ch=ch, pulser=True)                 # Pulser Attenuators
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
                rows[i] += make_pic_link('CombinedPulserPulseHeights', self.get_pulser(runs, tc, ch))               # Pulser Pulse Height
                rows[i] += [self.get_pulser_mean(runs, tc, rp, ch)]                                                 # Pulser Pulse Height (corrected)
                rows[i] += make_pic_link('PulserPedestalMeanFlux', 'Plot', use_name=False)                          # Pulser Pedestal
                rows[i] += make_pic_link('CombinedPulseHeights', self.get_signal(runs, tc, ch))
                rows[i] += make_pic_link('PedestalMeanFlux', 'Plot', use_name=False)                                # Signal Pedestal
                rows[i] += make_pic_link('PedestalSigmaFlux', self.get_noise(runs, tc, ch))                         # Noise
            rows[i] += [conv_time(self.DiaScans.RunInfos[tc][str(runs[0])]['starttime0'])]                         # Start Time
            rows[i] += [self.calc_duration(info, self.DiaScans.RunInfos[tc][str(runs[-1])])]                       # Duration

        f.write(add_bkg(HTMLTable.table(rows, header_row=header), color=self.BkgCol))
        f.write(self.create_home_button(path))
        f.write('\n\n\n</body>\n</html>\n')
        f.close()

    @staticmethod
    def get_attenuators(info, ch, pulser=False):
        if 'attenuators' in info:
            key = 'pulser' if pulser else 'dia'
            return [info['attenuators']['{k}{ch}'.format(k=key, ch='' if key in info['attenuators'] else ch)]]
        else:
            return ['']

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

    # endregion

    def copy_logs(self):
        for tc in self.DiaScans.RunPlans:
            if tc == '201707':
                copy('/data/psi_{y}_{m}/run_log.json'.format(y=tc[:4], m=tc[-2:]), '{dir}/data/run_log{tc}.json'.format(dir=self.Dir, tc=tc))
        copy('{ana}/Runinfos/run_plans.json'.format(ana=self.AnaDir), '{dir}/data/'.format(dir=self.Dir))

    @staticmethod
    def create_year_button(year, before=True):
        y_str = '{b}{y}{a}'.format(b='<< ' if before else '', y=year, a=' >>' if not before else '')
        btn_string = '#rs30#lightgrey</br> <button onclick="location.href={t}" type="button"> {s} </button>'.format(t="'index{y}.html'".format(y=year), s=y_str)
        return [btn_string] if start_year <= year <= this_year else []


def get_dir():
    return os.path.dirname(os.path.realpath('__file__'))


if __name__ == '__main__':
    z = DiamondTable()
    # z.build_everything()
