# --------------------------------------------------------
#       DIAMOND RATE SCANS
# created on June 24th 2016 by M. Reichmann
# --------------------------------------------------------

from argparse import ArgumentParser
from ConfigParser import NoOptionError
from collections import OrderedDict
from Utils import *
from DiaScan import DiaScan
from datetime import timedelta


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
                warning('{0} is not a known diamond name! Please choose one from \n{1}'.format(dia, self.Parser.options('ALIASES')))

    @staticmethod
    def load_tcs(tcs):
        all_tcs = ['201505', '201508', '201510', '201605']
        if tcs is None:
            return all_tcs
        tcs = [tcs] if type(tcs) is not list else tcs
        if not all(tc in all_tcs for tc in tcs):
            warning('You entered and invalid test campaign! Aborting!')
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

    def get_diamond_tcs(self, dia):
        return sorted(list(set(tc for tc, dic1 in self.RunPlans.iteritems() for rp, dic2 in dic1.iteritems() if dia in self.get_rp_diamonds(tc, rp))))

    def get_dia_runplans(self, dia, tc):
        return sorted(rp for rp, dic in self.RunPlans[tc].iteritems() if dia in self.get_rp_diamonds(tc, rp))

    def get_tc_diamond_scans(self, dia, tc):
        scans = []
        for rp, dic in sorted(self.RunPlans[tc].iteritems()):
            rp_diamonds = self.get_rp_diamonds(tc, rp)
            if dia in rp_diamonds:
                scans.append(DiaScan(tc, rp, rp_diamonds.index(dia) + 1))
        return scans

    def get_diamond_scans(self, dia):
        dia_scans = [(tc, self.get_tc_diamond_scans(dia, tc)) for tc in sorted(self.RunPlans)]
        return OrderedDict([(tc, scans) for tc, scans in dia_scans if scans])

    def get_runs(self, rp, tc):
        return self.RunPlans[tc][rp]['runs']

    def get_first_run(self, tc, rp):
        return str(self.get_runs(rp, tc)[0])

    def get_type(self, tc, rp):
        return self.RunPlans[tc][rp]['type']

    def get_biases(self, rp, tc, ch):
        runs = self.get_runs(rp, tc)
        return sorted(list(set([int(self.RunInfos[tc][str(run)]['dia{c}hv'.format(c=ch)]) for run in runs])), key=lambda x: abs(x))

    def get_diamonds(self, single_tc=None):
        dias = []
        for tc, item in self.RunPlans.iteritems():
            if single_tc is not None:
                if tc != single_tc:
                    continue
            for rp, dic in item.iteritems():
                runs = dic['runs']
                for ch in xrange(1, self.get_n_diamonds(tc, rp) + 1):
                    dia0 = self.load_diamond(self.RunInfos[tc][str(runs[0])]['dia{0}'.format(ch)])
                    if all(dia0 == self.load_diamond(self.RunInfos[tc][str(run)]['dia{0}'.format(ch)]) for run in runs) and dia0.lower() != 'none':
                        dias.append(dia0)
        return sorted(list(set(dias)))

    def get_tc_diamonds(self, tc):
        return set(dia for lst in self.get_all_rp_diamonds(tc) for dia in lst)

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
        rp_info = self.RunPlans[tc][rp]
        if 'attenuators' in rp_info:
            key = 'pulser' if pulser else 'dia'
            return [rp_info['attenuators']['{k}{ch}'.format(k=key, ch='' if key in rp_info['attenuators'] else ch)]]
        else:
            return ['']

    def get_dia_position(self, tc, rp, ch):
        run_info = self.RunInfos[tc][self.get_first_run(tc, rp)]
        keys = sorted([key for key in run_info.iterkeys() if key.startswith('dia') and len(key) < 6])
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
