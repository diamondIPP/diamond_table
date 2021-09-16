#!/usr/bin/env python
# --------------------------------------------------------
#       module for whole info of the rate scans
# created on December 20th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from src.utils import Configuration, BaseDir, join, load_json, info, warning, critical, datetime, loads, make_list, isfile, ufloat, pickle, update_pbar, PBAR, choose
from subprocess import getstatusoutput, check_output, CalledProcessError
from datetime import timedelta
import h5py
from glob import glob
from numpy import zeros, errstate, average, sum as npsum, isnan, array, log10, append
from os import environ
from src.html import conv_time, irr2str, basename
from hashlib import md5
from operator import itemgetter


# ----------------------------------------
# region CONFIG
def load_config():
    return Configuration(join(BaseDir, 'config', 'main.ini'))


def load_dut_parser():
    return Configuration(join(Dir, 'DiamondAliases.ini'))
# endregion CONFIG
# ----------------------------------------


# CONFIG
Dir = join(BaseDir, 'data')
Config = load_config()
DUTParser = load_dut_parser()

ServerName = Config.get('Server', 'host')
ServerData = Config.get('Server', 'data')
ServerSoft = Config.get('Server', 'software')
Excluded = [dut.lower() for dut in Config.get_list('General', 'excluded')]

# DATA FILE
environ['HDF5_USE_FILE_LOCKING'] = 'FALSE'
File = h5py.File(join(Dir, 'data.hdf5'), 'a')


# ----------------------------------------
# region CLASSES
class DUT:
    """ Class with all information about a single DUT. """
    def __init__(self, name, specs):

        # Info
        self.Name = name
        self.RelDir = join('content', 'diamonds', name)
        self.Dir = join(BaseDir, self.RelDir)

        # Specs
        self.Specs = specs
        self.Manufacturer = self.load_spec('manufacturer', default='?')
        self.Types = self.load_spec('type', default={})
        self.BoardNumber = self.load_spec('boardnumber')
        self.Irradiation = self.load_spec('irradiation', default={})
        self.Pulser = self.load_spec('pulser', default=[])
        self.Thickness = self.load_spec('thickness', typ=int, default='?')
        self.CCD = self.load_spec('CCD', typ=int)
        self.Size = self.load_spec('size', lst=True, default=[5, 5])
        self.PadSize = self.load_spec('metal', typ=float, error=.02, default=ufloat(3.5, .2))
        self.ActiveArea = self.PadSize ** 2 if self.PadSize is not None else None
        self.GuardRing = self.load_spec('guard ring', typ=float)
        self.Comment = self.load_spec('comment', default='').replace('\n', '<br>')

    def __str__(self):
        return self.Name

    def __repr__(self):
        return f'DUT {self.Name}'

    def __eq__(self, other):
        return self.Name == (other.Name if isinstance(other, DUT) else other)

    def get_names(self):
        return [f'{self.Name}_{t}' for t in self.load_spec('types')] if 'types' in self.Specs else [self.Name]

    def get_irradiation(self, tc):
        return self.Irradiation[tc] if tc in self.Irradiation else critical(f'Please make an irradiation entry in the dia_info.json for "{self.Name}" in {tc}')

    def get_irradiations(self):
        return ', '.join(irr2str(irr) for irr in sorted(set(self.Irradiation.values()), key=float))

    def get_type(self, tc):
        return self.Types[tc] if self.Types is not None and tc in self.Types else 'pad'

    def get_types(self):
        has_all = list(self.Types) == self.tcs
        return ', '.join(list(set(self.Types.values())) + ([] if has_all else ['pad'])) if self.Types else 'pad'

    @property
    def rp_tcs(self):
        return [tc.ID for tc in TestCampaigns.values() if self.Name in tc.runplan_duts]

    @property
    def tcs(self):
        tcs = [tc.ID for tc in TestCampaigns.values() if self.Name in tc.DUTs]
        return tcs if tcs else [tc for tc in self.Irradiation if tc in TestCampaigns]

    def get_board_number(self, tc):
        return self.BoardNumber[tc] if tc in self.BoardNumber else '?'

    def get_pulser(self, tc):
        return '' if 'pixel' in self.get_type(tc) else self.Pulser[tc] if tc in self.Pulser else 'extern'

    def load_spec(self, section, typ=None, lst=False, error=None, default=None):
        if section not in self.Specs or self.Specs[section] == 'None':
            return default
        spec = self.Specs[section] if typ is None else typ(self.Specs[section])
        return loads(spec) if lst and spec is not None else ufloat(spec, error) if error is not None and spec is not None else spec

    @staticmethod
    def translate(dut_name):
        words = dut_name.split('_')
        name, suffix = words[0], '_'.join(words[1:])
        return '_'.join([DUTParser.get_value('ALIASES', words[0].lower(), default=f'?{words[0]}')] + ([suffix] if suffix else []))

    @staticmethod
    def to_main(name):
        return name.split('_')[0]


class TestCampaign:

    BadTypes = ['shadow']

    def __init__(self, name):

        self.ID = str(name)
        self.Name = self.to_str(name)
        self.LongName = self.to_str(name, short=False)
        self.Location = 'PSI'
        self.LogFile = join(BaseDir, 'data', 'run_logs', f'{name}.json')
        self.Log = load_json(self.LogFile)
        self.NMaxDUTs = len(list(set([key for dic in self.Log.values() for key in dic if key.startswith('dia') and len(key) == 4])))

        self.fill_empty_data()
        data = self.data

        self.Runs = {int(nr): Run(name, nr, log, data) for nr, log in self.Log.items() if log['runtype'] not in TestCampaign.BadTypes}
        self.DUTs = self.load_duts()
        self.RunPlans = [RunPlan(tag, name) for tag in RPDic[name]]
        self.Hash = md5(data).hexdigest()

    def __repr__(self):
        return f'{self.__class__.__name__} {self.Name}, {len(self.Runs)} Runs'

    def __str__(self):
        return self.LongName

    def load_duts(self):
        return sorted(list(set(dut for run in self.Runs.values() for dut in run.DUTs if not dut.startswith('?') and dut not in ['unknown', 'None'])))

    def fill_empty_data(self):
        if self.ID not in File:
            File.create_group(self.ID)
            info(f'created group for {self}')
        for i in range(1, self.NMaxDUTs + 1):
            nruns = int(max(self.Log, key=int))
            if not str(i) in File[self.ID]:
                File[self.ID].create_dataset(str(i), data=zeros((nruns + 1, 10, 2), 'd'))
                info(f'created dataset {i} with shape {File[self.ID][str(i)].shape} for {self}')
            if File[self.ID][str(i)].shape[0] < nruns + 1:
                data = append(File[self.ID][str(i)], zeros((nruns - File[self.ID][str(i)].shape[0] + 1, 10, 2), 'd'), axis=0)
                del File[self.ID][str(i)]
                File[self.ID].create_dataset(str(i), data)
                info(f'extended dataset {i} with shape {File[self.ID][str(i)].shape} for {self}')

    @property
    def data(self):
        return array([File[self.ID][key] for key in File[self.ID]])

    @property
    def has_new_data(self):
        return md5(self.data).hexdigest() != self.Hash

    @property
    def runplan_runs(self):
        return sorted(list(set(self.Runs[nr] for rp in self.RunPlans for nr in rp.RunNumbers)))

    @property
    def runplan_duts(self):
        return list(set(dut.Name for rp in self.RunPlans for dut in rp.DUTs))

    @property
    def dut_types(self):
        types = [DUTs[DUT.to_main(dut)].get_type(self.ID) for dut in self.DUTs]
        return sorted(set('bcm\'' if t.startswith('pad') and t.endswith(')') else t for t in types))

    def get_dut_runs(self, dut):
        return [nr for nr, run in self.Runs.items() if dut in run.DUTs]

    def get_dut_runplans(self, dut):
        return [rp for rp in self.RunPlans if dut in rp.DUTs]

    @staticmethod
    def to_str(tc, short=True):
        return '-'.join([name if i else f'{datetime.strptime(name, "%Y%m"):{"%b%y" if short else "%B %Y"}}' for i, name in enumerate(tc.split('-'))])


class RunPlan:

    def __init__(self, tag, tc, data=None):

        # MAIN
        self.Tag = tag
        self.TC = tc
        self.Name = f'Run Plan {tag.lstrip("0")}'
        self.ShortName = f'RP {tag.lstrip("0")}'
        self.TCString = TestCampaign.to_str(tc, short=False)
        self.IsMain = self.Tag.isdigit()
        self.NSub = sum(rp.startswith(self.Tag.split('.')[0]) for rp in RPDic[self.TC])

        # LOG DATA
        rp = RPDic[tc][tag]
        self.RunNumbers = rp['runs']
        self.Size = len(self.RunNumbers)
        log = RunLogs[tc][str(self.RunNumbers[0])]
        self.DUTNrs = [i for i in range(1, 4) if f'dia{i}' in log]
        self.NDUTs = len(self.DUTNrs)
        self.DUTs = [DUTs[DUT.translate(log[f'dia{i}'])] for i in self.DUTNrs]
        self.StartTime = conv_time(log['starttime0'])
        self.Duration = self.calc_duration()

        # INFO
        self.Type = rp['type'].replace('_', ' ')
        self.DUTType = self.DUTs[0].get_type(self.TC)
        self.Attenuators = self.load_attenuators(log, rp)
        self.PulserAttenuators = self.load_attenuators(log, rp, pulser=True)
        self.Digitiser = rp['digitiser'] if 'digitiser' in rp else 'PSI46' if 'pixel' in self.DUTs[0].get_type(tc) else 'DRS4'
        self.Amplifier = self.load_amp(rp)
        self.RelDirs = [join(dut.RelDir, self.TC, str(self)) for dut in self.DUTs]
        self.Positions = ['front' if dut_nr == 1 else 'middle' if len(self.DUTNrs) == 3 and dut_nr == 2 else 'back' for dut_nr in self.DUTNrs]

        # STRINGS
        self.EventStr = self.get_total_events()
        self.RunStr = f'{self.RunNumbers[0]:03d}-{self.RunNumbers[-1]:03d}'
        self.BiasStr = [make_bias_str([RunLogs[self.TC][str(run)][f'dia{i}hv'] for run in self.RunNumbers]) for i in self.DUTNrs]
        self.DataStr = self.get_data_str(data)

    def load_amp(self, rp):
        if 'pixel' in self.DUTs[0].get_type(self.TC):
            return 'PSI46'
        if 'amplifiers' in rp:
            amps = [amp for amp in loads(rp['amplifiers']) if amp]
            return 'OSU2' if 'OSU2' in amps[0] else ', '.join(amps)
        return 'OSU1'

    def __repr__(self):
        return f'{self.Name} ({self.TCString})'

    def __str__(self):
        return f'RP-{self.Tag.lstrip("0").replace(".", "-")}'

    def get_total_events(self):
        evts = [log['events'] for log in [RunLogs[self.TC][str(run)] for run in self.RunNumbers] if 'events' in log]
        return make_ev_str(sum(evts)) if len(evts) == self.Size else '?'

    def get_irradiation(self, dut_nr):
        return self.DUTs[dut_nr].get_irradiation(self.TC)

    def get_position(self, dut_nr):
        return 'front' if dut_nr == '1' else 'middle' if len(self.DUTNrs) == 3 and dut_nr == '2' else 'back'

    def get_dut_names(self):
        return [dut.Name for dut in self.DUTs]

    def get_dut_nr(self, dut):
        return self.DUTs.index(dut)

    @property
    def is_complete(self):
        names = ['FluxProfile', 'NoiseFlux', 'PedestalFlux', 'PulseHeightFlux', 'PulserPH', 'PulserSigma']
        return all(isfile(join(BaseDir, d, f'{n}.root')) for n in names for d in self.RelDirs)

    def load_attenuators(self, log, rp, pulser=False):
        if 'pixel' in self.DUTs[0].get_type(self.TC):
            return ['-'] * self.NDUTs
        if 'att_dia1' in log:
            return [log[f'att_dia{i}'] for i in self.DUTNrs]
        return [rp['attenuators'][f'{"pulser" if pulser else "dia"}{i}'] if 'attenuators' in rp else '?' for i in self.DUTNrs]

    def get_attenuators(self, dut_nr):
        return [self.Attenuators[dut_nr], self.PulserAttenuators[dut_nr]]

    @staticmethod
    def flux2str(values):
        return f'{min(values):.0f} ... {max(values):.0f}' if all(values) else '-'

    def calc_duration(self):
        return sum([Run.calc_duration(RunLogs[self.TC][str(run)]) for run in self.RunNumbers], timedelta())

    def get_data_str(self, data=None):
        """:returns:
        [flux, cur, ph, ped, noise, pulph, pulsig, events]"""
        form = [.1, .1,  .1,    .1,    .1,     .1]
        d = array([File[self.TC][str(i)][self.RunNumbers] for i in self.DUTNrs]) if data is None else data[:self.NDUTs, self.RunNumbers]
        with errstate(divide='ignore', invalid='ignore'):  # catch zero divide errors
            values, events = average(d[:, :, 1:7, 0], axis=1, weights=1 / d[:, :, 1:7, 1]), npsum(d[:, :, -1, 0], axis=1)
        return [[RunPlan.flux2str(d[i, :, 0, 0])] + ['-' if isnan(v) else f'{v:{f}f}' for v, f in zip(values[i], form)] + [make_ev_str(events[i])] for i in range(self.NDUTs)]


class Run:
    def __init__(self, tc, number, log=None, data=None):
        # MAIN
        self.TC = tc
        self.Number = int(number)

        # LOG INFO
        log = RunLogs[tc][str(number)] if log is None else log
        self.StartTime = conv_time(log['starttime0'])
        self.Duration = Run.calc_duration(log)
        self.DUTNrs = [i for i in range(1, 4) if f'dia{i}' in log]
        self.NDUTs = len(self.DUTNrs)
        self.DUTs = [DUT.translate(log[f'dia{i}']) for i in self.DUTNrs]
        self.Biases = [log[f'dia{i}hv'] for i in self.DUTNrs]
        self.Comment = log['comments']
        self.Type = log['runtype'].replace('_', ' ')
        self.FS11 = log['fs11']
        self.FS13 = log['fs13']
        self.NEvents = log['events'] if 'events' in log else None
        self.RelDirs = [join('content', 'diamonds', dut, self.TC, str(self.Number)) for dut in self.DUTs]

        # Strings
        self.EventStr = make_ev_str(self.NEvents)
        self.FullData = self.get_data_str(data)

    def __repr__(self):
        return f'{self.__class__.__name__} {self.Number} ({self.TC})'

    def __lt__(self, other):
        return self.Number < (other.Number if isinstance(other, Run) else other)

    @staticmethod
    def calc_duration(log):
        dur = conv_time(log['endtime'], to_string=False) - conv_time(log['starttime0'], to_string=False)
        return dur + timedelta(days=1 if dur.days < 0 else 0)

    def get_ev_str(self):
        return make_ev_str(self.NEvents)

    def get_short_data(self, dut_nr):
        """:returns: [current, flux, ph, ped, events]"""
        return list(itemgetter(1, 0, 2, 3, 9)(self.FullData[dut_nr]))

    def get_data_str(self, data=None):
        """:returns:
               [flux, cur, ph, ped, noise, pulph, pulsig, pulped, pulnoi, events]"""
        form = [.0,    .1, .1,  .1,    .2,    .1,     .2,     .2,    .2]
        is_u = [0,      1,  1,   0,     0,     1,      0,      0,     0,       0]
        data = array([File[self.TC][str(i)][self.Number] for i in self.DUTNrs]) if data is None else data[range(self.NDUTs), self.Number]
        data = [[ufloat(*data[j][i]) if u else data[j][i][0] for i, u in enumerate(is_u)] for j in range(self.NDUTs)]
        return [[(make_ev_str(v) if i == 9 else f'{v:{form[i]}f}') if v else '-' for i, v in enumerate(row)] for row in data]
# endregion CLASSES
# ----------------------------------------


# ----------------------------------------
# region INIT
def find_testcampaigns():
    words = [word for word in getstatusoutput(f'ssh -tY {ServerName} ls {join("/scratch2", "psi")}')[1].split()[:-1] if word.startswith('psi')]
    if not words:
        return [basename(word).replace('.json', '') for word in glob(join(Dir, 'run_logs', '*.json'))]
    return [tc for tc in sorted(tc.replace('psi_', '').replace('_', '').strip('\t') for tc in words) if tc not in Config.get_list('General', 'exclude tc')]


def get_years(test_campaigns):
    return ['< 2015'] + sorted(list(set([tc[:4] for tc in test_campaigns])))


def load_runplans():
    return load_json(join(Dir, 'run_plans.json'))


def load_duts():
    d = {DUT.translate(key): value for key, value in load_json(join(Dir, 'dia_info.json')).items()}
    return {key: DUT(key, value) for key, value in d.items()}


def load_runlogs():
    return {tc: load_json(join(Dir, 'run_logs', f'{tc}.json')) for tc in TCStrings}


@update_pbar
@pickle(use_args=True)
def load_tc(tc, _redo=False):
    return TestCampaign(tc)


def load_tcs(redos=None):
    info('loading test campaigns ...')
    PBAR.start(len(TCStrings))
    redos = {tc: False for tc in TCStrings} if redos is None else redos
    return {tc: load_tc(tc, _redo=redo) for tc, redo in redos.items()}


def make_bias_str(v):
    v = make_list(v)
    v = [f'{float(bias):+.0f}' for bias in (v if len(set(v)) > 3 else set(v))]
    return v[0] if len(v) == 1 else ' &#8594; '.join(sorted(v, reverse=True, key=lambda x: abs(float(x)))) if len(v) < 4 else f'{v[0]} ... {v[-1]}'


def make_ev_str(v):
    if not v:
        return '?'
    n = int(log10(v) // 3)
    return f'{v / 10 ** (3 * n):.{1 if n > 1 else 0}f}{["", "k", "M"][n]}'
# endregion INIT
# ----------------------------------------


RPDic = load_runplans()
TCStrings = find_testcampaigns()  # init only strings
DUTs = load_duts()
RunLogs = load_runlogs()
TestCampaigns = load_tcs()


# ----------------------------------------
# region UPDATE
def update():
    try:
        reload_config()
        return update_logs()
    except CalledProcessError:
        return warning('cannot connect to server ... ')


def reload_config():
    global Config, DUTParser
    Config = load_config()
    copy_diamond_aliases()
    DUTParser = load_dut_parser()


def update_logs():
    global TCStrings, TestCampaigns, RPDic, RunLogs, DUTs
    TCStrings = find_testcampaigns()
    new_runplans = copy_runplans()
    RPDic = load_runplans()
    new_runlogs = copy_runlogs()
    RunLogs = load_runlogs()
    new_duts = copy_diamond_info()
    DUTs = load_duts()
    reload_tcs = {tc: new_duts or new_runplans or new_runlog or (TestCampaigns[tc].has_new_data if tc in TestCampaigns else False) for tc, new_runlog in new_runlogs.items()}
    if any(reload_tcs.values()):
        TestCampaigns = load_tcs(reload_tcs)
    return any(reload_tcs.values())


def copy_from_server(server_file, local_file=None):
    return 'to-chk' in str(check_output(f'rsync -aP {ServerName}:{server_file} {choose(local_file, Dir)}'.split()))


def copy_runplans():
    return copy_from_server(join(ServerSoft, 'Runinfos', 'run_plans.json'))


def copy_diamond_info():
    return copy_from_server(join(ServerSoft, 'Runinfos', 'dia_info.json'))


def copy_diamond_aliases():
    return copy_from_server(join(ServerSoft, 'config', 'DiamondAliases.ini'))


@update_pbar
def copy_runlog(tc):
    return copy_from_server(server_file=join(f'{ServerData}', f'psi_{tc[:4]}_{tc[4:]}', 'run_log.json'), local_file=join(Dir, 'run_logs', f'{tc}.json'))


def copy_runlogs():
    info('copying run logs ...')
    PBAR.start(len(TCStrings))
    return {tc: copy_runlog(tc) for tc in TCStrings}
# endregion UPDATE
# ----------------------------------------


def get_rp_tcs():
    return [tc.ID for tc in TestCampaigns.values() if tc.RunPlans]


if __name__ == '__main__':
    a = RunPlan('08.2', '201510')
    b = Run('201510', '392')
