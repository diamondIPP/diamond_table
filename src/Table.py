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
from os.path import dirname, realpath, join
import pickle
from progressbar import Bar, ETA, FileTransferSpeed, Percentage, ProgressBar


def get_program_dir():
    return '/'.join(dirname(realpath(__file__)).split('/')[:-1])


class Table:

    def __init__(self):

        # program directory
        self.Dir = get_program_dir()

        # config
        self.ConfigFileName = 'conf.ini'
        self.Config = self.load_config()

        # directories
        self.DataPath = '{dir}/{file}'.format(dir=self.Dir, file=self.Config.get('General', 'data_directory'))
        self.AnaDir = self.Config.get('General', 'analysis_dir')
        self.AnaPickleDir = '{ana}/Configuration/Individual_Configs'.format(ana=self.AnaDir)
        self.PickleDir = '{dir}/Pickles'.format(dir=self.Dir)

        # info
        self.TestCampaigns = loads(self.Config.get("BeamTests", "dates"))
        self.OtherCols = loads(self.Config.get("Other", "columns"))
        self.Exclude = loads(self.Config.get("General", "exclude"))
        self.DiaScans = DiaScans(self.Dir)
        self.Diamonds = self.DiaScans.get_diamonds()

        # settings
        self.BkgCol = 'lightgrey'

        # progressbar
        self.Widgets = ['Progress: ', Percentage(), ' ', Bar(marker='>'), ' ', ETA(), ' ', FileTransferSpeed()]
        self.ProgressBar = None

    def start_pbar(self, n):
        self.ProgressBar = ProgressBar(widgets=self.Widgets, maxval=n)
        self.ProgressBar.start()

    def load_config(self):
        p = ConfigParser()
        p.read(join(self.Dir, self.ConfigFileName))
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
        area = [52 * 80 * pixel_size] * 2
        try:
            f = open('{path}/masks/{mask}'.format(path=self.Dir, mask=info['maskfile']), 'r')
            data = []
            for line in f:
                if line.startswith('#'):
                    continue
                if len(line) > 3:
                    line = line.split()
                    data.append([int(line[2])] + [int(line[3])])
            f.close()
            area = [(data[1][0] - data[0][0]) * (data[1][1] - data[0][1]) * pixel_size, (data[3][0] - data[2][0]) * (data[3][1] - data[2][1]) * pixel_size]
        except IOError:
            log_warning('Could not find mask file {f}! Not taking any mask!'.format(f=info['maskfile']))
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

    def get_pickle(self, run, tc, ch, tag, form=''):
        ch = 0 if ch == 1 else 3
        file_name_dic = {'PH': 'Ph_fit/{tc}_{run}_{ch}_10000_eventwise_b2',
                         'Pedestal': 'Pedestal/{tc}_{run}_{ch}_ab2_fwhm_all_cuts',
                         'Pulser': 'Pulser/HistoFit_{tc}_{run}_{ch}_ped_corr_BeamOn',
                         'PulserPed': 'Pedestal/{tc}_{run}_{ch}_ab2_fwhm_PulserBeamOn'}
        path = '{dir}/Pickles/{f}.pickle'.format(dir=self.Dir, f=file_name_dic[tag])
        path = path.format(tc=tc, run=run, ch=ch)
        if not file_exists(path):
            log_warning('did not find {p}'.format(p=path))
            return FitRes()
        f = open(path)
        fit_res = FitRes(pickle.load(f), form)
        f.close()
        return fit_res

    def translate_dia(self, dia):
        return self.DiaScans.Parser.get('ALIASES', dia.lower())

    def translate_old_dia(self, dia):
        dic = load_parser('{dir}/data/OldDiamondAliases.cfg'.format(dir=self.Dir))
        return dic.get('ALIASES', dia)

if __name__ == '__main__':
    z = Table()
