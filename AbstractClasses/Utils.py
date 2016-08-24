# --------------------------------------------------------
#       UTILITY FUNCTIONS
# created on May 19th 2016 by M. Reichmann
# --------------------------------------------------------

from datetime import datetime, timedelta
from termcolor import colored
import os
from ConfigParser import ConfigParser
from json import load


# ==============================================
# UTILITY FUNCTIONS
# ==============================================
def log_warning(msg):
    t = datetime.now().strftime('%H:%M:%S')
    print '{head} {t} --> {msg}'.format(t=t, msg=msg, head=colored('WARNING:', 'red'))


def log_message(msg):
    t = datetime.now().strftime('%H:%M:%S')
    print '{t} --> {msg}'.format(t=t, msg=msg, head=colored('WARNING:', 'red'))


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


def make_link(target, name='Results', new_tab=False, path=None, use_name=True, center=False):
    tab = ' target="_blank"' if new_tab else ''
    name = center_txt(name) if center else name
    if path is not None:
        return '<a href={tar}{tab}>{nam}</a>'.format(tar=target, nam=name, tab=tab) if file_exists('{path}/{tgt}'.format(path=path, tgt=target.strip('.'))) else (name if use_name else '')
    else:
        return '<a href={tar}{tab}>{nam}</a>'.format(tar=target, nam=name, tab=tab)


def folder_exists(path):
    return os.path.isdir(path)


def file_exists(path):
    return os.path.isfile(path)


def create_dir(path):
    if not folder_exists(path):
        os.mkdir(path)


def write_html_header(f, name):
    f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n')
    f.write('<html>\n<head>\n<meta content="text/html; charset=ISO-8859-1" http-equiv="content-type">\n')
    f.write('<title> {tit} </title>\n'.format(tit=name))
    f.write('</head>\n<body>\n\n\n')
    f.write('<h1>{tit}</h1>\n'.format(tit=name))


def make_rp_string(string):
    return string[1:] if string[0] == '0' else string


def make_tc_str(tc, txt=True):
    if tc[0].isdigit():
        return datetime.strptime(tc, '%Y%m').strftime('%B %Y' if txt else '%b%y')
    else:
        return datetime.strptime(tc, '%b%y').strftime('%Y%m' if txt else '%B %Y')


def make_bias_str(bias):
    return '{sign}{val}'.format(sign='+' if int(bias) > 0 else '', val=int(bias))


def make_info_str(last_tc, tc_str, info):
    out = ['', '']
    for tc, value in info.iteritems():
        if last_tc < tc <= tc_str:
            for key, val in value.iteritems():
                if key == 'Irradiation':
                    out[0] = 'to {0:1.0g}'.format(val)
                elif key == 'Built':
                    out[0] = 'to {0}'.format(val)
                if key == 'BoardNumber':
                    out[1] = center_txt(val)
    return out


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


def do_nothing():
    pass
