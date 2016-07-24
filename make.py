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
from progressbar import Bar, ETA, FileTransferSpeed, Percentage, ProgressBar


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
        # self.copy_pics()

    @staticmethod
    def load_parser():
        p = ConfigParser()
        p.read('conf.ini')
        return p

    def create_overview(self):
        html_file = 'index.html'
        f = open(html_file, 'w')
        write_html_header(f, 'ETH Diamonds Overview')

        # single crystal
        f.write('<h3>Single Crystal Diamonds:</h3>\n')
        f.write(self.build_diamond_table())
        # poly chrystal
        f.write('\n<h3>Poly Crystal Diamonds:</h3>\n')
        f.write(self.build_diamond_table(scvd=False))
        f.write('\n\n\n</body>\n</html>\n')
        f.close()

    def build_diamond_table(self, scvd=True):
        header = self.build_header()
        dias = [name.split('/')[-1] for name in glob('{dat}/*'.format(dat=self.DataPath)) if (name.split('/')[-1].startswith('S') if scvd else not name.split('/')[-1].startswith('S'))]
        for ex in self.Exclude:
            dias.remove(ex) if ex in dias else do_nothing()
        rows = []
        for dia in sorted(dias):
            row = [dia]
            # test campaigns
            for tc in self.TestCampaigns:
                path = '{dat}{dia}/BeamTests/{tc}/index.html'.format(dat=self.DataPath, tc=tc, dia=dia)
                row.append(make_link('/'.join(path.split('/')[3:])) if file_exists(path) else '')
            # other stuff
            for col in self.OtherCols:
                path = '{dat}{dia}/{col}/'.format(dat=self.DataPath, col=col, dia=dia)
                row.append(self.build_col(col, path))
            rows.append(row)
        return HTML.table(rows, header_row=header)

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
        header_row += [date for date in self.TestCampaigns]
        return header_row + [col for col in self.OtherCols]

    def create_runplan_overview(self):
        dias = self.DiaScans.get_diamonds()
        for dia in dias:
            path = '{dat}{dia}'.format(dat=self.DataPath, dia=dia)
            create_dir(path)
            create_dir('{path}/BeamTests'.format(path=path))
            for col in self.OtherCols:
                create_dir('{path}/{col}'.format(path=path, col=col))
            self.make_runplan_folders(dia)

    def make_runplan_folders(self, dia):
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
                file_path = '{path}/{file}'.format(path=rp_path, file=self.Config.get('General', 'index_php'))
                if not file_exists(file_path):
                    copy('{dir}/{file}'.format(dir=self.Dir, file=self.Config.get('General', 'index_php')), file_path)

    def build_runplan_table(self, path, rp_dict, tc):
        html_file = '{path}/index.html'.format(path=path)
        f = open(html_file, 'w')
        tc_str = datetime.strptime(tc, '%Y%m').strftime('%B %Y')
        tit = 'Run Plans for {dia} for the Test Campaign in {tc}'.format(dia=path.split('/')[4], tc=tc_str)
        write_html_header(f, tit)
        header = ['Run Plans']
        rows = [['Runs'], ['Bias [V]']]
        rps = {rp: bias for bias, rps in rp_dict.iteritems() for rp in rps}
        for rp, bias in sorted(rps.iteritems()):
            runs = self.DiaScans.get_runs(rp, tc)
            header.append(make_link('RunPlan{rp}/index.php'.format(rp=make_rp_string(rp)), str(make_rp_string(rp))))
            # todo make link here
            rows[0].append('{first}-{last}'.format(first=runs[0], last=runs[-1]))
            rows[1].append(str(int(bias)))

        f.write(HTML.table(rows, header_row=header))
        f.write('\n\n\n</body>\n</html>\n')
        f.close()

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
                path = '/home/testbeam/Desktop/psiresults/Diamonds/{0}/BeamTests/{1}'.format(dia, make_tc_str(tc, 0))
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
            dst = '/home/testbeam/Desktop/psiresults/Pickles/{0}/'.format(picdir)
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

    def create_run_overview(self):
        pass

    def build_run_table(self):
        pass


def get_dir():
    return os.path.dirname(os.path.realpath('__file__'))


if __name__ == "__main__":
    z = DiamondTable()
    z.create_overview()
    z.create_runplan_overview()
