#! /usr/bin/env python
# --------------------------------------------------------
#       TABLE BASE CLASS
# created on October 14th 2016 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from Utils import *
from os.path import realpath, dirname, basename
from ConfigParser import ConfigParser
from glob import glob
from json import loads
from commands import getstatusoutput


class HomePage:

    def __init__(self, filename=None, config='conf.ini'):

        self.Dir = dirname(dirname(realpath(__file__)))

        self.Config = self.load_config(config_name=config)
        self.Icon = abs_html_path(join('figures', self.Config.get('Home Page', 'icon')))
        self.TextSize = self.Config.get('Home Page', 'text size')
        self.Color = self.Config.get('Home Page', 'color')
        self.BackgroundColor = self.Config.get('Home Page', 'background color')
        self.TestCampaigns = self.get_testcampaigns()

        self.FilePath = join('Overview', '{}.html'.format(filename))
        self.Body = ''

        self.NDropDowns = 6
        self.Excluded = loads(self.Config.get('General', 'exclude'))

    def __del__(self):
        info('created {}'.format(self.FilePath)) if 'default' not in self.FilePath else do_nothing()

    def load_config(self, config_name):
        conf = ConfigParser()
        conf.read(join(self.Dir, config_name))
        return conf

    def create(self):
        with open(join(self.Dir, self.FilePath), 'w') as f:
            self.write_header(f)
            self.write_style(f)
            self.write_body(f)
            self.write_script(f)
            self.write_trailer(f)

    def get_years(self):
        return ['< 2015'] + sorted(list(set(remove_letters(name)[:4] for name in glob(join(self.Dir, 'data', 'run_log*')))))

    def get_year_htmls(self):
        old = [join('Overview', 'Old.html')]
        return old + [join('Overview', '{}.html'.format(year)) for year in self.get_years()[1:]]

    @staticmethod
    def get_testcampaigns():
        words = ' '.join(getstatusoutput('ssh -tY mutter ls {}'.format(join('/scratch2', 'psi')))[-1].split('\r\n')[:-1])
        return sorted(tc.replace('psi_', '').replace('_', '').strip('\t') for tc in words.split())

    def get_tc_htmls(self, runs=False):
        return [join('BeamTests', tc_to_str(tc), '{}.html'.format('index' if runs else 'RunPlans')) for tc in self.TestCampaigns]

    def get_sccvd_dias(self):
        dias = [dia for dia in loads(self.Config.get('General', 'single_crystal')) if dia not in self.Excluded]
        s_dias = [dia for dia in dias if dia.startswith('S') and dia[2].isdigit()]
        return sorted(s_dias, key=lambda x: int(remove_letters(x))) + sorted(dia for dia in dias if dia not in s_dias)

    def get_si_detectors(self):
        return sorted(dia for dia in loads(self.Config.get('General', 'si-diodes')) if dia not in self.Excluded)

    def get_pcvd_dias(self):
        dias = [basename(name) for name in glob(join(self.Dir, 'Diamonds', '*'))]
        return sorted(dia for dia in dias if dia not in self.Excluded + self.get_sccvd_dias() + self.get_si_detectors())

    def set_body(self, txt):
        self.Body = txt

    def set_file_path(self, path):
        self.FilePath = path

    def write_body(self, f):
        f.write('<body>\n')
        f.write('  <div class="navbar">\n')
        f.write('    {}\n'.format(make_abs_link(join('Overview', 'HomePage.html'), 'Home', active='HomePage' in self.FilePath, colour=False)))
        f.write('    {}\n'.format(make_abs_link(join('Overview', 'Location.html'), 'Location', active='Location' in self.FilePath, colour=False)))
        f.write(make_dropdown('Years', self.get_years(), self.get_year_htmls(), n=0, active='20' in self.FilePath))
        f.write(make_dropdown('Diamond Scans', self.TestCampaigns, self.get_tc_htmls(), n=1))
        f.write(make_dropdown('Single Runs', self.TestCampaigns, self.get_tc_htmls(runs=True), n=2))
        f.write(make_dropdown('scCVD', self.get_sccvd_dias(), [join('Diamonds', dia, 'index.html') for dia in self.get_sccvd_dias()], n=3))
        f.write(make_dropdown('pCVD', self.get_pcvd_dias(), [join('Diamonds', dia, 'index.html') for dia in self.get_pcvd_dias()], n=4))
        f.write(make_dropdown('Silicon', self.get_si_detectors(), [join('Diamonds', dia, 'index.html') for dia in self.get_si_detectors()], n=5))
        f.write('    {}\n'.format(make_abs_link(join('Overview', 'AmpBoards.html'), 'Amplifier Boards', active='Boards' in self.FilePath, colour=False)))
        f.write('  </div>\n')
        f.write('  \n')
        f.write('{}\n'.format(self.Body))
        f.write('</body>\n')

    def write_header(self, f):
        f.write('<!DOCTYPE html>\n')
        f.write('<html lang="en">\n')
        f.write('  <head>\n')
        f.write('    <meta charset="UTF-8">\n')
        f.write('    <meta name="viewport" content="width=device-width, initial-scale=1">\n')
        f.write('    <link rel="stylesheet" href="https://www.w3schools.com/w3css/3/w3.css">\n')
        f.write('    <link rel="icon" href="{}">\n'.format(self.Icon))
        f.write('    <title> PSI Diamonds</title>\n')
        f.write('  </head>\n')

    def write_style(self, f):
        f.write('<style>\n')
        f.write('  body {')
        f.write('    margin: 0;\n')
        f.write('    font-family: "Ubuntu Mono", monospace;\n')
        f.write('    background-color: #666666;\n')
        f.write('  }\n')
        f.write('\n')
        f.write('  .dropdown {\n')
        f.write('    float: left;\n')
        f.write('    overflow: hidden;\n')
        f.write('  }\n')
        f.write('\n')
        f.write('  .navbar {\n')
        f.write('    background-color: {};\n'.format(self.BackgroundColor))
        f.write('    position: fixed;\n')
        f.write('    top: 0;\n')
        f.write('    width: 100%;\n')
        f.write('    z-index: 99999;\n')
        f.write('  }\n')
        f.write('  .navbar a, .dropdown .dropbtn {\n')
        f.write('    float: left;\n')
        f.write('    color: {};\n'.format(self.Color))
        f.write('    text-align: center;\n')
        f.write('    padding: 14px 16px;\n')
        f.write('    text-decoration: none;\n')
        f.write('    font-size: {}px;\n'.format(self.TextSize))
        f.write('    font-family: "Ubuntu Mono", monospace;\n')
        f.write('    display: inline-block;\n')
        f.write('    border: 1px solid lightgray;\n')
        f.write('    outline: none;\n')
        f.write('  }\n')
        f.write('  .dropdown {border: none}\n')
        f.write('\n')
        f.write('  .dropdown .dropbtn {\n')
        f.write('    float: none;\n')
        f.write('    background-color: inherit;\n')
        f.write('    outline: none;\n')
        f.write('    margin: 0;\n')
        f.write('    cursor: pointer;\n')
        f.write('    position: relative;\n')
        f.write('  }\n')
        f.write('\n')
        f.write('  .navbar a:hover, .dropdown:hover .dropbtn {\n')
        f.write('    background-color: #ddd;\n')
        f.write('    color: black;\n')
        f.write('    }\n')
        f.write('  .navbar a.active, .dropbtn.active {\n')
        f.write('    background-color: {};\n'.format(self.Color))
        f.write('    color: #333;')
        f.write('  }\n')
        f.write('\n')
        f.write('  .dropdown-content {\n')
        f.write('    display: none;\n')
        f.write('    position: absolute;\n')
        f.write('    background-color: {};\n'.format(self.BackgroundColor))
        f.write('    min-width: 200px;\n')
        f.write('    box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);\n')
        f.write('    z-index: 99999;\n')
        f.write('  }')
        f.write('  .dropdown-content a {\n')
        f.write('    float: none;\n')
        f.write('    color: {};\n'.format(self.Color))
        f.write('    padding: 2px 8px;\n')
        f.write('    border: none;\n')
        f.write('    text-decoration: none;\n')
        f.write('    display: block;\n')
        f.write('    text-align: left;\n')
        f.write('  }\n')
        f.write('  .dropdown-content a:hover {\n')
        f.write('    background-color: #ddd;\n')
        f.write('  }\n')
        f.write('\n')
        f.write('  .navbar .dropdown:hover .dropdown-content {\n')
        f.write('    display: block;\n')
        f.write('  }\n')
        f.write('\n')
        f.write('  .show {\n')
        f.write('    display: block;\n')
        f.write('  }\n')
        f.write('\n')
        f.write('  a.pdf {\n')
        f.write('    position: relative;\n')
        f.write('    display: inline-block;\n')
        f.write('  }\n')
        f.write('  a.pdf:after {\n')
        f.write('     content: "";\n')
        f.write('     position: absolute;\n')
        f.write('     top: 0;\n')
        f.write('     right: 0;\n')
        f.write('     bottom: 0;\n')
        f.write('     left:0;\n')
        f.write('  }\n')
        f.write('\n')
        f.write('</style>\n')

    def write_script(self, f):
        f.write('<script type="text/javascript">\n')
        f.write('\n')
        f.write('  // When the user clicks on the button, toggle between hiding and showing the dropdown content\n')
        for i in xrange(self.NDropDowns):
            f.write('  function f{0}() {{ document.getElementById("drop{0}").classList.toggle("show"); }}\n'.format(i))
        f.write('\n')
        f.write('  // Close the dropdown if the user clicks outside of it\n')
        f.write('  window.onclick = function(e){\n')
        f.write("    if (!e.target.matches('.dropbtn')) {\n")
        for i in xrange(self.NDropDowns):
            f.write('      var drop{0} = document.getElementById("drop{0}");\n'.format(i))
            f.write("      if (drop{0}.classList.contains('show')) {{ drop{0}.classList.remove('show'); }}\n".format(i))
        f.write('    }\n')
        f.write('  }\n')
        f.write('\n')
        f.write('  // show home page\n')
        f.write('  function load_home() { \n')
        f.write('    document.getElementById("content").innerHTML=\'<object type="text/html" data="{}" ></object>\';'.format(self.get_year_htmls()[-1]))
        f.write('  }\n')
        f.write('\n')
        f.write('</script>\n')

    @staticmethod
    def write_trailer(f):
        f.write('</html>\n')


if __name__ == '__main__':

    z = HomePage('HomePage')
