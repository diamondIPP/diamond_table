# --------------------------------------------------------
#       module for the navigation bar of the website
# created on June 24th 2021 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from src.utils import join, remove_letters
import src.html as html
from src.info import Data, Config


class NavBar(html.File):

    def __init__(self):

        super().__init__(join('content', 'nav.html'))
        self.DUTs = list(Data.DUTs.keys())

    def build(self):
        self.clear()
        self.add_line('<div class="navbar">')
        self.add_line()
        self.add_line(html.link('content', 'Home', colour=None), ind=1)
        self.add_line(html.link(join('content', 'Location.html'), 'Location', colour=None), ind=1)
        self.add_line()
        self.add_line(html.dropdown('DUTs', *self.get_dut_htmls(), n=0))
        self.add_line(html.dropdown('Beamtests', Data.TestCampaigns, self.get_tc_htmls(), n=1))
        self.add_line(html.dropdown('Single Runs', Data.TestCampaigns, self.get_tc_htmls(runs=True), n=2))
        self.add_line(html.dropdown('scCVD', *self.get_dut_links(self.used(self.get_sccvd_dias())), n=3))
        self.add_line(html.dropdown('pCVD', *self.get_dut_links(self.used(self.get_pcvd_dias())), n=4))
        self.add_line(html.dropdown('Diodes', *self.get_dut_links(self.used(self.get_si_detectors())), n=5))
        self.add_line(html.link(join('content', 'AmpBoards.html'), 'Amplifier Boards', colour=None), ind=1)
        self.add_line('</div>')
        self.save(add_root=False)

    @staticmethod
    def get(ind=2):
        f = html.File()
        f.add_comment('Navigation Bar', ind)
        f.add_line('<div id="nav-placeholder">', ind)
        f.add_line('</div>', ind)
        f.add_comment('End Navigation Bar', ind)
        return f.get_text()

    @staticmethod
    def get_dut_htmls():
        return [['scCVD', 'pCVD', 'Silicon'], [join('content', 'duts', f'{n}.html') for n in ['scCVD', 'pCVD', 'Si']]]

    @staticmethod
    def get_tc_htmls(runs=False):
        return [join('content', 'beamtests', tc, f'{"index" if runs else "RunPlans"}.html') for tc in Data.TestCampaigns]

    @staticmethod
    def get_dut_links(duts):
        return duts, [join('content', 'diamonds', dia) for dia in duts]

    def get_sccvd_dias(self):
        sccvd = Config.get_list('General', 'single crystal')
        dias = [dut for dut in self.DUTs if (dut in sccvd or dut.startswith('S') and dut[1].isdigit()) and dut not in Data.Excluded]
        s_dias = [dia for dia in dias if dia.startswith('S') and dia[1].isdigit()]
        return [Data.translate(dut) for dut in sorted(s_dias, key=lambda x: int(remove_letters(x))) + sorted(dia for dia in dias if dia not in s_dias)]

    def get_si_detectors(self):
        sil = Config.get_list('General', 'si-diodes')
        return sorted(Data.translate(dut) for dut in self.DUTs if dut in sil if dut not in Data.Excluded)

    def get_pcvd_dias(self):
        other = self.get_sccvd_dias() + self.get_si_detectors()
        return sorted(Data.translate(dut) for dut in self.DUTs if dut not in Data.Excluded and dut not in other)

    @staticmethod
    def used(duts):
        return [dut for dut in duts if Data.DUTs[dut].get_tcs()]


if __name__ == '__main__':
    pass
