#!/usr/bin/env python
# --------------------------------------------------------
#       module for whole info of the rate scans
# created on December 20th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from src.utils import *
from subprocess import getstatusoutput, check_output
from datetime import timedelta
import h5py
from glob import glob
from numpy import zeros
from os import environ


Config = Configuration(join(Dir, 'config', 'main.ini'))
ServerName = Config.get('Server', 'host')
ServerData = Config.get('Server', 'data')
ServerSoft = Config.get('Server', 'software')


def load_testcampaigns():
    words = [word for word in getstatusoutput(f'ssh -tY {ServerName} ls {join("/scratch2", "psi")}')[1].split()[:-1] if word.startswith('psi')]
    if not words:
        return [basename(word).replace('.json', '') for word in glob(join(Dir, 'data', 'run_logs', '*.json'))]
    return [tc for tc in sorted(tc.replace('psi_', '').replace('_', '').strip('\t') for tc in words) if tc not in Config.get_list('General', 'exclude tc')]


def get_years(test_campaigns):
    return ['< 2015'] + sorted(list(set([tc[:4] for tc in test_campaigns])))


class Data:

    # DATA
    Dir = join(Dir, 'data')
    environ['HDF5_USE_FILE_LOCKING'] = 'FALSE'
    File = h5py.File(join(Dir, 'data.hdf5'), 'a')

    TestCampaigns = load_testcampaigns()
    Years = get_years(TestCampaigns)
    RPDic = load_json(join(Dir, 'run_plans.json'))
    RunInfos = {tc: load_json(join(Dir, 'data', 'run_logs', f'{tc}.json')) for tc in TestCampaigns}
    RunPlans = None
    DUTs = None
    TCDUTs = None
    DUTRunPlans = {}

    Excluded = [dut.lower() for dut in Config.get_list('General', 'excluded')]
    DiaParser = Configuration(join(Dir, 'DiamondAliases.ini'))

    def __init__(self):

        self.PBar = PBar(counter=True)
        Data.DUTs = Data.load_duts()
        Data.RunPlans = {tc: [RunPlan(tag, tc) for tag in Data.RPDic[tc]] for tc in Data.TestCampaigns}
        Data.TCDUTs = {tc: list(set(dut.Name for rp in Data.RunPlans[tc] for dut in rp.DUTs)) for tc in Data.TestCampaigns}
        Data.DUTRunPlans = self.load_dut_runplans()

    def __getitem__(self, args):
        tc, ch, run = args
        return Data.File[str(tc)][str(ch)][int(run)]

    @update_pbar
    def load_dut_runplan(self, rp, tc, nr):
        return DUTRunPlan(rp.Tag, tc, str(nr))

    @pickle('data', 'runplans')
    def load_dut_runplans(self, _redo=False):
        info('loading run plans ...')
        self.PBar.start(sum(1 for rps in Data.RunPlans.values() for rp in rps for _ in rp.DUTNrs), counter=True)
        return {tc: [self.load_dut_runplan(rp, tc, nr) for rp in rps for nr in rp.DUTNrs] for tc, rps in Data.RunPlans.items()}

    def reload_dut_runplans(self):
        Data.DUTRunPlans = self.load_dut_runplans(_redo=True)

    @staticmethod
    def load_duts():
        d = {Data.translate(key): value for key, value in load_json(join(Data.Dir, 'dia_info.json')).items()}
        return {key: DUT(key, value) for key, value in d.items()}

    @staticmethod
    def find_tcs(dia):
        return [tc for tc, names in Data.TCDUTs.items() if dia in names]

    @staticmethod
    def find_runplans(dia, tc):
        return [rp.Tag for rp in Data.RunPlans[tc] if dia in rp.get_dut_names()]

    @staticmethod
    def find_runs(rps, tc):
        return list(set(run for rp in rps for run in Data.RPDic[tc][rp]['runs']))

    @staticmethod
    def find_max_duts(tc):
        keys = set([j for i in Data.RunInfos[tc].values() for j in i.keys()])
        return next(i for i in range(4, 0, -1) if f'dia{i}' in keys)

    # ----------------------------------------
    # region UPDATE
    @staticmethod
    def copy_runplans():
        server_file = join(ServerSoft, 'Runinfos', 'run_plans.json')
        return check_output(f'rsync -aP {ServerName}:{server_file} {Data.Dir}'.split())

    @staticmethod
    def copy_diamond_info():
        server_file = join(ServerSoft, 'Runinfos', 'dia_info.json')
        return check_output(f'rsync -aP {ServerName}:{server_file} {Data.Dir}'.split())

    @staticmethod
    def copy_diamond_aliases():
        server_file = join(ServerSoft, 'config', 'DiamondAliases.ini')
        return check_output(f'rsync -aP {ServerName}:{server_file} {Data.Dir}'.split())

    @update_pbar
    def copy_runlog(self, tc):
        server_file, local_file = join(f'{ServerData}', f'psi_{tc[:4]}_{tc[4:]}', 'run_log.json'), join(Data.Dir, 'run_logs', f'{tc}.json')
        return check_output(f'rsync -aP {ServerName}:{server_file} {local_file}'.split())

    def copy_runlogs(self):
        info('copying run logs ...')
        self.PBar.start(len(self.TestCampaigns))
        return [self.copy_runlog(tc) for tc in self.TestCampaigns]

    def update(self):
        self.copy_runplans()
        self.copy_diamond_info()
        self.copy_diamond_aliases()
        self.copy_runlogs()

    @staticmethod
    def fill_empty():
        for tc, dic in Data.RunInfos.items():
            if tc not in Data.File:
                Data.File.create_group(tc)
                info(f'created group {tc}')
            for i in range(1, Data.find_max_duts(tc) + 1):
                if not str(i) in Data.File[tc]:
                    Data.File[tc].create_dataset(str(i), data=zeros((int(max(dic, key=int)) + 1, 10, 2), 'd'))
                    info(f'created dataset {i} with shape {Data.File[tc][str(i)].shape} for {tc2str(tc, short=False)}')
    # endregion UPDATE
    # ----------------------------------------

    @staticmethod
    def translate(dut_name):
        return Data.DiaParser.get_value('ALIASES', dut_name.lower(), default=f'?{dut_name}')


class RunPlan:

    def __init__(self, tag, tc):

        self.Tag = tag
        self.TC = tc
        self.Name = f'Run Plan {tag.lstrip("0")}'
        self.ShortName = f'RP {tag.lstrip("0")}'
        self.TCString = tc2str(tc, short=False)

        rp = Data.RPDic[tc][tag]
        self.Type = rp['type'].replace('_', ' ')
        self.RunNumbers = rp['runs']
        self.Size = len(self.RunNumbers)
        log = Data.RunInfos[tc][str(self.RunNumbers[0])]
        self.DUTNrs = [i for i in range(1, 4) if f'dia{i}' in log]
        self.DUTs = [Data.DUTs[Data.translate(log[f'dia{i}'])] for i in self.DUTNrs]
        self.Digitiser = rp['digitiser'] if 'digitiser' in rp else 'PSI46' if 'pixel' in self.DUTs[0].get_type(tc) else 'DRS4'
        self.Amplifier = self.load_amp(rp)

    def load_amp(self, rp):
        if 'pixel' in self.DUTs[0].get_type(self.TC):
            return 'PSI46'
        if 'amplifiers' in rp:
            amps = [amp for amp in loads(rp['amplifiers']) if amp]
            return 'OSU2' if 'OSU2' in amps[0] else ', '.join(amps)
        return 'OSU1'

    def __repr__(self):
        return f'{self.Name} ({self.TCString})'

    @staticmethod
    def make_str(txt):
        return f'RP-{txt.lstrip("0").replace(".", "-")}'

    def get_runs_str(self):
        return f'{self.RunNumbers[0]:03d}-{self.RunNumbers[-1]:03d}'

    def get_bias_str(self, dut_nr):
        return make_bias_str([Data.RunInfos[self.TC][str(run)][f'dia{dut_nr}hv'] for run in self.RunNumbers])

    def get_ev_str(self):
        evts = [log['events'] for log in [Data.RunInfos[self.TC][str(run)] for run in self.RunNumbers] if 'events' in log]
        return make_ev_str(sum(evts)) if len(evts) == self.Size else '?'

    def is_main(self):
        return self.Tag.isdigit()

    def is_sub(self):
        return not self.is_main()

    def get_n_sub(self):
        return sum(rp.Tag.startswith(self.Tag.split('.')[0]) for rp in Data.RunPlans[self.TC])

    def get_dir(self, dut):
        return join(dut.RelDir, self.TC, RunPlan.make_str(self.Tag))

    def get_position(self, dut_nr):
        return 'front' if dut_nr == '1' else 'middle' if len(self.DUTNrs) == 3 and dut_nr == '2' else 'back'

    def get_dut_names(self):
        return [dut.Name for dut in self.DUTs]


class DUTRunPlan(RunPlan):

    def __init__(self, tag, tc, dut_nr):

        super().__init__(tag, tc)
        self.DUTNr = dut_nr

        self.DUT = Data.DUTs[Data.translate(Data.RunInfos[tc][str(self.RunNumbers[0])][f'dia{dut_nr}'])]
        self.Attenuator = self.load_attenuator()
        self.PulserAttenuator = self.load_attenuator(pulser=True)
        self.Runs = [Run(tc, run, dut_nr, self.DUT.Name) for run in self.RunNumbers]
        self.Irradiation = self.DUT.get_irradiation(tc)
        self.Position = self.get_position(self.DUTNr)
        self.StartTime = self.Runs[0].StartTime
        self.Duration = self.calc_duration()

        self.RelDir = self.get_dir(self.DUT)
        self.Dir = join(Dir, self.RelDir)

    def __repr__(self):
        return f'{super(DUTRunPlan, self).__repr__()}, {self.DUT}'

    def load_attenuator(self, pulser=False):
        rp, key = Data.RPDic[self.TC][self.Tag], f'{"pulser" if pulser else "dia"}{self.DUTNr}'
        return '-' if 'pixel' in self.DUT.get_type(self.TC) else rp['attenuators'][key] if 'attenuators' in rp and key in rp['attenuators'] else '?'

    def get_attenuators(self):
        return [self.Attenuator, self.PulserAttenuator]

    def get_values(self, i, err=True):
        v = Data.File[self.TC][str(self.DUTNr)][self.RunNumbers][:, i]
        return array([ufloat(*t) for t in v]) if err else v[:, 0]

    def get_mean(self, i, form='.1f'):
        v = self.get_values(i)
        return f'{mean_sigma(v)[0]:{form}}' if all(v) else '-'

    def get_flux_str(self):
        v = self.get_values(0, err=False)
        return f'{min(v):.0f} ... {max(v):.0f}' if all(v) else '-'

    def get_ev_str(self):
        v = self.get_values(9, err=False)
        return make_ev_str(sum(v)) if all(v) else '?'

    def calc_duration(self):
        return timedelta(seconds=sum(run.Duration.seconds for run in self.Runs))


class Run:

    def __init__(self, tc, number, dut_nr, dut_name=None):

        self.TC = tc
        self.DUTNr = str(dut_nr)
        self.Number = int(number)
        log = Data.RunInfos[tc][str(number)]
        self.DUTName = choose(dut_name, Data.translate(log[f'dia{dut_nr}']))
        self.Bias = make_bias_str(log[f'dia{dut_nr}hv'])
        self.StartTime = conv_time(log['starttime0'])
        self.Duration = Run.calc_duration(log)
        self.Comment = log['comments']
        self.Type = log['runtype'].replace('_', ' ')

        self.RelDir = join('content', 'diamonds', self.DUTName, tc, str(number))
        self.Dir = join(Dir, self.RelDir)

    @staticmethod
    def calc_duration(log):
        dur = conv_time(log['endtime'], strg=False) - conv_time(log['starttime0'], strg=False)
        return dur + timedelta(days=1 if dur.days < 0 else 0)

    def prep_data(self):
        """:returns: [flux, current, ph, ped, noise, pulserph, pulsersigma, pulserped, pulsernoise, events]"""
        data = Data.File[self.TC][self.DUTNr][self.Number]
        return [data[0][0], ufloat(*data[1]), ufloat(*data[2]), data[3][0], data[4][0], ufloat(*data[5]), data[6][0], data[7][0], data[8][0], data[9][0]]

    def get_flux_str(self):
        flux = Data.File[self.TC][self.DUTNr][self.Number][0][0]
        return f'{flux:.0f}' if flux else '?'

    def get_type(self):
        return Data.RunInfos[self.TC][str(self.Number)]['runtype'].replace('_', ' ')

    def get_fs11(self):
        return Data.RunInfos[self.TC][str(self.Number)]['fs11']

    def get_fs13(self):
        return Data.RunInfos[self.TC][str(self.Number)]['fs13']

    def get_ev_str(self):
        return make_ev_str(Data.RunInfos[self.TC][str(self.Number)]['events']) if 'events' in Data.RunInfos[self.TC][str(self.Number)] else '?'

    @staticmethod
    def get_dut_nrs(tc, run):
        return [i for i in range(1, 4) if f'dia{i}' in Data.RunInfos[tc][str(run)]]


class DUT:
    """ Class with all information about a single DUT. """
    def __init__(self, name, specs):

        # Info
        self.Name = name
        self.RelDir = join('content', 'diamonds', name)
        self.Dir = join(Dir, self.RelDir)

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
        return f'DUT {self.Name}'

    def __repr__(self):
        return self.__str__()

    def get_irradiation(self, tc):
        return self.Irradiation[tc] if tc in self.Irradiation else critical(f'Please make an irradiation entry in the dia_info.json for "{self.Name}" in {tc}')

    def get_irradiations(self):
        return ', '.join(irr2str(irr) for irr in sorted(set(self.Irradiation.values()), key=float))

    def get_type(self, tc):
        return self.Types[tc] if self.Types is not None and tc in self.Types else 'pad'

    def get_types(self):
        has_all = list(self.Types) == self.get_tcs()
        return ', '.join(list(set(self.Types.values())) + ([] if has_all else ['pad'])) if self.Types else 'pad'

    def get_tcs(self):
        return Data.find_tcs(self.Name)

    def get_board_number(self, tc):
        return self.BoardNumber[tc] if tc in self.BoardNumber else '?'

    def get_pulser(self, tc):
        return '' if 'pixel' in self.get_type(tc) else self.Pulser[tc] if tc in self.Pulser else 'extern'

    def load_spec(self, section, typ=None, lst=False, error=None, default=None):
        if section not in self.Specs or self.Specs[section] == 'None':
            return default
        spec = self.Specs[section] if typ is None else typ(self.Specs[section])
        return loads(spec) if lst and spec is not None else ufloat(spec, error) if error is not None and spec is not None else spec


if __name__ == '__main__':
    z = Data()
    # r = RunPlan('08.2', '201510')
    # r = Run('201510', '392', 1, z.RunInfos)
