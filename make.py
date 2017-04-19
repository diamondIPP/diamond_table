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
        f.write('<br/>*<br/>    BN  = Board Number\n')
        f.write('<br/>          Irr = Irradiation \n')
        f.write('<br/>          T   = Thickness \n\n')
        f.write('\n\n\n</body>\n</html>\n')
        f.close()

    def get_col_titles(self):
        cols = []
        for col in self.OtherCols:
            if col == 'Thickness':
                cols.append('T* [&mu;m]')
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
            row = [dia]
            # general information
            for col in self.OtherCols:
                row.append(self.build_col(col, dia))
            rows.append(row)
            # test campaigns
            last_tc = '201500'
            for tc in self.TestCampaigns:
                tc_str = make_tc_str(tc)
                row += self.make_info_str(last_tc, tc_str, dia)
                if not row[-1].startswith('#cs'):
                    target = join('Diamonds', dia, 'BeamTests', tc, 'index.html')
                    row.append(make_link(target, path=self.Dir, use_name=False))
                last_tc = make_tc_str(tc)
        return add_bkg(HTML.table(rows, header_row=header, ), 'lightgrey')


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

    @staticmethod
    def get_manufacturer(path):
        f_path = '{path}info.conf'.format(path=path)
        if file_exists(f_path):
            conf = load_parser(f_path)
            return make_link(conf.get('MAIN', 'url'), conf.get('MAIN', 'name'), new_tab=True)
        else:
            return ''

    def build_col(self, col, path):
        if col == 'Manufacturer':
            return self.get_manufacturer(path)

    def build_header(self):
        header_row = ['Diamond']
        for date in self.TestCampaigns:
            header_row += ['Proc.', 'BN*', date]
        return header_row + [col for col in self.OtherCols]

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
        header = ['Nr.', 'Type', 'Diamond<br>Attenuator', 'Pulser<br>Attenuator', 'Runs', 'Bias V', 'Leakage<br>Current', 'Pulser', 'Pulser<br>Ped.', 'Signal', 'Signal<br>Ped.', 'Start', 'Duration']
        rows = []
        rps = {rp: (bias, ch) for bias, rps in rp_dict.iteritems() for rp, ch in rps.iteritems()}
        for i, (rp, (bias, ch)) in enumerate(sorted(rps.iteritems())):
            runs = self.DiaScans.get_runs(rp, tc)
            rows.append([make_link('RunPlan{rp}/index.php'.format(rp=make_rp_string(rp)), str(make_rp_string(rp)), path=path, center=True)])
            rows[i] += [self.DiaScans.RunPlans[tc][rp]['type']]
            rows[i] += [self.DiaScans.RunPlans[tc][rp]['attenuators']['dia{ch}'.format(ch=ch)]] if 'attenuators' in self.DiaScans.RunPlans[tc][rp] else ['']
            rows[i] += [self.DiaScans.RunPlans[tc][rp]['attenuators']['pulser'.format(ch=ch)]] if 'attenuators' in self.DiaScans.RunPlans[tc][rp] else ['']
            name = '{first}-{last}'.format(first=runs[0], last=runs[-1])
            rows[i] += [make_link('RunPlan{rp}/index.html'.format(rp=make_rp_string(rp)), name, path=path)]
            rows[i] += [make_bias_str(bias)]
            rows[i] += [make_link('RunPlan{rp}/PhPulserCurrent.png'.format(rp=make_rp_string(rp)), 'Plot', path=path, use_name=False)]
            info = z.DiaScans.RunInfos[tc][str(runs[0])]
            rows[i] += [make_link('RunPlan{rp}/CombinedPulserPulseHeights.png'.format(rp=make_rp_string(rp)), info['pulser'] if 'pulser' in info else '', path=path)]
            rows[i] += [make_link('RunPlan{rp}/Pedestal_FluxPulserBeamOn.png'.format(rp=make_rp_string(rp)), 'Plot', path=path, use_name=False)]
            rows[i] += [make_link('RunPlan{rp}/CombinedPulseHeights.png'.format(rp=make_rp_string(rp)), 'Plot', path=path, use_name=False)]
            rows[i] += [make_link('RunPlan{rp}/Pedestal_Flux.png'.format(rp=make_rp_string(rp)), 'Plot', path=path, use_name=False)]
            runs = z.DiaScans.get_runs(rp, tc)
            rows[i] += [conv_time(z.DiaScans.RunInfos[tc][str(runs[0])]['starttime0'])]
            rows[i] += [self.calc_duration(z.DiaScans.RunInfos[tc][str(runs[0])], z.DiaScans.RunInfos[tc][str(runs[-1])])]

        f.write(add_bkg(HTML.table(rows, header_row=header), color=self.BkgCol))
        f.write('\n\n\n</body>\n</html>\n')
        f.close()
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

    def get_pickle(self, run, tc, ch, dia):
        ch = 0 if ch == 1 else 3
        pickle_dirs = ['Ph_fit', 'Pedestal', 'Pulser']
        file_names = '{tc}_{run}_{ch}_10000_eventwise_b2/{tc}_{run}_{ch}_ab2_fwhm_all_cuts/HistoFit_{tc}_{run}_{dia}_ped_corr_BeamOn'.format(tc=tc, run=run, ch=ch, dia=dia).split('/')
        pars = [0, 1, 1]
        data = []
        for i, (dir_, name) in enumerate(zip(pickle_dirs, file_names)):
            path = '{dir}/Pickles/{pic}/{f}.pickle'.format(dir=self.Dir, pic=dir_, f=name)
            if not file_exists(path):
                data.append(None)
                if i:
                    data.append(None)
                continue
            f = open(path)
            p = pickle.load(f)
            data.append(p.Parameter(pars[i]))
            if i:
                data.append(p.Parameter(pars[i] + 1))
            f.close()
        return data

    def create_pickle_data(self):
        path = '{dir}/src/data.json'.format(dir=self.Dir)
        f = open(path, 'w')
        data = {}
        for dia in self.DiaScans.get_diamonds():
            rps = self.DiaScans.find_diamond_runplans(dia)
            for tc, item in rps.iteritems():
                if tc not in data:
                    data[tc] = {}
                rps = {rp: ch for rps in item.itervalues() for rp, ch in rps.iteritems()}
                for rp, ch in sorted(rps.iteritems()):
                    runs = self.DiaScans.get_runs(rp, tc)
                    for run in runs:
                        try:
                            values = self.get_pickle(run, tc, ch, self.translate_dia(dia))
                        except ReferenceError:
                            values = [None] * 5
                        if run not in data[tc]:
                            data[tc][run] = {}
                        data[tc][run][ch] = values
        f.seek(0)
        dump(data, f, indent=2)
        f.truncate()
        f.close()

    def copy_index_php(self, path):
        file_path = '{path}/{file}'.format(path=path, file=self.Config.get('General', 'index_php'))
        if file_exists(file_path) and len(glob('{path}/*'.format(path=path))) <= 2:
            remove(file_path)
        if not file_exists(file_path) and len(glob('{path}/*'.format(path=path))) > 1:
            copy('{dir}/{file}'.format(dir=self.Dir, file=self.Config.get('General', 'index_php')), file_path)

    @staticmethod
    def calc_flux(info):
        if 'for1' not in info or info['for1'] == 0:
            if 'measuredflux' in info:
                return str('{0:5.0f}'.format(info['measuredflux'] * 2.48))
        pixel_size = 0.01 * 0.015
        if info['maskfile'] == 'None':
            area = [4160 * pixel_size, 4160 * pixel_size]
        else:
            f = open('{path}/masks/{mask}'.format(path=get_dir(), mask=info['maskfile']), 'r')
            data = []
            for line in f:
                if len(line) > 3:
                    line = line.split()
                    data.append([int(line[2])] + [int(line[3])])
            f.close()
            area = [(data[1][0] - data[0][0]) * (data[1][1] - data[0][1]) * pixel_size, (data[3][0] - data[2][0]) * (data[3][1] - data[2][1]) * pixel_size]
        flux = [info['for{0}'.format(i + 1)] / area[i] / 1000. for i in xrange(2)]
        return str('{0:5.0f}'.format(mean(flux)))

    @staticmethod
    def calc_duration(info1, info2=None):
        endinfo = info2 if info2 is not None else info1
        dur = conv_time(endinfo['endtime'], strg=False) - conv_time(info1['starttime0'], strg=False)
        dur += timedelta(days=1) if dur < timedelta(0) else timedelta(0)
        return str(dur)

    def translate_dia(self, dia):
        dic = load_parser('{dir}/data/OldDiamondAliases.cfg'.format(dir=self.Dir))
        return dic.get('ALIASES', dia)


def get_dir():
    return os.path.dirname(os.path.realpath('__file__'))


if __name__ == '__main__':
    z = DiamondTable()
    z.build_everything()
