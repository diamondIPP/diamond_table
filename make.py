#!/usr/bin/env python
# cdorfer@ethz.ch


import sys

sys.path.append('src')
import HTML
from json import loads
from glob import glob
from Utils import *
from shutil import copy
from progressbar import Bar, ETA, FileTransferSpeed, Percentage, ProgressBar
from RunTable import RunTable
from Table import Table
from os.path import basename, join


class DiamondTable(Table):
    def __init__(self):
        Table.__init__(self)

        self.RunTable = RunTable()

    def create_diamond_folders(self):
        for dia in self.Diamonds:
            path = '{dat}{dia}'.format(dat=self.DataPath, dia=dia)
            create_dir(path)
            create_dir('{path}/BeamTests'.format(path=path))

    def build_everything(self):
        self.create_overview()
        self.create_runplan_overview()
        self.RunTable.create_overview()

    # =====================================================
    # region OVERVIEW
    def create_overview(self):
        html_file = 'index.html'
        f = open(html_file, 'w')
        write_html_header(f, 'ETH Diamonds Overview', bkg=self.BkgCol)
        self.build_board_table()

        # single crystal
        f.write('<h3>{ln}\n</h4>'.format(ln=make_link('Diamonds/OLD/index.php', 'Tested before 2015')))
        f.write('<h3>Single Crystal Diamonds:</h3>\n')
        f.write(self.build_diamond_table(scvd=True))
        # poly chrystal
        f.write('\n<h3>Poly Crystal Diamonds:</h3>\n')
        f.write(self.build_diamond_table())
        # silicon pad
        f.write('\n<h3>Silicon Detectors:</h3>\n')
        f.write(self.build_diamond_table(si=True))
        # run overview
        f.write('\n<h3>Full Run Overview:</h3>\n')
        f.write(self.build_tc_table())
        f.write(self.build_legend())
        f.write('\n\n\n</body>\n</html>\n')
        f.close()

    def build_legend(self):
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

    def build_diamond_table(self, scvd=False, si=False):
        header, first_row = self.build_header()
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
                tc_str = make_tc_str(tc)
                row += self.make_info_str(tc_str, dia)
                if not row[-1].startswith('#cs'):
                    target = join('Diamonds', dia, 'BeamTests', tc, 'index.html')
                    row.append(make_link(target, path=self.Dir, name=self.make_set_string(tc, dia)))
        return add_bkg(HTML.table(rows, header_row=header, ), 'lightgrey')

    def make_set_string(self, tc, dia):
        start_runs = [str(run_plan['runs'][0]) for run_plan in self.DiaScans.RunPlans[make_tc_str(tc)].itervalues()]
        info = self.DiaScans.RunInfos[make_tc_str(tc)]
        dia_set = []
        for tup in [tuple(self.RunTable.translate_dia(info[run][d]) for d in ['dia1', 'dia2']) for run in start_runs]:
            dia_set += [tup] if tup not in dia_set else []
        return center_txt(' / '.join(['{i}{j}'.format(i=i, j='f' if not tup.index(dia) else 'b') for i, tup in enumerate(dia_set, 1) if dia in tup]))

    def make_info_str(self, tc_str, dia):
        info = ConfigParser()
        info.read(join(self.DataPath, dia, 'info.conf'))
        out = [''] * 3
        if tc_str not in info.sections():
            return ['#cs4#']
        options = info.options(tc_str)

        typ = '{0}'.format(info.get(tc_str, 'type')) if 'type' in options else ''
        out[0] = center_txt(typ)
        out[1] = center_txt('{0:.1e}'.format(float(info.get(tc_str, 'irradiation')))) if 'irradiation' in options else center_txt('0')
        if 'boardnumber' in options:
            out[2] = center_txt(info.get(tc_str, 'boardnumber'))
        else:
            out[2] = center_txt('-' if 'pix' in typ else '?')
        return out

    def build_tc_table(self):
        header = ['Test Campaign', 'Tested Diamonds']
        rows = []
        for tc in self.TestCampaigns:
            path = '{dir}/BeamTests/{dat}'.format(dir=self.Dir, dat=tc)
            create_dir(path)
            self.RunTable.build_full_table(tc, path)
            dias = str(list(z.DiaScans.get_diamonds(make_tc_str(tc)))).strip('[]').replace('\'', '')
            if dias:
                target = 'BeamTests/{tc}/index.html'.format(tc=tc)
                rows.append([make_link(target, make_tc_str(tc, txt=0), path=self.Dir), dias])
        return add_bkg(HTML.table(rows, header_row=header))

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

    def build_header(self):
        header_row = ['#rs2#Diamond'] + ['#rs2#{c}'.format(c=col) for col in self.get_col_titles()]
        second_row = []
        for date in self.TestCampaigns:
            header_row += ['#cs4#{d}'.format(d=date)]
            second_row += [center_txt(txt) for txt in [add_spacings('Type', 2), 'Irr* [neq]', make_link(join('BoardNumbers', 'bn.html'), 'BN*'), 'Data Set*']]
        return header_row, second_row

    def build_board_table(self):
        f = open('{dir}/BoardNumbers/bn.json'.format(dir=self.Dir))
        info = load(f)
        f.close()
        f = open('{dir}/BoardNumbers/bn.html'.format(dir=self.Dir), 'w')
        write_html_header(f, 'Diamond Amplifier Boards', bkg=self.BkgCol)
        header = ['Board Number', 'Pulser Type']
        rows = sorted([[center_txt(str(bn)), typ] for typ, bns in info.iteritems() for bn in bns])
        f.write(add_bkg(HTML.table(rows, header_row=header), color=self.BkgCol))
        f.write('\n\n\n</body>\n</html>\n')
        f.close()

    # endregion

    # =====================================================
    # region RUN PLANS
    def create_runplan_overview(self):
        for dia in self.Diamonds:
            rps = self.DiaScans.find_diamond_runplans(dia)
            path = '{dat}{dia}/BeamTests/'.format(dat=self.DataPath, dia=dia)
            for tc, item in rps.iteritems():
                if tc < '201508':
                    continue
                tc_string = datetime.strptime(tc, '%Y%m').strftime('%b%y')
                sub_path = '{path}{tc}'.format(path=path, tc=tc_string)
                create_dir(sub_path)
                runplans = sorted([str(j) for sl in [i.keys() for i in item.itervalues()] for j in sl])
                if runplans:
                    self.build_runplan_table(sub_path, item, tc)
                for rp in runplans:
                    rp_path = '{path}/RunPlan{rp}'.format(path=sub_path, rp=make_rp_string(rp))
                    create_dir(rp_path)
                    self.copy_index_php(rp_path)

    def build_runplan_table(self, path, rp_dict, tc):
        html_file = '{path}/index.html'.format(path=path)
        f = open(html_file, 'w')
        tit = 'Run Plans for {dia} for the Test Campaign in {tc}'.format(dia=path.split('/')[4], tc=make_tc_str(tc))
        write_html_header(f, tit, bkg=self.BkgCol)
        header = ['#rs2#Nr.', '#rs2#Type', '#rs2#Diamond<br>Attenuator', '#rs2#Pulser<br>Attenuator', '#rs2#Runs', '#rs2#Bias [V]', '#rs2#Leakage<br>Current',
                  '#cs4#Pulser', '#cs3#Signal', '#rs2#Start', '#rs2#Duration']
        rows = [[center_txt(txt) for txt in ['Type', 'Mean', 'Corr.', 'Ped.', 'Pulse Height', 'Ped.', 'Noise [&sigma;]']]]
        rps = {rp: (bias, ch) for bias, rps in rp_dict.iteritems() for rp, ch in rps.iteritems()}

        def make_pic_link(pic_name, text, use_name=True, ftype='pdf'):
            return [make_link(join(rp_dir, '{p}.{t}'.format(p=pic_name, t=ftype)), text, path=path, center=True, use_name=use_name)]

        for i, (rp, (bias, ch)) in enumerate(sorted(rps.iteritems()), 1):
            runs = self.DiaScans.get_runs(rp, tc)
            info = z.DiaScans.RunInfos[tc][str(runs[0])]
            rp_dir = 'RunPlan{rp}'.format(rp=make_rp_string(rp))
            name = '{first}-{last}'.format(first=runs[0], last=runs[-1])
            rows.append([make_link('RunPlan{rp}/index.php'.format(rp=make_rp_string(rp)), str(make_rp_string(rp)), path=path, center=True)])
            rows[i] += [self.DiaScans.RunPlans[tc][rp]['type']]                                                 # Run Plan Type
            rows[i] += self.get_attenuators(self.DiaScans.RunPlans[tc][rp], ch=ch, pulser=False)                # Diamond Attenuators
            rows[i] += self.get_attenuators(self.DiaScans.RunPlans[tc][rp], ch=ch, pulser=True)                 # Pulser Attenuators
            rows[i] += [make_link('RunPlan{rp}/index.html'.format(rp=make_rp_string(rp)), name, path=path)]     # Runs
            rows[i] += [right_txt(make_bias_str(bias))]                                                         # Bias
            rows[i] += make_pic_link('PhPulserCurrent', 'Plot', use_name=False)                                 # Leakage Current
            rows[i] += [info['pulser'] if 'pulser' in info else '']                                             # Pulser Type
            rows[i] += make_pic_link('CombinedPulserPulseHeights', self.get_pulser(runs, tc, ch))               # Pulser Pulse Height
            rows[i] += [self.get_pulser_mean(runs, tc, rp, ch)]                                                 # Pulser Pulse Height (corrected)
            rows[i] += make_pic_link('PedestalMeanFluxPulserBeamOn', 'Plot', use_name=False)                    # Pulser Pedestal
            rows[i] += make_pic_link('CombinedPulseHeights', self.get_signal(runs, tc, ch))                     # Signal Pulse Height
            rows[i] += make_pic_link('PedestalMeanFlux', 'Plot', use_name=False)                                # Signal Pedestal
            rows[i] += make_pic_link('PedestalSigmaFlux', self.get_noise(runs, tc, ch))                         # Noise
            rows[i] += [conv_time(z.DiaScans.RunInfos[tc][str(runs[0])]['starttime0'])]                         # Start Time
            rows[i] += [self.calc_duration(info, z.DiaScans.RunInfos[tc][str(runs[-1])])]                       # Duration

        f.write(add_bkg(HTML.table(rows, header_row=header), color=self.BkgCol))
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

    # endregion

    def copy_logs(self):
        for tc in self.DiaScans.RunPlans:
            copy('/data/psi_{y}_{m}/run_log.json'.format(y=tc[:4], m=tc[-2:]), '{dir}/data/run_log{tc}.json'.format(dir=self.Dir, tc=tc))
        copy('{ana}/Runinfos/run_plans.json'.format(ana=self.AnaDir), '{dir}/data/'.format(dir=self.Dir))

    def copy_pics(self, copy_all=False, runplan=None):
        widgets = ['Progress: ', Percentage(), ' ', Bar(marker='>'), ' ', ETA(), ' ', FileTransferSpeed()]
        n = len(glob('/home/testbeam/testing/micha/myPadAnalysis/Res*/*/*/png/*'))
        pbar = ProgressBar(widgets=widgets, maxval=n).start()
        k = 1
        used_runs = {}
        for dia in self.DiaScans.get_diamonds():
            rps = self.DiaScans.find_diamond_runplans(dia) if runplan is None else {make_tc_str(tc): {'bla': {make_runplan_string(runplan): 'bla'}} for tc in self.TestCampaigns}
            for tc, item in rps.iteritems():
                used_runs[tc] = {dia: []}
                runplans = sorted([str(j) for sl in [i.keys() for i in item.itervalues()] for j in sl])
                path = '/home/testbeam/Desktop/psi/Diamonds/{0}/BeamTests/{1}'.format(dia, make_tc_str(tc, 0))
                for rp in runplans:
                    rp_path = '{path}/RunPlan{rp}'.format(path=path, rp=make_rp_string(rp))
                    for name in glob('/home/testbeam/testing/micha/myPadAnalysis/Results{0}/{1}/runplan{2}/png/*'.format(tc, self.translate_dia(dia), rp)):
                        pbar.update(k)
                        k += 1
                        pic = name.split('/')[-1]
                        if not file_exists('{path}/{file}'.format(path=rp_path, file=pic)) or copy_all:
                            copy(name, rp_path)
                    runs = self.DiaScans.get_runs(rp, tc) if rp in self.DiaScans.RunPlans[tc] else []
                    for run in runs:
                        if run in used_runs[tc][dia]:
                            continue
                        used_runs[tc][dia].append(run)
                        run_path = '{path}/{run}'.format(path=path, run=run)
                        for name in glob('/home/testbeam/testing/micha/myPadAnalysis/Results{0}/{1}/{2}/png/*'.format(tc, self.translate_dia(dia), str(run).zfill(3))):
                            pbar.update(k)
                            k += 1
                            pic = name.split('/')[-1]
                            if not file_exists('{path}/{file}'.format(path=run_path, file=pic)) or copy_all:
                                copy(name, run_path)
        pbar.finish()

    @staticmethod
    def copy_pickles():
        picdirs = ['Ph_fit', 'Pulser', 'Pedestal']
        widgets = ['Progress: ', Percentage(), ' ', Bar(marker='>'), ' ', ETA(), ' ', FileTransferSpeed()]
        n = len([i for lst in [glob('/home/testbeam/testing/micha/myPadAnalysis/Configuration/Individual_Configs/{0}/*'.format(picdir)) for picdir in picdirs] for i in lst])
        pbar = ProgressBar(widgets=widgets, maxval=n).start()
        k = 1
        for picdir in picdirs:
            dst = '/home/testbeam/Desktop/psi/Pickles/{0}/'.format(picdir)
            for name in glob('/home/testbeam/testing/micha/myPadAnalysis/Configuration/Individual_Configs/{0}/*'.format(picdir)):
                pbar.update(k)
                k += 1
                pic = name.strip('/')[-1]
                if not file_exists('{path}/{file}'.format(path=dst, file=pic)):
                    copy(name, dst)
        pbar.finish()

    def copy_rp_pickle(self, rp, tc):
        pic_dic = {'Ph_fit': '', 'Pulser': 'HistoFit_', 'Pedestal': ''}
        rp = make_runplan_string(rp)
        runs = self.DiaScans.RunPlans[str(tc)][rp]['runs']
        files = []
        for picdir, name in pic_dic.iteritems():
            for run in runs:
                files += glob('{dir}/{sdir}/{n}{tc}_{r}*'.format(dir=self.AnaPickleDir, sdir=picdir, n=name, tc=tc, r=run))
        self.start_pbar(len(files))
        for i, f in enumerate(files, 1):
            copy(f, '{dir}/{sdir}'.format(dir=self.PickleDir, sdir=f.split('/')[-2]))
            self.ProgressBar.update(i)

    def copy_rp_pics(self, rp, tc, copy_all=False):
        rp = make_runplan_string(rp)
        runs = self.DiaScans.RunPlans[str(tc)][rp]['runs']
        anadir = '{dir}/Results{tc}/*'.format(dir=self.AnaDir, tc=tc)
        files = [i for lst in [glob('{dir}/{r}/png/*'.format(dir=anadir, r=run)) for run in runs] for i in lst] + glob('{dir}/runplan{rp}/png/*'.format(dir=anadir, rp=rp))
        this_dir = '{dir}/Diamonds/*/BeamTests/{tc}'.format(dir=self.Dir, tc=make_tc_str(tc, 0))
        existing_files = [i for lst in [glob('{dir}/{r}/*'.format(dir=this_dir, r=run)) for run in runs] for i in lst] + glob('{dir}/RunPlan{rp}/*'.format(dir=this_dir, rp=make_rp_string(rp)))
        self.start_pbar(len(files))
        for i, f in enumerate(files, 1):
            if not basename(f) in [basename(ef) for ef in existing_files] or copy_all:
                r_string = f.split('/')[-3]
                dia = self.translate_old_dia(f.split('/')[-4])
                sub_dir = 'RunPlan{r}'.format(r=make_rp_string(r_string.strip('runplan'))) if 'runplan' in f else r_string
                # print basename(f), '{dir}/{sdir}'.format(dir=this_dir.replace('*', dia), sdir=sub_dir)
                copy(f, '{dir}/{sdir}'.format(dir=this_dir.replace('*', dia), sdir=sub_dir))
            self.ProgressBar.update(i)


def get_dir():
    return os.path.dirname(os.path.realpath('__file__'))


if __name__ == '__main__':
    z = DiamondTable()
    z.build_everything()
