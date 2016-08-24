#!/usr/bin/env python
# cdorfer@ethz.ch


import sys
sys.path.append('AbstractClasses')
import HTML
from json import loads, dump
import pickle
from glob import glob
from Utils import *
from DiamondRateScans import DiaScans
from shutil import copy
from numpy import mean
from os import remove
from progressbar import Bar, ETA, FileTransferSpeed, Percentage, ProgressBar
from collections import OrderedDict


class DiamondTable:
    
    def __init__(self):
        self.Config = self.load_parser()

        self.Dir = get_dir()
        self.DataPath = '{dir}/{file}'.format(dir=get_dir(), file=self.Config.get('General', 'data_directory'))
        self.TestCampaigns = loads(self.Config.get("BeamTests", "dates"))
        self.OtherCols = loads(self.Config.get("Other", "columns"))
        self.Exclude = loads(self.Config.get("General", "exclude"))
        self.Data = load_json('{dir}/AbstractClasses/data.json'.format(dir=self.Dir))

        self.DiaScans = DiaScans()
        self.Diamonds = self.DiaScans.get_diamonds()
        self.create_diamond_folders()

    def create_diamond_folders(self):
        for dia in self.Diamonds:
            path = '{dat}{dia}'.format(dat=self.DataPath, dia=dia)
            create_dir(path)
            create_dir('{path}/BeamTests'.format(path=path))
            for col in self.OtherCols:
                create_dir('{path}/{col}'.format(path=path, col=col))

    @staticmethod
    def load_parser():
        p = ConfigParser()
        p.read('conf.ini')
        return p

    def build_everything(self):
        self.create_overview()
        self.create_runplan_overview()
        self.create_run_overview()

    # =====================================================
    # region OVERVIEW
    def create_overview(self):
        html_file = 'index.html'
        f = open(html_file, 'w')
        write_html_header(f, 'ETH Diamonds Overview')

        # single crystal
        f.write('<h3>Single Crystal Diamonds:</h3>\n')
        f.write(self.build_diamond_table())
        f.write('* Board Number\n\n')
        # poly chrystal
        f.write('\n<h3>Poly Crystal Diamonds:</h3>\n')
        f.write(self.build_diamond_table(scvd=False))
        f.write('* Board Number\n\n')
        # silicon pad
        f.write('\n<h3>Silicon Detectors:</h3>\n')
        f.write(self.build_diamond_table(si=True))
        f.write('* Board Number\n\n')
        # run overview
        f.write('\n<h3>Full Run Overview:</h3>\n')
        f.write(self.build_tc_table())
        f.write('\n\n\n</body>\n</html>\n')
        f.close()

    def build_diamond_table(self, scvd=True, si=False):
        header = self.build_header()
        scdias = loads(self.Config.get('General', 'single_crystal'))
        dias = [name.split('/')[-1] for name in glob('{dat}/*'.format(dat=self.DataPath)) if (name.split('/')[-1] in scdias if scvd else name.split('/')[-1] not in scdias)]
        for ex in self.Exclude:
            dias.remove(ex) if ex in dias else do_nothing()
        rows = []
        dias = ['SiD1'] if si else dias
        for dia in sorted(dias):
            row = [dia]
            proc = load_json('{dir}/{dia}/info.json'.format(dir=self.DataPath, dia=dia))
            # test campaigns
            last_tc = make_tc_str(self.TestCampaigns[0])
            for tc in self.TestCampaigns:
                tc_str = make_tc_str(tc)
                row_size = len(row)
                for value in make_info_str(last_tc, tc_str, proc):
                    row.append(value)
                if row_size == len(row):
                    row.append('')
                target = 'Diamonds/{dia}/BeamTests/{tc}/index.html'.format(tc=tc, dia=dia)
                row.append(make_link(target, path=self.Dir, use_name=False))
                last_tc = make_tc_str(tc)
            # other stuff
            for col in self.OtherCols:
                path = '{dat}{dia}/{col}/'.format(dat=self.DataPath, col=col, dia=dia)
                row.append(self.build_col(col, path))
            rows.append(row)
        return HTML.table(rows, header_row=header)

    def build_tc_table(self):
        header = ['Test Campaign', 'Tested Diamonds']
        rows = []
        for tc in self.TestCampaigns:
            path = '{dir}/BeamTests/{dat}'.format(dir=self.Dir, dat=tc)
            create_dir(path)
            self.build_full_run_table(tc, path)
            dias = str(list(z.DiaScans.get_diamonds(make_tc_str(tc)))).strip('[]').replace('\'', '')
            if dias:
                target = 'BeamTests/{tc}/index.html'.format(tc=tc)
                rows.append([make_link(target, make_tc_str(tc, txt=0), path=self.Dir), dias])
        return HTML.table(rows, header_row=header)

    def build_full_run_table(self, tc, path):
        html_file = '{path}/index.html'.format(path=path)
        f = open(html_file, 'w')
        tit = 'All Runs for the Beam Test Campaign in {tc}'.format(tc=make_tc_str(tc, txt=False))
        write_html_header(f, tit)
        header = ['Run', 'Type', 'Flux [kHz/cm{0}]'.format(sup(2)), 'FS11', 'FSH13', 'Start Time', 'Duration', 'Dia I', 'HV I [V]', 'Dia II', 'HV II [V]', 'Comments']
        rows = []
        if make_tc_str(tc) not in z.DiaScans.RunInfos:
            return
        runs = z.DiaScans.RunInfos[make_tc_str(tc)]
        sorted_runs = OrderedDict(sorted({int(run): data for run, data in runs.iteritems()}.iteritems()))
        for i, (run, data) in enumerate(sorted_runs.iteritems()):
            rows.append([run])
            rows[i] += [self.get_runtype(data), self.calc_flux(data), data['fs11'], data['fs13'], conv_time(data['starttime0']), self.calc_duration(data)]
            rows[i] += [k for j in [(self.DiaScans.load_diamond(data['dia{ch}'.format(ch=ch)]), make_bias_str(data['dia{ch}hv'.format(ch=ch)])) for ch in xrange(1, 3)] for k in j]
            rows[i] += [data['comments'][:100].replace('\\u03bc', '&mu').encode('utf-8')]
        f.write(HTML.table(rows, header_row=header))
        f.write('\n\n\n</body>\n</html>\n')
        f.close()

    @staticmethod
    def get_runtype(info):
        data = info['runtype']
        if 'signal' in data:
            return 'signal'
        elif 'pedes' in data:
            return 'pedestal'
        else:
            return data[:10]

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
        write_html_header(f, tit)
        header = ['Run Plans', 'Runs', 'Bias V', 'Leakage Current', 'Pulser', 'Pulse Height', 'Pedestal', 'Start', 'Duration']
        rows = []
        rps = {rp: (bias, ch) for bias, rps in rp_dict.iteritems() for rp, ch in rps.iteritems()}
        for i, (rp, (bias, ch)) in enumerate(sorted(rps.iteritems())):
            runs = self.DiaScans.get_runs(rp, tc)
            rows.append([make_link('RunPlan{rp}/index.php'.format(rp=make_rp_string(rp)), str(make_rp_string(rp)), path=path)])
            name = '{first}-{last}'.format(first=runs[0], last=runs[-1])
            rows[i] += [make_link('RunPlan{rp}/index.html'.format(rp=make_rp_string(rp)), name, path=path)]
            rows[i] += [make_bias_str(bias)]
            rows[i] += [make_link('RunPlan{rp}/PhPulserCurrent.png'.format(rp=make_rp_string(rp)), 'Plot', path=path, use_name=False)]
            info = z.DiaScans.RunInfos[tc][str(runs[0])]
            rows[i] += [make_link('RunPlan{rp}/CombinedPulserPulseHeights.png'.format(rp=make_rp_string(rp)), info['pulser'] if 'pulser' in info else '', path=path)]
            rows[i] += [make_link('RunPlan{rp}/CombinedPulseHeights.png'.format(rp=make_rp_string(rp)), 'Plot', path=path, use_name=False)]
            rows[i] += [make_link('RunPlan{rp}/Pedestal_Flux.png'.format(rp=make_rp_string(rp)), 'Plot', path=path, use_name=False)]
            runs = z.DiaScans.get_runs(rp, tc)
            rows[i] += [conv_time(z.DiaScans.RunInfos[tc][str(runs[0])]['starttime0'])]
            rows[i] += [self.calc_duration(z.DiaScans.RunInfos[tc][str(runs[0])], z.DiaScans.RunInfos[tc][str(runs[-1])])]

        f.write(HTML.table(rows, header_row=header))
        f.write('\n\n\n</body>\n</html>\n')
        f.close()
    # endregion

    # =====================================================
    # region RUNS
    def create_run_overview(self):
        for dia in self.Diamonds:
            rps = self.DiaScans.find_diamond_runplans(dia)
            for tc, item in rps.iteritems():
                rps = {rp: ch for rps in item.itervalues() for rp, ch in rps.iteritems()}
                for rp, ch in sorted(rps.iteritems()):
                    path = '{dat}{dia}/BeamTests/{tc}'.format(dat=self.DataPath, dia=dia, tc=make_tc_str(tc, 0))
                    runs = self.DiaScans.get_runs(rp, tc)
                    self.build_run_table(path, rp, tc, dia, runs, ch)
                    for run in runs:
                        run_path = '{path}/{run}'.format(path=path, run=run)
                        create_dir(run_path)
                        self.copy_index_php(run_path)

    def build_run_table(self, path, rp, tc, dia, runs, ch):
        html_file = '{path}/RunPlan{rp}/index.html'.format(path=path, rp=make_rp_string(rp))
        f = open(html_file, 'w')
        tit = 'Single Runs for Run Plan {rp} of {dia} for the Test Campaign in {tc}'.format(rp=make_rp_string(rp), tc=make_tc_str(tc), dia=dia)
        write_html_header(f, tit)
        header = ['Run', 'Type', 'HV [V]', 'Flux [kHz/cm{0}]'.format(sup(2)), 'Pulse Height [au]', 'Pedestal [au]', 'Sigma', 'Pulser [au]', 'Sigma', 'Start Time', 'Duration', 'Comments']
        rows = []
        file_names = ['PulseHeight20000', 'Pedestal_aball_cuts', 'PulserDistributionFit']
        for i, run in enumerate(runs):
            info = self.DiaScans.RunInfos[tc][str(run)]
            data = self.Data[tc][str(run)][str(ch)]
            run_path = '../{run}'.format(run=run)
            rows.append([make_link('{path}/index.php'.format(path=run_path), run, path=path)])
            rows[i] += [info['runtype'], make_bias_str(info['dia{ch}hv'.format(ch=ch)]), self.calc_flux(info)]
            links = [make_link('{path}/{name}.png'.format(path=run_path, name=name), dig_str(data[j]), path=path) for j, name in zip([0, 1, 3], file_names)]
            rows[i] += [links[0], links[1], dig_str(data[2]), links[2], dig_str(data[4])]
            rows[i] += [conv_time(info['starttime0']), self.calc_duration(info), info['comments'][:50]]
        f.write(HTML.table(rows, header_row=header))
        f.write('\n\n\n</body>\n</html>\n')
        f.close()
    # endregion

    def copy_logs(self):
        for tc in self.DiaScans.RunPlans:
            copy('/data/psi_{y}_{m}/run_log.json'.format(y=tc[:4], m=tc[-2:]), '{dir}/AbstractClasses/run_log{tc}.json'.format(dir=self.Dir, tc=tc))
        copy('/home/testbeam/testing/micha/myPadAnalysis/Runinfos/run_plans.json', '{dir}/AbstractClasses/'.format(dir=self.Dir))

    def copy_pics(self):
        widgets = ['Progress: ', Percentage(), ' ', Bar(marker='>'), ' ', ETA(), ' ', FileTransferSpeed()]
        n = len(glob('/home/testbeam/testing/micha/myPadAnalysis/Res*/*/*/png/*'))
        pbar = ProgressBar(widgets=widgets, maxval=n).start()
        k = 1
        used_runs = {}
        for dia in self.DiaScans.get_diamonds():
            rps = self.DiaScans.find_diamond_runplans(dia)
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
                        if not file_exists('{path}/{file}'.format(path=rp_path, file=pic)):
                            copy(name, rp_path)
                    runs = self.DiaScans.get_runs(rp, tc)
                    for run in runs:
                        if run in used_runs[tc][dia]:
                            continue
                        used_runs[tc][dia].append(run)
                        run_path = '{path}/{run}'.format(path=path, run=run)
                        for name in glob('/home/testbeam/testing/micha/myPadAnalysis/Results{0}/{1}/{2}/png/*'.format(tc, self.translate_dia(dia), str(run).zfill(3))):
                            pbar.update(k)
                            k += 1
                            pic = name.split('/')[-1]
                            if not file_exists('{path}/{file}'.format(path=run_path, file=pic)):
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
        file_names = '{tc}_{run}_{ch}_20000_eventwise_b2/{tc}_{run}_{ch}_ab2_fwhm_all_cuts/HistoFit_{tc}_{run}_{dia}_ped_corr_BeamOn'.format(tc=tc, run=run, ch=ch, dia=dia).split('/')
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
        path = '{dir}/AbstractClasses/data.json'.format(dir=self.Dir)
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
                        values = self.get_pickle(run, tc, ch, self.translate_dia(dia))
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
        dic = load_parser('{dir}/AbstractClasses/OldDiamondAliases.cfg'.format(dir=self.Dir))
        return dic.get('ALIASES', dia)


def get_dir():
    return os.path.dirname(os.path.realpath('__file__'))


if __name__ == '__main__':
    z = DiamondTable()
    z.build_everything()
