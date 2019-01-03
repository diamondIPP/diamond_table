# --------------------------------------------------------
#       UTILITY FUNCTIONS
# created on May 19th 2016 by M. Reichmann
# --------------------------------------------------------

from datetime import datetime, timedelta
from termcolor import colored
import os
from ConfigParser import ConfigParser
from json import load
from os.path import join, dirname, realpath
from math import sqrt
from re import sub


Dir = dirname(dirname(realpath(__file__)))


# ==============================================
# UTILITY FUNCTIONS
# ==============================================
def log_warning(msg):
    t = datetime.now().strftime('%H:%M:%S')
    print '{head} {t} --> {msg}'.format(t=t, msg=msg, head=colored('WARNING:', 'red'))


def log_message(msg):
    t = datetime.now().strftime('%H:%M:%S')
    print '{head} {t} --> {msg}'.format(t=t, msg=msg, head=colored('INFO:', 'cyan'))


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


def make_abs_link(target, name, active=False, center=False, new_tab=False, use_name=True, colour=True):
    active = 'class="active" ' if active else ''
    new_tab = ' target="_blank"' if new_tab else ''
    name = center_txt(name) if center else name
    style = ' style="color:red"' if colour else ''
    if file_exists(join(Dir, target)) or 'http' in target:
        return '<a {act}href={tar}{tab}{s}>{name}</a>'.format(act=active, tar=abs_html_path(target), tab=new_tab, name=name, s=style)
    return name if use_name else ''


def make_figure(path, name, width=None, height=None):
    width = ' width="{}"'.format(width) if width is not None else ''
    height = ' height"{}"'.format(height) if height is not None else ''
    return '<img src="{path}" alt="{name}"{w}{h}>'.format(path=abs_html_path(path), name=name, w=width, h=height)


def indent(txt, n_spaces=2):
    lines = txt.split('\n')
    return '\n'.join('{}{}'.format(n_spaces * ' ', line) for line in lines)


def bold(txt):
    return '<b>{}</b>'.format(txt)


def head(txt, size=1):
    return '<h{0}>{1}</h{0}>'.format(size, txt)


def folder_exists(path):
    return os.path.isdir(path)


def file_exists(path):
    return os.path.isfile(path)


def create_dir(path):
    if not folder_exists(path):
        os.mkdir(path)


def write_html_header(f, name, bkg=None):
    f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n')
    f.write('<html>\n<head>\n<meta content="text/html; charset=ISO-8859-1" http-equiv="content-type">\n')
    f.write('<link rel="icon" href="http://pngimg.com/uploads/diamond/diamond_PNG6684.png">\n')
    f.write('<title> {tit} </title>\n'.format(tit=name))
    f.write('</head>\n<body{bkg}>\n\n\n'.format(bkg='' if bkg is None else ' bgcolor=' + bkg))
    f.write('<h1>{tit}</h1>\n'.format(tit=name))


def make_rp_string(string):
    return string[1:] if string[0] == '0' else string


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
        return '{v:+2.0f}'.format(v=biases)
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


def conv_time(time_str, delta=1, strg=True):
    t = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ') + timedelta(hours=delta)
    return t.strftime('%b %d{0} %H:%M:%S').format(nth(t.day)) if strg else t


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
        s += '        {}\n'.format(make_abs_link(target, item, colour=False))
    s += '      </div>\n'
    s += '    </div>\n'
    return s


def calc_mean(lst):
    lst = [float(i) for i in lst]
    mean_ = sum(lst) / len(lst)
    mean2 = sum(map(lambda x: x ** 2, lst)) / len(lst)
    sigma = sqrt(mean2 - mean_ ** 2)
    return mean_, sigma


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
