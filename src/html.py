# --------------------------------------------------------
#       html helpers
# created on June 24th 2021 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from src.utils import isfile, join, BaseDir, warning, info, PBar, add_spaces, isiter, datetime
from os.path import basename
from pytz import timezone, utc
from pathlib import Path
from typing import Any


def tag(name, txt, *opts_):
    return f'<{name}{prep_opts(*opts_)}>{txt}</{name}>'


def sup(txt):
    return tag('sup', txt)


def nth(d):
    nth.ext = ['th', 'st', 'nd', 'rd'] + ['th'] * 16
    return sup(nth.ext[int(d) % 20])


def irr2str(val, unit=False):
    return val if val == '?' else 'nonirr' if not val or val == '0' else '{} &middot 10<sup>{}</sup>{}'.format(*val.split('e'), f' n/cm{sup(2)}' if unit else '')


def conv_time(time_str, to_string=True):
    t = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=utc).astimezone(timezone('Europe/Zurich'))
    return t.strftime(f'%b %d{nth(t.day)} %H:%M:%S') if to_string else t


def div(txt, *opts_):
    return tag('div', txt, *opts_)


def a(txt, *opts_):
    return tag('a', txt, *opts_)


def small(txt, *opts_):
    return tag('small', txt, *opts_)


def big(txt):
    return tag('span', txt, f'class="bigger"')


def image(filename, h=None, w=None):
    return tag('img', '', *opts(src=path(filename), h=h, w=w))


def icon(filename):
    return image(filename, 15, 15)


def fig_icon(symbol=9736):
    return big(f'&#{symbol}')


def empty_line(n=1):
    return '<br/>' * n


def make_root_html():
    f = File()
    h = File()
    h.add_line('<meta charset="UTF-8">')
    h.add_line('<link rel="icon" href="/psi2/figures/pic.png">')
    h.add_line('<title>{title}</title>')
    h.add_line(script('/jsroot/scripts/JSRoot.core.min.js', 'type="text/javascript"'))
    f.set_header(h.text)
    b = File()
    b.add_line('JSROOT.settings.Palette = {pal}')
    b.add_line('JSROOT.openFile("{filename}")')
    b.add_line('.then(file => file.readObject("c;1"))', ind=1)
    b.add_line('.then(obj => JSROOT.draw("drawing", obj, "{draw_opt}"));', ind=1)
    b = File.add_tag(b.text, 'script', 'type="text/javascript"')
    f.set_body('\n'.join([div('', 'id="drawing"'), b]))
    return f


def style(center=False, right=False, left=False, colour=None, vcenter=False, fontsize=None, smaller=False, transform=None, nowrap=None, hline=None, w=None, wmin=None, wmax=None):
    align = f'text-align: {"center" if center else "right" if right else "left"}' if any([center, right, left]) else ''
    valign = f'vertical-align: middle' if vcenter else ''
    colour = f'color: {colour}' if colour else ''
    tf = f'text-transform: {transform}' if transform else ''
    fs = f'font-size: {"smaller" if smaller else fontsize}' if fontsize is not None or smaller else ''
    wrp = 'white-space: nowrap' if nowrap is not None else ''
    hline = f'border-bottom: {hline}' if hline is not None else ''
    w = f'width: {w}' if w is not None else ''
    wmin = f'min-width: {wmin}' if wmin is not None else ''
    wmax = f'max-width: {wmax}' if wmax is not None else ''
    sargs = [sarg for sarg in [align, colour, valign, fs, tf, wrp, hline, w, wmin, wmax] if sarg]
    return f'style="{"; ".join(sargs)}"' if sargs else ''


def path(*dirs):
    return Path(*dirs) if 'http' in str(Path(*dirs)) else Path('/psi2', *dirs)


def link(target, name, active=False, center=False, new_tab=False, use_name=True, colour: Any = None, right=False, warn=True):
    fpath = BaseDir.joinpath(target)
    if fpath.exists() or fpath.is_dir() and fpath.joinpath('index.html').exists() or 'http' in str(target):
        return a(name, style(center, right, colour=colour), *opts(active=active, new_tab=new_tab), *make_opt('href', path(target)))
    warning(f'The file {target} does not exist!', prnt=warn)
    return name if use_name else ''


def prep_opts(*opts_):
    return f' {" ".join(filter(bool, opts_))}' if len(opts_) else ''


def heading(txt, size=1, *opts_):
    return tag(f'h{size}', txt, *opts_)


def script(src, *opts_):
    return tag('script', '', f'src="{src}"', *opts_)


def dropdown(name, items, targets, n, active=False, ind=1):
    s = File()
    s.add_line('<div class="dropdown">', ind)
    s.add_line(f'<button class="dropbtn{" active" if active else ""}" onclick="f{n}()">{name}', ind + 1)
    s.add_line('<i class="fa fa-caret-down"></i>', ind + 2)
    s.add_line('</button>', ind + 1)
    s.add_line(f'<div class="dropdown-content" id="drop{n}">', ind + 1)
    for item, target in zip(items, targets):
        s.add_line(link(target, item, colour=None), ind + 2)
    s.add_line('</div>', ind + 1)
    s.add_line('</div>', ind)
    return s.text


def opts(rs=None, cs=None, src=None, h=None, w=None, active=None, new_tab=None):
    return make_opt('rowspan', rs) + make_opt('colspan', cs) + make_opt('src', src) + make_opt('height', h) + make_opt('width', w) + make_opt('class', 'active' if active else None) \
           + make_opt('target', '_blank' if new_tab else None)


def sopts(rs=None, cs=None, src=None):
    return ' '.join(opts(rs, cs, src))


def make_opt(name, value):
    return [] if value is None else [f'{name}="{value}"']


def make_tup(v):
    return v if type(v) is tuple else (v, '')


def table(title, header, rows, *row_opts, w=None):
    title = heading(title, 2, 'class="mb-5"')
    h1, h2 = (header, None) if type(header[0]) in [tuple, str] else header
    h1 = File().add_lines([tag('th', *txt if isiter(txt) else [txt], 'scope="col"') for txt in h1]).text
    h1 = File.add_tag(h1, 'tr')
    if h2 is not None:
        h2 = File().add_lines([tag('th', small(txt), 'scope="col"', style(transform='none')) for txt in h2]).text
        h2 = File.add_tag(h2, 'tr')
        h1 = f'{h1}\n{h2}'
    h1 = File.add_tag(h1, 'thead')
    rows = File.add_tag(File().add_lines([table_row(row, *row_opts) for row in rows]).text, 'tbody')
    t = File.add_tag(f'{h1}\n{rows}', 'table', f'class="table table-striped custom-table" {style(wmax=w, wmin=w)}')
    t = '\n'.join([title, File.add_tag(t, 'div', 'class="table-responsive"')])
    t = File.add_tag(t, 'div', 'class="container"')
    return File.add_tag(t, 'div', 'class="content"')


def table_row(row, *o):
    """ style: ([(txt, *fmt), txt, ...], *gen_fmt) or [(txt, *fmt), txt, ...]"""
    row = make_tup(row)  # make tuple if no general fmt for all items is given
    row, fmt = row[0], row[1:]
    return File.add_tag(File().add_lines([tag('td', *make_tup(txt)) for txt in row]).text, 'tr', 'scope="row"', *o, *fmt)


LinkIcon = fig_icon(8635)
NoIcon = fig_icon(128561)
Good = '#5EA85E'


class File:

    def __init__(self, filename=None, ind_width=2, verbose=True):
        self.FileName = None if filename is None else filename if filename.startswith('/scratch') else join(BaseDir, filename)
        self.T = ''
        self.Header = ''
        self.Body = ''
        self.Scripts = ''
        self.W = ind_width

        self.PBar = PBar()
        self.Verbose = verbose

    def __str__(self):
        return self.T if self.Header is None else f'{self.Header}\n{self.Body}'

    def __repr__(self):
        return f'{self.__class__.__name__}: {None if self.FileName is None else basename(self.FileName)}'

    def set_filename(self, *name):
        self.FileName = Path(*name) if str(name[0]).startswith('/scratch') else BaseDir.joinpath(*name)

    def set_header(self, txt, *opts_):
        self.Header = self.add_tag(txt, 'head', *opts_)

    def set_body(self, txt, *opts_):
        self.Body = self.add_tag(txt, 'body', *opts_)

    def set_verbose(self, status):
        self.Verbose = status

    def add_line(self, txt='', ind=0):
        self.T += f'{" " * ind * self.W}{txt}\n'

    def add_lines(self, lines, ind=0):
        for line in lines:
            self.add_line(line, ind)
        return self

    def add_comment(self, txt, ind=0):
        self.add_line(f'<!-- {txt} -->', ind)

    def link(self, target, name, warn=True, *args, **kwargs):
        return link(target, name, *args, **kwargs, warn=warn and self.Verbose)
        
    @staticmethod
    def add_tag(txt, tag_, *opts_):
        lines = txt.split('\n')
        lines = lines[:-1] if not lines[-1] else lines
        if not lines[0].startswith(' '):
            lines = [f'  {line}' for line in lines]
        return '\n'.join([f'<{tag_}{prep_opts(*opts_)}>'] + lines + [f'</{tag_}>'])
        
    @staticmethod
    def add_root(t):
        t = File.add_tag(t, 'html', 'lang="en"')
        return f'<!doctype html>\n{t}'

    def save(self, add_root=True):
        t = self.text if not self.Header else f'{self.Header}\n{self.Body}' 
        if add_root:
            t = self.add_root(t)
        with open(self.FileName, 'w+') as f:
            f.write(t)
            f.truncate()
        self.info(f'wrote file {self.FileName}')

    @property
    def text(self):
        return self.T

    def show(self):
        print(self.text)

    def info(self, txt, endl=True, prnt=True):
        return info(txt, endl, prnt=prnt and self.Verbose)

    def check_content(self):
        if isfile(self.FileName):
            with open(self.FileName) as f:
                return self.T == ''.join(f.readlines())
        return False

    def clear(self):
        self.T = self.Header = self.Body = self.Scripts = ''


ROOTHTML = make_root_html()


def create_root(file_path: Path, title='', draw_opt='colz', pal=55):
    f = File(str(file_path.with_suffix('.html')))
    f.set_body(ROOTHTML.Body.format(pal=pal, filename=file_path.name, draw_opt=draw_opt))
    f.set_header(ROOTHTML.Header.format(title=f'{add_spaces(file_path.stem.title())} {title}'))
    f.save()
