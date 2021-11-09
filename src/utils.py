# --------------------------------------------------------
#       UTILITY FUNCTIONS
# created on May 19th 2016 by M. Reichmann
# --------------------------------------------------------

from configparser import ConfigParser, NoOptionError, NoSectionError
from copy import deepcopy
from datetime import datetime, timedelta
from functools import wraps
from json import load, loads
from os import _exit, mkdir
from os.path import join, dirname, realpath, isdir, isfile
from pickle import load as pload, dump as pdump
from time import time

from numpy import array, sqrt, average
from progressbar import Bar, ETA, FileTransferSpeed, Percentage, ProgressBar, SimpleProgress, Widget
from termcolor import colored
from uncertainties import ufloat, ufloat_fromstr
from uncertainties.core import Variable, AffineScalarFunc

BaseDir = dirname(dirname(realpath(__file__)))


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


def add_spaces(s):
    return ''.join(f' {s[i]}' if i and (s[i].isupper() or s[i].isdigit()) and not s[i - 1].isdigit() and not s[i - 1].isupper() else s[i] for i in range(len(s)))


def remove_letters(s):
    return ''.join(filter(str.isdigit, s))


def load_json(path):
    if not isfile(path):
        return {}
    with open(path) as f:
        return load(f)


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


class Latex(object):

    @staticmethod
    def f(name, *args):
        return f'\\{name}' + ''.join(f'{{{i}}}' for i in args)

    @staticmethod
    def multirow(txt, n, pos='*'):
        return Latex.f('multirow', n, pos, txt)

    @staticmethod
    def makecell(*txt):
        return Latex.f('makecell', '\\\\'.join(txt))

    @staticmethod
    def bold(txt):
        return Latex.f('textbf', txt)

    @staticmethod
    def unit(txt, custom=False):
        return Latex.f('unit', '' if custom else "\\" + txt)

    @staticmethod
    def si(v, f='.1f', unit=''):
        return Latex.f('SI', f'{v:{f}}', f'\\{unit}' if unit else unit).replace('/', '')

    @staticmethod
    def si_range(v0, v1,  f='.0f', unit=''):
        return Latex.f('SIrange', f'{float(v0):{f}}', f'{float(v1):{f}}', f'\\{unit}' if unit else unit)

    @staticmethod
    def hline(word):
        return word + ' \\\\' + Latex.f('hline') if 'hline' not in word else word

    @staticmethod
    def table_row(*words, hline=False):
        row = f'  { " & ".join(words)}'
        return Latex.hline(row) if hline or 'hline' in row else f'{row} \\\\'

    @staticmethod
    def table(header, rows, hlines=False):
        cols = array(rows, str).T
        max_width = [len(max(col, key=len).replace(' \\\\\\hline', '')) for col in cols]  # noqa
        rows = array([[f'{word:<{w}}' for word in col] for col, w in zip(cols, max_width)]).T
        rows = '\n'.join(Latex.table_row(*row, hline=hlines) for row in rows)
        return f'{Latex.table_row(*header, hline=True)}\n{rows}'


def pickle(*rel_path, print_dur=False, use_args=False):
    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            file_name = ['_'.join(str(arg) for arg in args)] if use_args else ()
            pickle_path = f'{join(BaseDir, "data", "metadata", *rel_path, *file_name)}.pickle'
            redo = kwargs['_redo'] if '_redo' in kwargs else False
            if isfile(pickle_path) and not redo:
                with open(pickle_path, 'rb') as f:
                    return pload(f)
            prnt = print_dur and (kwargs['prnt'] if 'prnt' in kwargs else True)
            t = (args[0].info if len(args) and hasattr(args[0], 'info') else info)(f'{args[0].__class__.__name__ if args else ""}: {func.__name__.replace("_", " ")} ...', endl=False, prnt=prnt)
            value = func(*args, **kwargs)
            with open(pickle_path, 'wb') as f:
                pdump(value, f)
            (args[0].add_to_info if args and hasattr(args[0], 'add_to_info') else add_to_info)(t, prnt=prnt)
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
        if self.PBar and not self.PBar.finished:
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

    def get_value(self, section, option, dtype: type = str, default=None):
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

    def Parameter(self, arg):  # noqa
        if arg >= len(self.Pars):
            return ''
        return self.Pars[arg] if not self.Format else f'{self.Pars[arg]:f"{self.Format}}'

    def ParError(self, arg):  # noqa
        if arg >= len(self.Errors):
            return ''
        return self.Errors[arg] if not self.Format else f'{self.Errors[arg]:f"{self.Format}}'
# endregion CLASSES
# ----------------------------------------


def do_nothing():
    pass


PBAR = PBar()


def update_pbar(f):
    @wraps(f)
    def inner(*args, **kwargs):
        value = f(*args, **kwargs)
        PBAR.update()
        return value
    return inner
