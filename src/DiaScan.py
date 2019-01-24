#!/usr/bin/env python
# --------------------------------------------------------
#       class to get information about a single diamond scan
# created on January 4th 2019 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from Utils import *
from time import time
from ConfigParser import NoOptionError
from collections import OrderedDict
from pickle import load as pload
from os.path import basename


class DiaScan:

    def __init__(self, test_campaign, run_plan, channel):

        self.Dir = dirname(dirname(realpath(__file__)))
        self.DataDir = join(self.Dir, 'data')

        self.TestCampaign = test_campaign
        self.RunPlan = run_plan
        self.RunPlanStr = make_rp_string(run_plan)
        self.Channel = channel

        self.Info = self.load_run_plan()
        self.Runs = self.Info['runs']
        self.FirstRun = self.Runs[0]
        self.Type = self.Info['type']
        self.RunInfos = self.load_run_infos()
        self.FirstInfo = self.RunInfos[str(self.FirstRun)]
        self.Diamond = self.load_diamond()
        self.DiaInfo = self.load_dia_info()
        self.DetectorType = self.DiaInfo.get(self.TestCampaign, 'type')

        self.Path = join('Diamonds', self.Diamond, 'BeamTests', tc_to_str(test_campaign), 'RunPlan{}'.format(make_rp_string(run_plan)))

        self.Bias = self.load_biases()
        self.Fluxes = self.load_fluxes()
        self.Attenuator = self.load_attenuator()
        self.PulserAttenuator = self.load_pulser_attenuator()
        self.StartTime = self.load_start_time()
        self.EndTime = self.load_end_time()
        self.Duration = self.calc_duration()
        self.DiaPosition = self.load_dia_position()
        self.PulserType = self.FirstInfo['pulser'] if 'pulser' in self.FirstInfo else ''
        self.Digitiser = self.load_digitiser()
        self.Events = self.get_events()

    def load_run_plan(self):
        with open(join(self.DataDir, 'run_plans.json')) as f:
            return load(f)[self.TestCampaign][self.RunPlan]

    def load_run_infos(self):
        with open(join(self.DataDir, 'run_log{}.json'.format(self.TestCampaign))) as f:
            return OrderedDict((key, item) for key, item in sorted(load(f).iteritems()) if int(key) in self.Runs)

    def load_diamond(self):
        parser = ConfigParser()
        parser.read(join(self.DataDir, 'DiamondAliases.cfg'))
        dia = self.RunInfos.values()[0]['dia{}'.format(self.Channel)]
        if dia in OrderedDict(parser.items('ALIASES')).values():
            return dia
        try:
            return parser.get('ALIASES', dia)
        except NoOptionError:
            warning('"{}" is not a known diamond')

    def load_biases(self):
        return sorted(list(set([int(dic['dia{}hv'.format(self.Channel)]) for dic in self.RunInfos.values()])), key=lambda x: abs(x))

    def load_attenuator(self, pulser=False):
        if 'pixel' in self.DetectorType.lower():
            return '-'
        if 'attenuators' in self.Info:
            key = '{}{}'.format('dia', self.Channel) if not pulser else '{}{}'.format('pulser', self.Channel if 'pulser1' in self.Info['attenuators'] else '')
            return self.Info['attenuators'][key]

    def load_pulser_attenuator(self):
        return self.load_attenuator(pulser=True)

    def load_start_time(self):
        return conv_time(self.FirstInfo['starttime0'], strg=False)

    def load_end_time(self):
        return conv_time(self.RunInfos.values()[-1]['endtime'], strg=False)

    def calc_duration(self):
        dur = self.EndTime - self.StartTime
        dur += timedelta(days=1) if dur < timedelta(0) else timedelta(0)
        return str(dur)

    def calc_run_duration(self, run):
        dur = conv_time(self.RunInfos[str(run)]['endtime'], strg=False) - conv_time(self.RunInfos[str(run)]['starttime0'], strg=False)
        dur += timedelta(days=1) if dur < timedelta(0) else timedelta(0)
        return str(dur)

    def get_run_bias(self, run):
        return make_bias_str(self.RunInfos[str(run)]['dia{}hv'.format(self.Channel)])

    def load_dia_position(self):
        keys = sorted([key for key in self.RunInfos.values()[0].iterkeys() if key.startswith('dia') and len(key) < 5])
        pos = ['Front', 'Middle', 'Back'] if len(keys) == 3 else ['Front', 'Back']
        return pos[keys.index('dia{ch}'.format(ch=self.Channel))]

    def get_runs_str(self):
        return '{:03d}-{:03d}'.format(self.FirstRun, self.Runs[-1])

    def get_flux_str(self):
        min_flux, max_flux = int(min(self.Fluxes.itervalues(), key=int)), int(max(self.Fluxes.itervalues(), key=int))
        if max_flux - min_flux < .5 * max_flux:
            return '~ {:1.0f}'.format(mean([int(flux) for flux in self.Fluxes.itervalues()]))
        return '{} ... {}'.format(min_flux, max_flux)

    def get_events(self):
        if all('events' in dic for dic in self.RunInfos.itervalues()):
            n = sum(dic['events'] for dic in self.RunInfos.itervalues())
            return '{:1.1f}M'.format(n / 1e6)
        return '?'

    def get_pickle(self, run, tag, form=''):
        dic = {'PH': join('Ph_fit', '{tc}_{run}_{ch}_10000_eventwise_b2'),
               'Ped': join('Pedestal', '{tc}_{run}_{ch}_ab2_fwhm_AllCuts'),
               'Pul': join('Pulser', 'HistoFit_{tc}_{run}_{ch}_ped_corr_BeamOn'),
               'Cur': join('Currents', '{tc}_{run}_{ch}'),
               'PulPed': join('Pedestal', '{tc}_{run}_{ch}_ac2_fwhm_PulserBeamOn')}
        path = join(self.Dir, 'Pickles', '{}.pickle'.format(dic[tag])).format(tc=self.TestCampaign, run=run, ch=self.Channel)
        if not file_exists(path):
            if 'pixel' not in self.DetectorType.lower():
                warning('did not find {p}'.format(p=path))
            return
        with open(path) as f:
            try:
                value = pload(f)
                if type(value) is Variable:
                    return value
                fit = FitRes(value, form)
                if fit.Parameter(0) is None:
                    warning('empty fitparameter pickle for: {}'.format(basename(path)))
                    return
                return fit
            except ImportError as err:
                warning(err)

    def get_pickle_mean(self, name, par, val=False):
        if self.TestCampaign < '201508':
            return center_txt('?')
        try:
            fits = [self.get_pickle(run, name) for run in self.Runs]
            signal, sigma = mean_sigma([make_ufloat((fit.Parameter(par), fit.ParError(par))) for fit in fits])
            return center_txt('{:2.2f} ({:.2f})'.format(signal, sigma)) if not val else make_ufloat((signal, sigma))
        except (TypeError, ValueError, ReferenceError, AttributeError):
            return center_txt('?')

    def get_noise(self, pulser=False):
        return self.get_pickle_mean('{}Ped'.format('Pul' if pulser else ''), 2)

    def get_signal(self, val=False):
        return self.get_pickle_mean('PH', 0, val)

    def get_pulser(self, val=False):
        return self.get_pickle_mean('Pul', 1, val)

    def get_corrected_signal(self, pulser=False):
        if self.TestCampaign < '201505':
            return center_txt('?')
        att_str = self.PulserAttenuator if pulser else self.Attenuator
        try:
            if str(att_str).lower() in ['none', '-']:
                return center_txt('-')
            elif att_str.lower() in ['?', 'unknown']:
                return center_txt('?')
            attenuations = att_str.split('+')
            db = sum(int(att.lower().split('db')[0]) for att in attenuations)
            att = 10 ** (make_ufloat((db, .01 * db)) / 20.)
            value = (self.get_pulser(val=True) if pulser else self.get_signal(val=True)) * att
            return center_txt('{:2.2f} ({:.2f})'.format(value.n, value.s))
        except TypeError:
            return center_txt('?')

    def get_corrected_pulser(self):
        return self.get_corrected_signal(pulser=True)

    def get_run_noise(self, run, pulser=False):
        value = self.get_pickle(run, 'PulPed' if pulser else 'Ped')
        return center_txt('{:.2f}'.format(value.Parameter(2))) if value is not None else ''

    def get_run_ped(self, run, pulser=False):
        value = self.get_pickle(run, 'PulPed' if pulser else 'Ped')
        return center_txt('{:.2f}'.format(value.Parameter(1))) if value is not None else ''

    def get_run_ph(self, run):
        value = make_ufloat(self.get_pickle(run, 'PH'), par=0)
        return center_txt('{:2.2f} ({:.2f})'.format(value.n, value.s)) if value is not None else ''

    def get_run_pul(self, run, sigma=False):
        value = make_ufloat(self.get_pickle(run, 'Pul'), par=2 if sigma else 1)
        return center_txt('{:2.2f}{}'.format(value.n, '' if sigma else ' ({:.2f})'.format(value.s))) if value is not None else ''

    def get_run_flux(self, run):
        return self.Fluxes[str(run)]

    def get_run_events(self, run):
        if 'events' in self.RunInfos[str(run)]:
            n = self.RunInfos[str(run)]['events']
            return '{:1.1f}M'.format(n / 1e6) if n > 1e6 else '{:1.0f}k'.format(n / 1e3)
        return '?'

    def get_run_current(self, run):
        value = make_ufloat(self.get_pickle(run, 'Cur'))
        return center_txt('{:2.1f} ({:.1f})'.format(value.n, value.s)) if value is not None else ''

    def load_digitiser(self):
        if 'pixel' in self.DetectorType.lower():
            return 'ROC'
        return self.Info['digitiser'] if 'digitiser' in self.Info else 'DRS4'

    def load_dia_info(self):
        parser = ConfigParser()
        parser.read(join(self.Dir, 'Diamonds', self.Diamond, 'info.ini'))
        if self.TestCampaign not in parser.sections():
            critical('The testcampaign {} was not added to {}\'s info.ini yet!'.format(self.TestCampaign, self.Diamond))
        return parser

    def load_fluxes(self):
        return {run: calc_flux(run_info) for run, run_info in self.RunInfos.iteritems()}


if __name__ == '__main__':
    t = time()
    z = DiaScan('201508', '01', '1')
    print time() - t
