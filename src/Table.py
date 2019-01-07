# --------------------------------------------------------
#       TABLE BASE CLASS
# created on October 14th 2016 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from json import loads

from Utils import *
from DiamondRateScans import DiaScans
from shutil import copy
from glob import glob
from numpy import mean
from os.path import dirname, realpath, join, sep, expanduser, basename
import pickle
from progressbar import Bar, ETA, FileTransferSpeed, Percentage, ProgressBar
from ConfigParser import NoSectionError, NoOptionError
from json import load


def get_program_dir():
    return '/'.join(dirname(realpath(__file__)).split('/')[:-1])


tc = None
dia = None


class Table:

    def __init__(self):

        # program directory
        self.Dir = get_program_dir()

        # config
        self.ConfigFileName = 'conf.ini'
        self.Config = self.load_config()
        self.Irradiations = self.load_irradiations()

        # directories
        self.DataPath = join(self.Dir, self.Config.get('General', 'data_directory'))
        self.AnaDir = expanduser(self.Config.get('General', 'analysis_dir'))
        self.AnaPickleDir = join(self.AnaDir, 'Configuration', 'Individual_Configs')
        self.PickleDir = join(self.Dir, 'Pickles')

        # info
        self.TestCampaigns = loads(self.Config.get("BeamTests", "dates"))
        self.OtherCols = loads(self.Config.get("Other", "columns"))
        self.Exclude = loads(self.Config.get("General", "exclude"))
        self.DiaScans = DiaScans()
        self.Diamonds = self.DiaScans.get_diamonds()

        # settings
        self.BkgCol = 'lightgrey'
        self.TestCampaign = None
        self.Diamond = None
        self.set_global_vars()

        # progressbar
        self.Widgets = ['Progress: ', Percentage(), ' ', Bar(marker='>'), ' ', ETA(), ' ', FileTransferSpeed()]
        self.ProgressBar = None

    def set_global_vars(self, campaign=None, diamond=None):
        global tc
        global dia
        tc = campaign if campaign is not None else tc
        dia = diamond if diamond is not None else dia
        self.select_diamond(dia)
        self.select_campaign(tc)

    def select_campaign(self, campaign):
        if campaign is not None and make_tc_str(campaign, long_=False) in self.TestCampaigns:
            self.TestCampaign = campaign

    def select_diamond(self, diamond):
        if diamond is not None and diamond in self.Diamonds:
            self.Diamond = diamond

    def start_pbar(self, n):
        self.ProgressBar = ProgressBar(widgets=self.Widgets, maxval=n)
        self.ProgressBar.start()

    def load_irradiations(self):
        f = open(join(self.Dir, 'data', self.Config.get('Files', 'irradiation')), 'r')
        irr = load(f)
        f.close()
        return irr

    def load_config(self):
        p = ConfigParser()
        p.read(join(self.Dir, self.ConfigFileName))
        return p

    def copy_index_php(self, path):
        file_path = join(self.Dir, path, self.Config.get('General', 'index_php'))
        # if file_exists(file_path) and len(glob(join(dirname(file_path), '*'))) <= 2:
        #     remove(file_path)
        if not file_exists(file_path) and len(glob(join(dirname(file_path), '*'))) > 1:
            copy(join(self.Dir, basename(file_path)), file_path)

    def calc_flux(self, info):
        if 'for1' not in info or info['for1'] == 0:
            if 'measuredflux' in info:
                return str('{0:5.0f}'.format(info['measuredflux'] * 2.48))
        pixel_size = 0.01 * 0.015
        area = [52 * 80 * pixel_size] * 2
        file_name = basename(info['maskfile']).strip('"')
        try:
            if file_name.lower() in ['none.msk', 'none', 'no mask']:
                raise UserWarning
            f = open(join(self.Dir, 'masks', file_name), 'r')
            data = {}
            for line in f:
                if line.startswith('#'):
                    continue
                if len(line) > 3:
                    line = line.split()
                    roc = int(line[1])
                    if roc not in data:
                        data[roc] = {}
                    data[roc][line[0]] = (int(line[2]), int(line[3]))
            f.close()
            try:
                area = [(dic['cornTop'][1] - dic['cornBot'][1] + 1) * (dic['cornTop'][0] - dic['cornBot'][0] + 1) * pixel_size for dic in data.itervalues()]
            except KeyError:
                area = [dic['col'][1] - dic['col'][0] + 1 * dic['row'][1] - dic['row'][0] + 1 * pixel_size for dic in data.itervalues()]
        except IOError:
            log_warning('Could not find mask file "{f}"! Not taking any mask!'.format(f=file_name))
        except UserWarning:
            pass
        flux = [info['for{0}'.format(i + 1)] / area[i] / 1000. for i in xrange(len(area))]
        return str('{0:5.0f}'.format(mean(flux)))

    @staticmethod
    def get_runtype(info):
        data = info['runtype']
        if 'signal' in data:
            return 'signal'
        elif 'pedes' in data:
            return 'pedestal'
        else:
            return data[:10]

    def get_pickle(self, run, campaign, ch, tag, form=''):
        ch = 0 if ch == 1 else 3
        pul_ped = 'Pedestal/{{tc}}_{{run}}_{{ch}}_a{n}2_fwhm_PulserBeamOn'.format(n='b' if campaign < '201707' else 'c')
        file_name_dic = {'PH': 'Ph_fit/{tc}_{run}_{ch}_10000_eventwise_b2',
                         'Pedestal': 'Pedestal/{tc}_{run}_{ch}_ab2_fwhm_all_cuts',
                         'Pulser': 'Pulser/HistoFit_{tc}_{run}_{ch}_ped_corr_BeamOn',
                         'PulserPed': pul_ped}
        path = '{dir}/Pickles/{f}.pickle'.format(dir=self.Dir, f=file_name_dic[tag])
        path = path.format(tc=campaign, run=run, ch=ch)
        if not file_exists(path):
            log_warning('did not find {p}'.format(p=path))
            return FitRes()
        f = open(path)
        try:
            fit_res = FitRes(pickle.load(f), form)
        except ImportError as err:
            print err
            return FitRes()
        f.close()
        return fit_res

    def translate_dia(self, diamond):
        self.DiaScans.translate_dia(diamond)

    def create_home_button(self, curr_path):
        n_dirs = len(curr_path.split(sep)) - len(self.Dir.split(sep))
        back = '../' * n_dirs
        return '</br> <button onclick="location.href={t}" type="button"> Home </button>'.format(t="'{p}'".format(p=join(back, 'index.html')))

    def get_info(self, diamond, section, option, quiet=False):
        info = ConfigParser()
        info.read(join(self.DataPath, diamond, 'info.ini'))
        try:
            return info.get(section, option)
        except NoOptionError:
            log_warning('option {o} not in {d} config'.format(o=option, d=diamond)) if option == 'type' else do_nothing()
            return ''
        except NoSectionError:
            log_warning('section {s} not in {d} config'.format(s=section, d=diamond)) if option == 'type' and not quiet else do_nothing()
            return ''

    def get_irradiation(self, campaign, diamond):
        return center_txt(make_irr_string(self.Irradiations[campaign][diamond]))


if __name__ == '__main__':
    z = Table()
