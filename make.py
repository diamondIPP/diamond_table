#!/usr/bin/env python
# cdorfer@ethz.ch


import sys
sys.path.append('AbstractClasses')
import HTML
from json import loads
from glob import glob
from Utils import *
from DiamondRateScans import DiaScans
from shutil import copy


class DiamondTable:
    
    def __init__(self):
        self.Config = self.load_parser()

        self.Dir = get_dir()
        self.DataPath = '{dir}/{file}'.format(dir=get_dir(), file=self.Config.get('General', 'data_directory'))
        self.TestCampaigns = loads(self.Config.get("BeamTests", "dates"))
        self.OtherCols = loads(self.Config.get("Other", "columns"))
        self.Exclude = loads(self.Config.get("General", "exclude"))

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
        for dia in self.DiaScans.get_diamonds():
            rps = self.DiaScans.find_diamond_runplans(dia)
            for tc, item in rps.iteritems():
                runplans = sorted([str(j) for sl in [i.keys() for i in item.itervalues()] for j in sl])
                for rp in runplans:
                    tc_str = datetime.strptime(tc, '%Y%m').strftime('%b%y')
                    dst = '/home/testbeam/Desktop/psiresults/Diamonds/{0}/BeamTests/{1}/RunPlan{2}'.format(dia, tc_str, rp[1:] if rp[0] == '0' else rp)
                    for name in glob('/home/testbeam/testing/micha/myPadAnalysis/Results{0}/{1}/runplan{2}/png/*'.format(tc, dia, rp)):
                        pic = name.split('/')[-1]
                        if not file_exists('{path}/{file}'.format(path=dst, file=pic)):
                            copy(name, dst)

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
