#! /usr/bin/env python
# --------------------------------------------------------
#       TABLE BASE CLASS
# created on October 14th 2016 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from Utils import *
from os.path import realpath, dirname, basename
from ConfigParser import ConfigParser
from glob import glob


class HomePage:

    def __init__(self, config, filename):

        self.Dir = dirname(dirname(realpath(__file__)))

        self.Config = config
        self.Icon = abs_html_path(join('figures', self.Config.get('Home Page', 'icon')))
        self.TextSize = self.Config.get('Home Page', 'text size')
        self.Color = self.Config.get('Home Page', 'color')
        self.BackgroundColor = self.Config.get('Home Page', 'background color')

        self.FilePath = join('Overview', '{}.html'.format(filename))
        self.Body = ''

    def __del__(self):
        log_message('created {}'.format(self.FilePath)) if 'default' not in self.FilePath else do_nothing()

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
        old = [join('Diamonds', 'OLD', 'index.php')]
        return old + [join('Overview', '{}.html'.format(year)) for year in self.get_years()[1:]]

    def get_testcampaigns(self):
        return sorted(basename(name).strip('run_log.json') for name in glob(join(self.Dir, 'data', 'run_log*')))

    def get_tc_htmls(self):
        return [join('BeamTests', tc_to_str(tc), 'RunPlans.html') for tc in self.get_testcampaigns()]

    def set_body(self, txt):
        self.Body = txt

    def set_file_path(self, path):
        self.FilePath = path

    def write_body(self, f):
        f.write('<body>\n')
        f.write('  <div class="navbar">\n')
        f.write('    {}\n'.format(make_abs_link(self.FilePath, 'Home', active=True)))
        f.write('    {}\n'.format(make_abs_link(join('Overview', 'Location.html'), 'Location')))
        f.write(make_dropdown('Years', self.get_years()))
        f.write(make_dropdown('Test Campaigns', self.get_testcampaigns()))
        f.write('  </div>\n')
        f.write('  \n')
        f.write('  <p> <br /><br /><br /><br />Here could be your text...</p>\n')
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
        f.write('  .navbar a.active {\n')
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
        f.write('    z-index: 1;\n')
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
        f.write('</style>\n')

    @staticmethod
    def write_script(f):
        f.write('<script>\n')
        f.write('\n')
        f.write('  // When the user clicks on the button, toggle between hiding and showing the dropdown content\n')
        f.write('  function myFunction() { document.getElementById("myDropdown").classList.toggle("show"); }\n')
        f.write('\n')
        f.write('  // Close the dropdown if the user clicks outside of it\n')
        f.write('  window.onclick = function(e){\n')
        f.write("    if (!e.target.matches('.dropbtn')) {\n")
        f.write('      var myDropdown = document.getElementById("myDropdown");\n')
        f.write("        if (myDropdown.classList.contains('show')) {\n")
        f.write("          myDropdown.classList.remove('show');\n")
        f.write('        }\n')
        f.write('    }\n')
        f.write('  }\n')
        f.write('\n')
        f.write('</script>\n')

    @staticmethod
    def write_trailer(f):
        f.write('</html>\n')


if __name__ == '__main__':

    conf = ConfigParser()
    d = dirname(dirname(realpath(__file__)))
    conf.read(join(d, 'conf.ini'))

    z = HomePage(conf)
    z.create()