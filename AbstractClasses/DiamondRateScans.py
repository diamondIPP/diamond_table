# --------------------------------------------------------
#       DIAMOND RATE SCANS
# created on June 24th 2016 by M. Reichmann
# --------------------------------------------------------

from ConfigParser import ConfigParser, NoOptionError
from argparse import ArgumentParser
from json import load
from collections import OrderedDict
from Utils import *


class DiaScans:
    def __init__(self, diamond):
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

    @staticmethod
    def load_diamond_parser():
        parser = ConfigParser()
        parser.read('AbstractClasses/DiamondAliases.cfg')
        return parser

    def load_diamond(self, dia):
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

    @staticmethod
    def load_all_runplans():
        f = open('AbstractClasses/run_plans.json', 'r')
        runplans = load(f)
        f.close()
        return runplans

    def load_runinfos(self):
        run_infos = {}
        for tc in self.RunPlans:
            file_path = 'AbstractClasses/run_log{tc}.json'.format(tc=tc)
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
            for rp, runs in sorted(self.RunPlans[tc]['rate_scan'].iteritems()):
                dias = [self.load_diamond(self.RunInfos[tc][str(runs[0])]['dia{0}'.format(ch)]) for ch in [1, 2]]
                print rp.ljust(5), '{0}-{1}'.format(str(runs[0]).zfill(3), str(runs[-1]).zfill(3)), dias[0].ljust(11), dias[1].ljust(11)

    # endregion

    def find_diamond_runplans(self):
        runplans = {}
        for tc, item in self.RunPlans.iteritems():
            runplans[tc] = {}
            for rp, runs in item['rate_scan'].iteritems():
                for ch in [1, 2]:
                    if all(self.DiamondName == self.load_diamond(self.RunInfos[tc][str(run)]['dia{0}'.format(ch)]) for run in runs):
                        bias = self.RunInfos[tc][str(runs[0])]['dia{0}hv'.format(ch)]
                        if all(self.RunInfos[tc][str(run)]['dia{0}hv'.format(ch)] == bias for run in runs):
                            if bias not in runplans[tc]:
                                runplans[tc][bias] = {}
                            runplans[tc][bias][rp] = ch
        return runplans

    def get_runs(self, rp, tc):
        return self.RunPlans[tc]['rate_scan'][rp]

    def get_diamonds(self):
        dias = []
        for tc, item in self.RunPlans.iteritems():
            for runs in item['rate_scan'].itervalues():
                for ch in [1, 2]:
                    dia0 = self.load_diamond(self.RunInfos[tc][str(runs[0])]['dia{0}'.format(ch)])
                    if all(dia0 == self.load_diamond(self.RunInfos[tc][str(run)]['dia{0}'.format(ch)]) for run in runs):
                        dias.append(dia0)
        return set(dias)


if __name__ == '__main__':
    main_parser = ArgumentParser()
    main_parser.add_argument('dia', nargs='?', default='S129')
    args = main_parser.parse_args()
    print_banner('STARTING DIAMOND RATE SCAN COLLECTION OF DIAMOND {0}'.format(args.dia))

    z = DiaScans(args.dia)
