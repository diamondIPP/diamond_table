# --------------------------------------------------------
#       UTILITY FUNCTIONS
# created on May 19th 2016 by M. Reichmann
# --------------------------------------------------------

from datetime import datetime
from termcolor import colored
import os
from ConfigParser import ConfigParser
from json import load
from os.path import join, dirname, realpath, basename
from re import sub
from uncertainties import ufloat
from uncertainties.core import Variable
from numpy import array, sqrt, average, mean
from pytz import timezone, utc


Dir = dirname(dirname(realpath(__file__)))


# ==============================================
# UTILITY FUNCTIONS
# ==============================================
def get_t_str():
    return datetime.now().strftime('%H:%M:%S')


def warning(msg, color='yellow'):
    print '{head} {t} --> {msg}'.format(t=get_t_str(), msg=msg, head=colored('WARNING:', color))


def info(msg):
    print '{head} {t} --> {msg}'.format(t=get_t_str(), msg=msg, head=colored('INFO:', 'cyan'))


def critical(msg):
    print '{head} {t} --> {msg}\n'.format(t=get_t_str(), msg=msg, head=colored('CRITICAL:', 'red'))
    os._exit(1)


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


def print_banner(msg, symbol='='):
    print '\n{delim}\n{msg}\n{delim}\n'.format(delim=len(str(msg)) * symbol, msg=msg)


def print_small_banner(msg, symbol='-'):
    print '\n{delim}\n{msg}\n'.format(delim=len(str(msg)) * symbol, msg=msg)


def list_dirs(path):
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]


def make_link(target, name='Results', new_tab=False, path='', use_name=True, center=False):
    tab = ' target="_blank"' if new_tab else ''
    name = center_txt(name) if center else name
    if file_exists(join(path, target.strip('./'))) or not path:
        return '<a href={tar}{tab}>{nam}</a>'.format(tar=target, nam=name, tab=tab)
    return name if use_name else ''


def make_lines(n):
    return '<br/>' * n


def make_abs_link(target, name, active=False, center=False, new_tab=False, use_name=True, colour='red', warn=True):
    active = 'class="active" ' if active else ''
    new_tab = ' target="_blank"' if new_tab else ''
    name = center_txt(name) if center else name
    style = ' style="color:{}"'.format(colour) if colour else ''
    if file_exists(join(Dir, target)) or 'http' in target:
        return '<a {act}href={tar}{tab}{s}>{name}</a>'.format(act=active, tar=abs_html_path(target), tab=new_tab, name=name, s=style)
    warning('The file {} does not exist!'.format(target), color='magenta') if warn else do_nothing()
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


def indent(txt, n_spaces=2):
    lines = txt.split('\n')
    return '\n'.join('{}{}'.format(n_spaces * ' ', line) for line in lines)


def bold(txt):
    return '<b>{}</b>'.format(txt)


def head(txt, size=1):
    return '<h{0}>{1}</h{0}>\n'.format(size, txt)


def folder_exists(path):
    return os.path.isdir(path)


def file_exists(path):
    return os.path.isfile(path)


def create_dir(path):
    if not folder_exists(path):
        info('creating directory: {}'.format(path))
        os.mkdir(path)


def write_html_header(f, name, bkg=None):
    f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n')
    f.write('<html>\n<head>\n<meta content="text/html; charset=ISO-8859-1" http-equiv="content-type">\n')
    f.write('<link rel="icon" href="http://pngimg.com/uploads/diamond/diamond_PNG6684.png">\n')
    f.write('<title> {tit} </title>\n'.format(tit=name))
    f.write('</head>\n<body{bkg}>\n\n\n'.format(bkg='' if bkg is None else ' bgcolor=' + bkg))
    f.write('<h1>{tit}</h1>\n'.format(tit=name))


def make_rp_string(string, directory=False):
    return '{}{}'.format('RunPlan' if directory else '', string[1:] if string[0] == '0' else string)


def make_runplan_string(nr):
    nr = str(nr)
    return nr.zfill(2) if len(nr) <= 2 else nr.zfill(4)


def str_to_tc(tc, short=True):
    tc_str = tc.split('-')[0]
    sub_str = '-{}'.format(tc.split('-')[-1]) if '-' in str(tc) else ''
    return '{tc}{s}'.format(tc=datetime.strptime(tc_str, '%b%y').strftime('%Y%m' if short else '%B %Y'), s=sub_str)


def tc_to_str(tc, short=True):
    tc_str = str(tc).split('-')[0]
    sub_str = '-{}'.format(tc.split('-')[-1]) if '-' in str(tc) else ''
    return '{tc}{s}'.format(tc=datetime.strptime(tc_str, '%Y%m').strftime('%b%y' if short else '%B %Y'), s=sub_str)


def make_bias_str(biases):
    if type(biases) is not list:
        return '{v:+2.0f}'.format(v=float(biases))
    if len(biases) == 1:
        return '{v:+2.0f}'.format(v=biases[0])
    elif len(biases) < 4:
        return ' &#8594; '.join('{v:+2.0f}'.format(v=bias) for bias in sorted(biases, reverse=True, key=abs))
    else:
        return '{min:+4.0f} ... {max:+4.0f}'.format(min=biases[0], max=biases[-1])


def make_irr_string(val):
    if val == '?':
        return val
    if not val or val == '0':
        return 'unirr.'
    val, power = [float(i) for i in val.split('e')]
    return '{v:1.1f} &middot 10<sup>{p}</sup>'.format(v=val, p=int(power))


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
        return make_ufloat(values[0])
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
            area = [(dic['cornTop'][1] - dic['cornBot'][1] + 1) * (dic['cornTop'][0] - dic['cornBot'][0] + 1) * pixel_size for dic in data.itervalues()]
        except KeyError:
            area = [dic['col'][1] - dic['col'][0] + 1 * dic['row'][1] - dic['row'][0] + 1 * pixel_size for dic in data.itervalues()]
    except IOError:
        warning('Could not find mask file "{f}"! Not taking any mask!'.format(f=file_name))
    except UserWarning:
        pass
    flux = [run_info['for{0}'.format(i + 1)] / area[i] / 1000. for i in xrange(len(area))]
    return '{0:1.0f}'.format(mean(flux))


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


def do_nothing():
    pass
