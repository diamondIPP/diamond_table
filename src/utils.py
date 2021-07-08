# --------------------------------------------------------
#       UTILITY FUNCTIONS
# created on May 19th 2016 by M. Reichmann
# --------------------------------------------------------

from datetime import datetime
from termcolor import colored
from configparser import ConfigParser, NoOptionError, NoSectionError
from progressbar import Bar, ETA, FileTransferSpeed, Percentage, ProgressBar, SimpleProgress, Widget
from json import load, loads
from os.path import join, dirname, realpath, basename, isdir, isfile
from os import _exit, mkdir, listdir
from re import sub
from uncertainties import ufloat, ufloat_fromstr
from uncertainties.core import Variable
from numpy import array, sqrt, average, mean, log10
from pytz import timezone, utc
from time import time
from functools import wraps
from copy import deepcopy
from pickle import load as pload, dump as pdump


Dir = dirname(dirname(realpath(__file__)))


# ==============================================
# UTILITY FUNCTIONS
# ==============================================
def get_base_dir():
    return dirname(dirname(realpath(__file__)))


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


def untitle(string):
    s = ''
    for word in string.split(' '):
        if word:
            s += word[0].lower() + word[1:] + ' '
    return s.strip(' ')


def round_down_to(num, val):
    return int(num) / val * val


def round_up_to(num, val):
    return int(num) / val * val + val


def list_dirs(path):
    return [d for d in listdir(path) if isdir(join(path, d))]


def make_link(target, name='Results', new_tab=False, path='', use_name=True, center=False):
    tab = ' target="_blank"' if new_tab else ''
    name = center_txt(name) if center else name
    if file_exists(join(path, target.strip('./'))) or not path:
        return '<a href={tar}{tab}>{nam}</a>'.format(tar=target, nam=name, tab=tab)
    return name if use_name else ''


def make_lines(n):
    return '<br/>' * n


def get_elapsed_time(start):
    t = datetime.fromtimestamp(time() - start)
    return '{}.{:02.0f}'.format(t.strftime('%M:%S'), t.microsecond / 10000)


def make_abs_link(target, name, active=False, center=False, new_tab=False, use_name=True, colour='red', warn=True):
    active = 'class="active" ' if active else ''
    new_tab = ' target="_blank"' if new_tab else ''
    name = center_txt(name) if center else name
    style = ' style="color:{}"'.format(colour) if colour else ''
    if file_exists(join(Dir, target)) or 'http' in target:
        return '<a {act}href={tar}{tab}{s}>{name}</a>'.format(act=active, tar=abs_html_path(target), tab=new_tab, name=name, s=style)
    warning('The file {} does not exist!'.format(target), prnt=warn)
    return name if use_name else ''


def make_figure(path, name='', width=None, height=None):
    width = ' width="{}"'.format(width) if width is not None else ''
    height = ' height="{}"'.format(height) if height is not None else ''
    return '<img src="{path}" alt="{name}"{w}{h}>'.format(path=abs_html_path(path), name=name, w=width, h=height)


def embed_google_pdf(path, width=None, height=None):
    width = ' width="{}"'.format(width) if width is not None else ''
    height = ' height="{}"'.format(height) if height is not None else ''
    return '<embed src="https://drive.google.com/viewerng/viewer?embedded=true&url={}"{}{}>\n'.format(path, width, height)


def embed_pdf(path, width=400, height=390, zoom=52):
    width = ' width="{}"'.format(width) if width is not None else ''
    height = ' height="{}"'.format(height) if height is not None else ''
    error = 'pdf {} does not exist'.format(basename(path))
    zoom = 'view=FitH' if zoom is None else 'zoom={}'.format(zoom)
    html = '  <a href="{}" target="_blank" class="pdf">\n'.format(path)
    html += '    <object {h}{w} type="application/pdf" data="{p}?#{z}&scrollbar=0&toolbar=0&navpanes=0&statusbar=0"><p>{e}</p></object>\n'.format(h=height, w=width, p=path, e=error, z=zoom)
    return html + '  </a>\n'


def embed_png(path, width=400, height=390):
    width = ' width="{}"'.format(width) if width is not None else ''
    height = ' height="{}"'.format(height) if height is not None else ''
    return '  <a href="{0}.pdf" target="_blank">\n    <img {1} {2} src="{0}.png"\n  </a>\n'.format(path, width, height)


def indent(txt, n_spaces=2):
    lines = txt.split('\n')
    return '\n'.join('{}{}'.format(n_spaces * ' ', line) for line in lines)


def bold(txt):
    return '<b>{}</b>'.format(txt)


def head(txt, size=1):
    return '<h{0}>{1}</h{0}>\n'.format(size, txt)


def folder_exists(path):
    return isdir(path)


def file_exists(path):
    return isfile(path)


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


def write_html_header(f, name, bkg=None):
    f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n')
    f.write('<html>\n<head>\n<meta content="text/html; charset=ISO-8859-1" http-equiv="content-type">\n')
    f.write('<link rel="icon" href="http://pngimg.com/uploads/diamond/diamond_PNG6684.png">\n')
    f.write('<title> {tit} </title>\n'.format(tit=name))
    f.write('</head>\n<body{bkg}>\n\n\n'.format(bkg='' if bkg is None else ' bgcolor=' + bkg))
    f.write('<h1>{tit}</h1>\n'.format(tit=name))


def add_spaces(txt):
    return ''.join(f' {txt[i]}' if i and (txt[i].isupper() or txt[i].isdigit()) and not txt[i - 1].isdigit() and not txt[i - 1].isupper() else txt[i] for i in range(len(txt)))


def make_rp_string(string, directory=False):
    return '{}{}'.format('RunPlan' if directory else '', string[1:] if string[0] == '0' else string)


def make_runplan_string(nr):
    nr = str(nr)
    return nr.zfill(2) if len(nr) <= 2 else nr.zfill(4)


def str_to_tc(tc, short=True):
    tc_str = tc.split('-')[0]
    sub_str = '-{}'.format(tc.split('-')[-1]) if '-' in str(tc) else ''
    return '{tc}{s}'.format(tc=datetime.strptime(tc_str, '%b%y').strftime('%Y%m' if short else '%B %Y'), s=sub_str)


def tc2str(tc, short=True):
    tc_str = str(tc).split('-')[0]
    sub_str = '-{}'.format(tc.split('-')[-1]) if '-' in str(tc) else ''
    return '{tc}{s}'.format(tc=datetime.strptime(tc_str, '%Y%m').strftime('%b%y' if short else '%B %Y'), s=sub_str)


def make_bias_str(v):
    v = [f'{float(bias):+.0f}' for bias in set(make_list(v))]
    return v[0] if len(v) == 1 else ' &#8594; '.join(sorted(v, reverse=True, key=lambda x: abs(float(x)))) if len(v) < 4 else f'{v[0]} ... {v[-1]}'


def irr2str(val, unit=False):
    return val if val == '?' else 'nonirr' if not val or val == '0' else '{} &middot 10<sup>{}</sup>{}'.format(*val.split('e'), f' n/cm{sup(2)}' if unit else '')


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
    if file_exists(path):
        f = open(path)
        j = load(f)
        f.close()
        return j
    else:
        return {}


def conv_time(time_str, strg=True):
    t = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=utc).astimezone(timezone('Europe/Zurich'))
    return t.strftime('%b %d{} %H:%M:%S').format(nth(t.day)) if strg else t


def t_to_str(time):
    return time.strftime('%b %d{} %H:%M:%S').format(nth(time.day))


def dig_str(value, form='5.1f'):
    return ('{0:' + form + '}').format(value) if value is not None else ''


def nth(d):
    nth.ext = ['th', 'st', 'nd', 'rd'] + ['th'] * 16
    return sup(nth.ext[int(d) % 20])


def sup(txt):
    return '<sup>{0}</sup>'.format(txt)


def center_txt(txt):
    return '<div align="center">{0}</div>'.format(txt)


def right_txt(txt):
    return '<div align="right">{0}</div>'.format(txt)


def add_spacings(txt, n=1):
    return '{s}{txt}{s}'.format(txt=txt, s=' &nbsp ' * n)


def add_bkg(table, color='black'):
    lines = table.split('\n')
    for i, line in enumerate(lines):
        if ('&n' in line or '"></TD>' in line) and len(line) < 24:
            lines[i] = line.replace('<TD>&n', '<TD bgcolor={col}>&n'.format(col=color))
        elif color in line:
            line = line.replace(color, '')
            lines[i] = line.replace('<TD', '<TD bgcolor={col} '.format(col=color))
            lines[i] = line.replace('<TH', '<TH bgcolor={col} '.format(col=color))
        else:
            lines[i] = line.replace('<TD', '<TD bgcolor=white ')
        if 'bgcolor' not in lines[i]:
            lines[i] = lines[i].replace('<TH', '<TH bgcolor=white ')
    return '\n'.join(lines)


def abs_html_path(*paths):
    paths = list(paths) if type(paths) is not list else paths
    return join('https://diamond.ethz.ch', 'psi', *paths) if 'http' not in paths[0] else paths[0]


def make_dropdown(name, items, targets, n, active=False):
    s = ''
    s += '    <div class="dropdown">\n'
    s += '      <button class="dropbtn{}" onclick="f{}()">{}\n'.format(' active' if active else '', n, name)
    s += '        <i class="fa fa-caret-down"></i>\n'
    s += '      </button>\n'
    s += '      <div class="dropdown-content" id="drop{}">\n'.format(n)
    for item, target in zip(items, targets):
        s += '        {}\n'.format(make_abs_link(target, item, colour=''))
    s += '      </div>\n'
    s += '    </div>\n'
    return s


def calc_mean(lst):
    lst = [float(i) for i in lst]
    mean_ = sum(lst) / len(lst)
    mean2 = sum(map(lambda x: x ** 2, lst)) / len(lst)
    sigma = sqrt(mean2 - mean_ ** 2)
    return mean_, sigma


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


def get_dia_channels(dic):
    return sorted(key.strip('dia') for key in dic if key.startswith('dia') and len(key) < 5)


def get_max_channels(dic):
    return max(len(get_dia_channels(data)) for data in dic.itervalues())


def make_ufloat(tup, par=0):
    if tup is None:
        return
    if type(tup) is Variable:
        return tup
    if isinstance(tup, FitRes):
        return ufloat(tup.Parameter(par), tup.ParError(par))
    return ufloat(tup[0], tup[1])


def isiter(v):
    try:
        iter(v)
        return False if type(v) is str else True
    except TypeError:
        return False


def calc_flux(run_info):
    if 'for1' not in run_info or run_info['for1'] == 0:
        if 'measuredflux' in run_info:
            return str('{0:5.0f}'.format(run_info['measuredflux'] * 2.48))
    pixel_size = 0.01 * 0.015
    area = [52 * 80 * pixel_size] * 2
    file_name = basename(run_info['maskfile']).strip('"')
    try:
        if file_name.lower() in ['none.msk', 'none', 'no mask', 'pump.msk']:
            raise UserWarning
        f = open(join(Dir, 'masks', file_name), 'r')
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
            area = [(dic['cornTop'][1] - dic['cornBot'][1] + 1) * (dic['cornTop'][0] - dic['cornBot'][0] + 1) * pixel_size for dic in data.values()]
        except KeyError:
            area = [dic['col'][1] - dic['col'][0] + 1 * dic['row'][1] - dic['row'][0] + 1 * pixel_size for dic in data.values()]
    except IOError:
        warning('Could not find mask file "{f}"! Not taking any mask!'.format(f=file_name))
    except UserWarning:
        pass
    flux = [run_info['for{0}'.format(i + 1)] / area[i] / 1000. for i in range(len(area))]
    return '{0:1.0f}'.format(mean(flux))


def pickle(*rel_path, print_dur=False):
    def inner(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            pickle_path = f'{join(Dir, *rel_path)}.pickle'
            redo = kwargs['_redo'] if '_redo' in kwargs else False
            if file_exists(pickle_path) and not redo:
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
        return self.Pars[arg] if not self.Format else dig_str(self.Pars[arg], self.Format)

    def ParError(self, arg):
        if arg >= len(self.Errors):
            return ''
        return self.Errors[arg] if not self.Format else dig_str(self.Errors[arg], self.Format)
# endregion CLASSES
# ----------------------------------------


def do_nothing():
    pass
