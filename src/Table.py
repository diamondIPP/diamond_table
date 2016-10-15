# --------------------------------------------------------
#       TABLE BASE CLASS
# created on October 14th 2016 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from json import loads

from Utils import *
from DiamondRateScans import DiaScans
from os import remove
from shutil import copy
from glob import glob
from numpy import mean
import pickle


def get_program_dir():
    return '/'.join(dirname(realpath(__file__)).split('/')[:-1])


class Table:

    def __init__(self):

        self.Dir = get_program_dir()
        self.ConfigFileName = 'conf.ini'
        self.Config = self.load_parser()

        self.DataPath = '{dir}/{file}'.format(dir=self.Dir, file=self.Config.get('General', 'data_directory'))
        self.AnaDir = self.Config.get('General', 'analysis_dir')
        self.TestCampaigns = loads(self.Config.get("BeamTests", "dates"))
        self.OtherCols = loads(self.Config.get("Other", "columns"))
        self.Exclude = loads(self.Config.get("General", "exclude"))

        try:
            self.Data = load_json('{dir}/data/data.json'.format(dir=self.Dir))
        except ValueError:
            self.Data = {}
        self.DiaScans = DiaScans(self.Dir)
        self.Diamonds = self.DiaScans.get_diamonds()

        self.BkgCol = 'lightgrey'

    def load_parser(self):
        p = ConfigParser()
        p.read('{dir}/{file}'.format(dir=self.Dir, file=self.ConfigFileName))
        return p

    def copy_index_php(self, path):
        file_path = '{path}/{file}'.format(path=path, file=self.Config.get('General', 'index_php'))
        if file_exists(file_path) and len(glob('{path}/*'.format(path=path))) <= 2:
            remove(file_path)
        if not file_exists(file_path) and len(glob('{path}/*'.format(path=path))) > 1:
            copy('{dir}/{file}'.format(dir=self.Dir, file=self.Config.get('General', 'index_php')), file_path)

    def calc_flux(self, info):
        if 'for1' not in info or info['for1'] == 0:
            if 'measuredflux' in info:
                return str('{0:5.0f}'.format(info['measuredflux'] * 2.48))
        pixel_size = 0.01 * 0.015
        if info['maskfile'] == 'None':
            area = [4160 * pixel_size, 4160 * pixel_size]
        else:
            f = open('{path}/masks/{mask}'.format(path=self.Dir, mask=info['maskfile']), 'r')
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

    @staticmethod
    def get_runtype(info):
        data = info['runtype']
        if 'signal' in data:
            return 'signal'
        elif 'pedes' in data:
            return 'pedestal'
        else:
            return data[:10]

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

    def get_new_pickle(self, run, tc, ch, dia):
        ch = 0 if ch == 1 else 3
        dia = self.translate_dia(dia)
        pickle_dirs = ['Ph_fit', 'Pedestal', 'Pulser']
        file_names = '{tc}_{run}_{ch}_10000_eventwise_b2/{tc}_{run}_{ch}_ab2_fwhm_all_cuts/HistoFit_{tc}_{run}_{dia}_ped_corr_BeamOn'.format(tc=tc, run=run, ch=ch, dia=dia).split('/')
        data = []
        for dir_, name in zip(pickle_dirs, file_names):
            path = '{dir}/Pickles/{pic}/{f}.pickle'.format(dir=self.Dir, pic=dir_, f=name)
            if not file_exists(path):
                data.append(None)
            else:
                f = open(path)
                p = pickle.load(f)
                data.append(p)
                f.close()
        return data

    def translate_dia(self, dia):
        dic = load_parser('{dir}/data/OldDiamondAliases.cfg'.format(dir=self.Dir))
        return dic.get('ALIASES', dia)

if __name__ == '__main__':
    z = Table()
