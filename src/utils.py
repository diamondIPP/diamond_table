# --------------------------------------------------------
#       UTILITY FUNCTIONS
# created on May 19th 2016 by M. Reichmann
# --------------------------------------------------------

from datetime import datetime, timedelta
from termcolor import colored
from configparser import ConfigParser, NoOptionError, NoSectionError
from progressbar import Bar, ETA, FileTransferSpeed, Percentage, ProgressBar, SimpleProgress, Widget
from json import load, loads
from os.path import join, dirname, realpath, isdir, isfile
from os import _exit, mkdir
from re import sub
from uncertainties import ufloat, ufloat_fromstr
from uncertainties.core import Variable, AffineScalarFunc
from numpy import array, sqrt, average, log10
from time import time
from functools import wraps
from copy import deepcopy
from pickle import load as pload, dump as pdump


Dir = dirname(dirname(realpath(__file__)))


def get_t_str():
    return datetime.now().strftime('%H:%M:%S')


def warning(msg, prnt=True):
    if prnt:
        print(prepare_msg(msg, 'WARNING', 'yellow'))


def critical(msg):
    print(prepare_msg(msg, 'CRITICAL', 'red'))
    _exit(1)


def prepare_msg(msg, header, color=None, attrs=None, blank_lines=0):
    return '{}\r{} {} --> {}'.format('\n' * blank_lines, colored(header, color, attrs=choose(make_list(attrs), None, attrs)), get_t_str(), msg)


def info(msg, endl=True, blank_lines=0, prnt=True):
    if prnt:
        print(prepare_msg(msg, 'INFO', 'cyan', 'dark', blank_lines), flush=True, end='\n' if endl else ' ')
    return time()


def add_to_info(t, msg='Done', prnt=True):
    if prnt:
        print('{m} ({t:2.2f} s)'.format(m=msg, t=time() - t))


def print_banner(msg, symbol='~', new_lines=1, color=None):
    msg = '{} |'.format(msg)
    print(colored('{n}{delim}\n{msg}\n{delim}{n}'.format(delim=len(str(msg)) * symbol, msg=msg, n='\n' * new_lines), color))


def print_small_banner(msg, symbol='-', color=None):
    print(colored('\n{delim}\n{msg}\n'.format(delim=len(str(msg)) * symbol, msg=msg), color))


def choose(v, default, decider='None', *args, **kwargs):
    use_default = decider is None if decider != 'None' else v is None
    if callable(default) and use_default:
        default = default(*args, **kwargs)
    return default if use_default else v(*args, **kwargs) if callable(v) else v


def make_list(value):
    return array([value], dtype=object).flatten()


def get_elapsed_time(start, hrs=False):
    t = str(timedelta(seconds=round(time() - start, 0 if hrs else 2)))
    return t if hrs else t[2:-4]


def create_dir(*path):
    path = join(*path)
    if not isdir(path):
        info(f'creating directory: {path}')
        mkdir(path)
    return path


def prep_kw(dic, **default):
    d = deepcopy(dic)
    for kw, value in default.items():
        if kw not in d:
            d[kw] = value
    return d


def add_spaces(txt):
    return ''.join(f' {txt[i]}' if i and (txt[i].isupper() or txt[i].isdigit()) and not txt[i - 1].isdigit() and not txt[i - 1].isupper() else txt[i] for i in range(len(txt)))


def tc2str(tc, short=True):
    tc_str = str(tc).split('-')[0]
    sub_str = '-{}'.format(tc.split('-')[-1]) if '-' in str(tc) else ''
    return '{tc}{s}'.format(tc=datetime.strptime(tc_str, '%Y%m').strftime('%b%y' if short else '%B %Y'), s=sub_str)


def make_bias_str(v):
    v = make_list(v)
    v = [f'{float(bias):+.0f}' for bias in (v if len(set(v)) > 3 else set(v))]
    return v[0] if len(v) == 1 else ' &#8594; '.join(sorted(v, reverse=True, key=lambda x: abs(float(x)))) if len(v) < 4 else f'{v[0]} ... {v[-1]}'


def make_ev_str(v):
    if not v:
        return '?'
    n = int(log10(v) // 3)
    return f'{v / 10 ** (3 * n):.{1 if n > 1 else 0}f}{["", "k", "M"][n]}'


def make_runs_str(runs):
    return '{b:03d}-{e:03d}'.format(b=runs[0], e=runs[-1])


def remove_letters(string):
    return sub('\D', '', string)


def load_parser(path):
    p = ConfigParser()
    p.read(path)
    return p


def load_json(path):
    if isfile(path):
        f = open(path)
        j = load(f)
        f.close()
        return j
    else:
        return {}


def mean_sigma(values, weights=None):
    """ Return the weighted average and standard deviation. values, weights -- Numpy ndarrays with the same shape. """
    if len(values) == 1:
        v = make_ufloat(values[0])
        return v.n, v.s
    weights = [1] * len(values) if weights is None else weights
    if type(values[0]) is Variable:
        weights = [1 / v.s for v in values]
        values = array([v.n for v in values], 'd')
    if all(weight == 0 for weight in weights):
        return [0, 0]
    avrg = average(values, weights=weights)
    variance = average((values - avrg) ** 2, weights=weights)  # Fast and numerically precise
    return avrg, sqrt(variance)


def is_ufloat(value):
    return type(value) in [Variable, AffineScalarFunc]


def make_ufloat(n, s=0):
    if isiter(n):
        return array([ufloat(*v) for v in array([n, s]).T])
    return n if is_ufloat(n) else ufloat(n, s)


def isiter(v):
    try:
        iter(v)
        return False if type(v) is str else True
    except TypeError:
        return False


def pickle(*rel_path, print_dur=False):
    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            pickle_path = f'{join(Dir, *rel_path)}.pickle'
            redo = kwargs['_redo'] if '_redo' in kwargs else False
            if isfile(pickle_path) and not redo:
                with open(pickle_path, 'rb') as f:
                    return pload(f)
            prnt = print_dur and (kwargs['prnt'] if 'prnt' in kwargs else True)
            t = (args[0].info if hasattr(args[0], 'info') else info)(f'{args[0].__class__.__name__}: {func.__name__.replace("_", " ")} ...', endl=False, prnt=prnt)
            value = func(*args, **kwargs)
            with open(pickle_path, 'wb') as f:
                pdump(value, f)
            (args[0].add_to_info if hasattr(args[0], 'add_to_info') else add_to_info)(t, prnt=prnt)
            return value
        return wrapper
    return inner


def quiet(func):
    @wraps(func)
    def wrapper(cls, *args, **kwargs):
        old = cls.Verbose
        cls.set_verbose(False)
        value = func(cls, *args, **kwargs)
        cls.set_verbose(old)
        return value
    return wrapper


# ----------------------------------------
# region CLASSES
def update_pbar(func):
    @wraps(func)
    def my_func(*args, **kwargs):
        value = func(*args, **kwargs)
        if args[0].PBar is not None and args[0].PBar.PBar is not None and not args[0].PBar.is_finished():
            args[0].PBar.update()
        return value
    return my_func


class PBar(object):
    def __init__(self, start=None, counter=False, t=None):
        self.PBar = None
        self.Widgets = self.init_widgets(counter, t)
        self.Step = 0
        self.N = 0
        self.start(start)

    def __reduce__(self):
        return self.__class__, (None, False, None), (self.Widgets, self.Step, self.N)

    def __setstate__(self, state):
        self.Widgets, self.Step, self.N = state
        if self.N:
            self.PBar = ProgressBar(widgets=self.Widgets, maxval=self.N).start()
            self.update(self.Step) if self.Step > 0 else do_nothing()

    @staticmethod
    def init_widgets(counter, t):
        return ['Progress: ', SimpleProgress('/') if counter else Percentage(), ' ', Bar(marker='>'), ' ', ETA(), ' ', FileTransferSpeed() if t is None else EventSpeed(t)]

    def start(self, n, counter=None, t=None):
        if n is not None:
            self.Step = 0
            self.PBar = ProgressBar(widgets=self.Widgets if t is None and counter is None else self.init_widgets(counter, t), maxval=n).start()
            self.N = n

    def update(self, i=None):
        i = self.Step if i is None else i
        if i >= self.PBar.maxval:
            return
        self.PBar.update(i + 1)
        self.Step += 1
        if i == self.PBar.maxval - 1:
            self.finish()

    def finish(self):
        self.PBar.finish()

    def is_finished(self):
        return self.PBar.currval == self.N


class EventSpeed(Widget):
    """Widget for showing the event speed (useful for slow updates)."""

    def __init__(self, t='s'):
        self.unit = t
        self.factor = {'s': 1, 'min': 60, 'h': 60 * 60}[t]

    def update(self, pbar):
        value = 0
        if pbar.seconds_elapsed > 2e-6 and pbar.currval > 2e-6:
            value = pbar.currval / pbar.seconds_elapsed * self.factor
        return f'{value:4.1f} E/{self.unit}'


class Configuration(ConfigParser):

    def __init__(self, file_name, **kwargs):
        super(Configuration, self).__init__(**kwargs)
        self.FileName = file_name
        self.read(file_name) if type(file_name) is not list else self.read_file(file_name)

    def get_value(self, section, option, dtype=str, default=None):
        dtype = type(default) if default is not None else dtype
        try:
            if dtype is bool:
                return self.getboolean(section, option)
            v = self.get(section, option)
            return loads(v) if dtype == list or '[' in v and dtype is not str else dtype(v)
        except (NoOptionError, NoSectionError):
            return default

    def get_values(self, section):
        return [j for i, j in self.items(section)]

    def get_list(self, section, option, default=None):
        return self.get_value(section, option, list, choose(default, []))

    def get_ufloat(self, section, option, default=None):
        return ufloat_fromstr(self.get_value(section, option, default=default))

    def show(self):
        for key, section in self.items():
            print(colored('[{}]'.format(key), 'yellow'))
            for option in section:
                print('{} = {}'.format(option, self.get(key, option)))
            print()


class FitRes:
    def __init__(self, fit_obj=None, form=''):
        self.Pars = self.load_pars(fit_obj)
        self.Errors = self.load_errors(fit_obj)
        self.Format = form

    @staticmethod
    def load_pars(fit_obj):
        if fit_obj is None:
            return [None]
        if hasattr(fit_obj, 'Pars'):
            return fit_obj.Pars
        else:
            return list(fit_obj.Parameters())

    @staticmethod
    def load_errors(fit_obj):
        if fit_obj is None:
            return [None]
        elif hasattr(fit_obj, 'Errors'):
            return fit_obj.Errors
        else:
            return list(fit_obj.Errors())

    def Parameter(self, arg):
        if arg >= len(self.Pars):
            return ''
        return self.Pars[arg] if not self.Format else f'{self.Pars[arg]:f"{self.Format}}'

    def ParError(self, arg):
        if arg >= len(self.Errors):
            return ''
        return self.Errors[arg] if not self.Format else f'{self.Errors[arg]:f"{self.Format}}'
# endregion CLASSES
# ----------------------------------------


def do_nothing():
    pass
