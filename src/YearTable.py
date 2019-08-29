#!/usr/bin/env python
# --------------------------------------------------------
#       class to create the year tables
# created on December 20th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from Table import Table
from Utils import *
import HTMLTable
from json import loads


class YearTable(Table):

    def __init__(self, year):
        Table.__init__(self)
        self.Year = year
        self.TestCampaigns = self.get_test_campaigns()

    def get_body(self):
        txt = make_lines(3)
        txt += head(bold('ETH Diamonds Overview for {}\n'.format(self.Year)))
        # single crystal
        txt += '{}\n'.format(head('Single-Crystalline Diamonds:', size=3))
        txt += self.build_scvd()
        # poly chrystal
        txt += '{}\n'.format(head('Poly-Crystalline Diamonds:', size=3))
        txt += self.build_pcvd()
        # silicon pad
        txt += '{}\n'.format(head('Silicon Diodes:', size=3))
        txt += self.build_diodes()
        # legend
        txt += self.build_legend()
        return txt

    def build_scvd(self):
        return self.build(scvd=True)

    def build_pcvd(self):
        return self.build()

    def build_diodes(self):
        return self.build(si=True)

    def build(self, scvd=False, si=False):
        header, first_row = self.build_header(self.Year)
        rows = [first_row]
        dias = self.get_diamond_names(scvd, si)
        for dia in dias:
            row = [make_abs_link(join('Diamonds', dia, 'index.html'), name=dia)]
            # general information
            for col in self.OtherCols:
                row.append(self.build_col(col, dia))
            # test campaigns
            for tc in self.TestCampaigns:
                row += self.make_info_str(str_to_tc(tc), dia)
            rows.append(row)
        return add_bkg(HTMLTable.table(rows, header_row=header, ), self.BkgCol)

    def get_test_campaigns(self):
        return [tc for tc in self.TestCampaigns if str(self.Year)[2:] in tc]

    def build_header(self, year):
        header_row = ['#rs2#{d}'.format(d=add_spacings('Diamond'))] + ['#rs2#{c}'.format(c=col) for col in self.get_col_titles()]
        second_row = []
        for date in self.TestCampaigns:
            if str(year)[2:] in date:
                header_row += ['#cs4#{d}'.format(d=make_link(join('BeamTests', date, 'RunPlans.html'), date, path=self.Dir))]
                second_row += [center_txt(txt) for txt in [add_spacings('Type', 2), 'Irr* [neq]', make_abs_link(join('Overview', 'AmpBoards.html'), 'BN*'), 'Data Set*']]
        return header_row, second_row

    def build_col(self, col, dia):
        if col == 'Manufacturer':
            return self.get_manufacturer(dia)
        elif col == 'Thickness':
            return self.get_thickness(dia)

    def get_manufacturer(self, dia):
        url, name = (self.get_info(dia, 'Manufacturer', option) for option in ['url', 'name'])
        return make_abs_link(url, name, center=True, new_tab=True)

    def get_thickness(self, dia):
        thickness = self.get_info(dia, 'Thickness', 'value')
        return center_txt(thickness if thickness else '??')

    def get_col_titles(self):
        dic = {'Thickness': 'T* [&mu;m]', 'Manufacturer': add_spacings('Manufacturer')}
        return [dic[col] if col in dic else col for col in self.OtherCols]

    def get_single_crystal_dias(self):
        dias = [dia for dia in loads(self.Config.get('General', 'single_crystal')) if dia not in self.Exclude]
        s_dias = [dia for dia in dias if dia.startswith('S') and dia[2].isdigit()]
        return sorted(s_dias, key=lambda x: int(remove_letters(x))) + sorted(dia for dia in dias if dia not in s_dias)

    def get_si_diodes(self):
        return sorted(dia for dia in loads(self.Config.get('General', 'si-diodes')) if dia not in self.Exclude)

    def get_diamond_names(self, scvd=False, si=False):
        if scvd:
            return self.get_single_crystal_dias()
        elif si:
            return self.get_si_diodes()
        return sorted([dia for dia in self.Diamonds if dia not in self.get_single_crystal_dias() + self.get_si_diodes() + self.Exclude])

    def make_set_string(self, tc, dia):
        dias = self.DiaScans.get_all_rp_diamonds(tc)
        dia_set = [dias[0]]
        for i in xrange(1, len(dias)):
            if dias[i] != dias[i - 1]:
                dia_set.append(dias[i])
        strings = ['{i}{j}'.format(i=i, j='f' if not tup.index(dia) else 'b') for i, tup in enumerate(dia_set, 1) if dia in tup]
        for i in xrange(len(strings)):
            if i and not i % 3:
                strings[i] = '<br/>{}'.format(strings[i])
        return center_txt(','.join(strings))

    def make_info_str(self, tc, dia):
        if not self.get_info(dia, tc, 'type', quiet=True):  # if the tc exists it always has the type option
            return ['#cs4#']
        typ = center_txt(self.get_info(dia, tc, 'type'))
        irr = self.get_irradiation(tc, dia)
        board_number = self.get_info(dia, tc, 'boardnumber')
        board_number = center_txt(board_number if board_number else '-' if 'pix' in typ else '?')
        set_str = make_abs_link(join('Diamonds', dia, 'BeamTests', tc_to_str(tc), 'index.html'), name=self.make_set_string(tc, dia))
        return [typ, irr, board_number, set_str]

    @staticmethod
    def build_legend():
        string = make_lines(1)
        string += '<br/>*<br/>   BN  = Board Number\n'
        string += '<br/>         Irr = Irradiation \n'
        string += '<br/>         T   = Thickness \n'
        string += '<br/>         Data Set = Example "1f": Results of the front (f) diamond the first (1) measured set of diamonds during the beam test campaign \n\n'
        return string


if __name__ == '__main__':
    z = YearTable('2015')
