# --------------------------------------------------------
#       DIAMOND RATE SCANS
# created on June 24th 2016 by M. Reichmann
# --------------------------------------------------------

from argparse import ArgumentParser
from ConfigParser import NoOptionError
from collections import OrderedDict
from Utils import *
from DiaScan import DiaScan


class DiaScans:
    def __init__(self, diamond=None):

        self.Dir = dirname(dirname(realpath(__file__)))
        self.Selection = []
        self.Name = None
        self.scale_factors = OrderedDict()

        self.Parser = self.load_diamond_parser()

        # information
        self.DiamondName = self.load_diamond(diamond)
        self.RunPlans = self.load_all_runplans()
        self.RunInfos = self.load_runinfos()

    # ==========================================================================
    # region INIT

    def load_diamond_parser(self):
        parser = ConfigParser()
        parser.read('{dir}/data/DiamondAliases.cfg'.format(dir=self.Dir))
        return parser

    def load_diamond(self, dia):
        if dia is None:
            return None
        try:
            return self.Parser.get('ALIASES', dia)
        except NoOptionError:
            if dia in [self.Parser.get('ALIASES', a) for a in self.Parser.options('ALIASES')]:
                return dia
            if dia != 'none':
                log_warning('{0} is not a known diamond name! Please choose one from \n{1}'.format(dia, self.Parser.options('ALIASES')))

    @staticmethod
    def load_tcs(tcs):
        all_tcs = ['201505', '201508', '201510', '201605']
        if tcs is None:
            return all_tcs
        tcs = [tcs] if type(tcs) is not list else tcs
        if not all(tc in all_tcs for tc in tcs):
            log_warning('You entered and invalid test campaign! Aborting!')
            exit()
        else:
            return tcs

    def load_all_runplans(self):
        with open(join(self.Dir, 'data', 'run_plans.json')) as f:
            return load(f)

    def load_runinfos(self):
        run_infos = {}
        for tc in self.RunPlans:
            file_path = '{dir}/data/run_log{tc}.json'.format(tc=tc, dir=self.Dir)
            f = open(file_path)
            run_infos[tc] = load(f)
            f.close()
        return run_infos

    # endregion

    # ==========================================================================
    # region SHOW

    def show_runplans(self):
        for tc in self.RunPlans:
            print_small_banner(tc)
            for rp, info in sorted(self.RunPlans[tc].iteritems()):
                runs = info['runs']
                dias = [self.load_diamond(self.RunInfos[tc][str(runs[0])]['dia{0}'.format(ch)]) for ch in [1, 2]]
                print rp.ljust(5), '{0}-{1}'.format(str(runs[0]).zfill(3), str(runs[-1]).zfill(3)), str(dias[0]).ljust(11), str(dias[1]).ljust(11)

    # endregion

    def find_diamond_runplans(self, dia=None):
        dia = self.DiamondName if dia is None else dia
        runplans = {}
        for tc, item in self.RunPlans.iteritems():
            runplans[tc] = {}
            for rp, info in item.iteritems():
                runs = info['runs']
                for ch in [1, 2]:
                    if all(dia == self.load_diamond(self.RunInfos[tc][str(run)]['dia{0}'.format(ch)]) for run in runs):
                        bias = self.RunInfos[tc][str(runs[0])]['dia{0}hv'.format(ch)]
                        if all(self.RunInfos[tc][str(run)]['dia{0}hv'.format(ch)] == bias for run in runs):
                            if bias not in runplans[tc]:
                                runplans[tc][bias] = {}
                            runplans[tc][bias][rp] = ch
        return runplans

    def find_dia_run_plans(self, dia):
        runplans = {}
        for tc, dic in self.RunPlans.iteritems():
            plans = []
            for rp, info in dic.iteritems():
                runs = info['runs']
                all_dias = set([self.load_diamond(self.RunInfos[tc][str(run)]['dia{0}'.format(ch)]) for run in info['runs'] for ch in [1, 2]])
                if dia not in all_dias or len(all_dias) > 2:
                    continue
                ch = next(ch for ch in [1, 2] if dia == self.load_diamond(self.RunInfos[tc][str(runs[0])]['dia{0}'.format(ch)]))
                plans.append((rp, ch))
            if plans:
                runplans[tc] = sorted(plans)
        return OrderedDict(sorted(runplans.iteritems()))

    def get_diamond_scans(self, dia, tc):
        scans = []
        for rp, dic in sorted(self.RunPlans[tc].iteritems()):
            rp_diamonds = self.get_rp_diamonds(tc, rp)
            if dia in rp_diamonds:
                scans.append(DiaScan(tc, rp, rp_diamonds.index(dia) + 1))
        return scans

    def get_runs(self, rp, tc):
        return self.RunPlans[tc][rp]['runs']

    def get_first_run(self, tc, rp):
        return str(self.get_runs(rp, tc)[0])

    def get_type(self, tc, rp):
        return self.RunPlans[tc][rp]['type']

    def get_biases(self, rp, tc, ch):
        runs = self.get_runs(rp, tc)
        return sorted(list(set([int(self.RunInfos[tc][str(run)]['dia{c}hv'.format(c=ch)]) for run in runs])), key=abs)

    def get_diamonds(self, single_tc=None):
        dias = []
        for tc, item in self.RunPlans.iteritems():
            if single_tc is not None:
                if tc != single_tc:
                    continue
            for info in item.itervalues():
                runs = info['runs']
                for ch in [1, 2]:
                    dia0 = self.load_diamond(self.RunInfos[tc][str(runs[0])]['dia{0}'.format(ch)])
                    if all(dia0 == self.load_diamond(self.RunInfos[tc][str(run)]['dia{0}'.format(ch)]) for run in runs) and dia0.lower() != 'none':
                        dias.append(dia0)
        return set(dias)

    def get_rp_diamonds(self, tc, rp):
        dias = [item for key, item in sorted(self.RunInfos[tc][self.get_first_run(tc, rp)].iteritems()) if key.startswith('dia') and len(key) < 6]
        return [self.translate_dia(dia) for dia in dias]

    def get_all_rp_diamonds(self, tc):
        return [self.get_rp_diamonds(tc, rp) for rp in self.RunPlans[tc]]

    def get_rp_biases(self, tc, rp):
        return [self.get_biases(rp, tc, ch) for ch in xrange(1, self.get_n_diamonds(tc, rp) + 1)]

    def get_n_diamonds(self, tc, rp):
        return sum(1 for key in self.RunInfos[tc][self.get_first_run(tc, rp)] if key.startswith('dia') and len(key) < 6)

    def translate_dia(self, dia):
        return self.Parser.get('ALIASES', dia.lower())

    def get_attenuators(self, tc, rp, ch, pulser=False):
        info = self.RunPlans[tc][rp]
        if 'attenuators' in info:
            key = 'pulser' if pulser else 'dia'
            return [info['attenuators']['{k}{ch}'.format(k=key, ch='' if key in info['attenuators'] else ch)]]
        else:
            return ['']

    def get_dia_position(self, tc, rp, ch):
        info = self.RunInfos[tc][self.get_first_run(tc, rp)]
        keys = sorted([key for key in info.iterkeys() if key.startswith('dia') and len(key) < 6])
        pos = ['Front', 'Middle', 'Back'] if len(keys) == 3 else ['Front', 'Back'] if len(keys) == 2 else range(len(keys))
        return pos[keys.index('dia{ch}'.format(ch=ch))]

    def calc_duration(self, tc, rp):
        runs = self.get_runs(rp, tc) if type(rp) in [str, unicode] else [rp]
        endinfo = self.RunInfos[tc][str(runs[-1])]
        startinfo = self.RunInfos[tc][str(runs[0])]
        dur = conv_time(endinfo['endtime'], strg=False) - conv_time(startinfo['starttime0'], strg=False)
        dur += timedelta(days=1) if dur < timedelta(0) else timedelta(0)
        return str(dur)


if __name__ == '__main__':
    main_parser = ArgumentParser()
    main_parser.add_argument('dia', nargs='?', default=None)
    args = main_parser.parse_args()
    print_banner('STARTING DIAMOND RATE SCAN COLLECTION OF DIAMOND {0}'.format(args.dia))

    z = DiaScans(args.dia)
