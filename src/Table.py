# --------------------------------------------------------
#       TABLE BASE CLASS
# created on October 14th 2016 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from json import loads

from Utils import *
from DiamondRateScans import DiaScans
from shutil import copy
from os.path import dirname, realpath, join, basename
from progressbar import Bar, ETA, FileTransferSpeed, Percentage, ProgressBar
from ConfigParser import NoSectionError, NoOptionError
from json import load


def get_program_dir():
    return '/'.join(dirname(realpath(__file__)).split('/')[:-1])


class Table:

    def __init__(self):

        # program directory
        self.Dir = get_program_dir()

        # config
        self.ConfigFileName = 'conf.ini'
        self.Config = self.load_config()
        self.Irradiations = self.load_irradiations()

        # directories
        self.DataDir = join(self.Dir, self.Config.get('Files', 'data directory'))
        self.PickleDir = join(self.Dir, self.Config.get('Files', 'pickle directory'))
        self.TCDir = join(self.Dir, self.Config.get('Files', 'tc directory'))

        # info
        self.OtherCols = loads(self.Config.get("Other", "columns"))
        self.Exclude = loads(self.Config.get("General", "exclude"))
        self.DiaScans = DiaScans()
        self.TestCampaigns = self.load_test_campaigns()
        self.Diamonds = self.DiaScans.get_diamonds()

        # settings
        self.BkgCol = 'lightgrey'

        # progressbar
        self.Widgets = ['Progress: ', Percentage(), ' ', Bar(marker='>'), ' ', ETA(), ' ', FileTransferSpeed()]
        self.ProgressBar = None

    def load_test_campaigns(self):
        return [tc_to_str(tc) for tc in sorted(self.DiaScans.RunPlans.keys())]

    def create_dia_dir(self, diamond):
        path = join(self.DataDir, diamond)
        create_dir(path)
        create_dir(join(path, 'BeamTests'))
        self.create_default_info(path)

    def create_tc_dir(self, tc):
        create_dir(join(self.TCDir, tc))

    @staticmethod
    def create_default_info(path):
        file_name = join(path, 'info.ini')
        if not file_exists(file_name):
            with open(file_name, 'w') as f:
                f.write('[Manufacturer]\n')
                f.write('name = ?\n')
                f.write('url = ?\n')

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
        file_path = join(self.Dir, path, self.Config.get('Files', 'index php'))
        if not file_exists(file_path):
            copy(join(self.Dir, basename(file_path)), file_path)

    def translate_dia(self, diamond):
        self.DiaScans.translate_dia(diamond)

    def get_info(self, diamond, section, option, quiet=False):
        parser = ConfigParser()
        parser.read(join(self.DataDir, diamond, 'info.ini'))
        try:
            return parser.get(section, option)
        except NoOptionError:
            warning('option {o} not in {d} config'.format(o=option, d=diamond)) if option == 'type' else do_nothing()
            return ''
        except NoSectionError:
            warning('section {s} not in {d} config'.format(s=section, d=diamond)) if option == 'type' and not quiet else do_nothing()
            return ''

    def get_irradiation(self, campaign, diamond):
        try:
            return center_txt(make_irr_string(self.Irradiations[campaign][diamond]))
        except KeyError:
            warning('{} does not exist in irradiation file of {}!'.format(diamond, tc_to_str(campaign, short=False)))


if __name__ == '__main__':
    z = Table()
