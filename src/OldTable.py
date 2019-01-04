#!/usr/bin/env python
# --------------------------------------------------------
#       class to create the table for the old diamonds
# created on January 4th 2019 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from Table import Table
from Utils import *
from glob import glob
from os.path import basename
import HTMLTable


class OldTable(Table):

    def __init__(self):
        Table.__init__(self)
        self.DataPath = join(self.DataPath, 'OLD')
        self.Diamonds = self.get_diamonds()

    def get_diamonds(self):
        return sorted((basename(name) for name in glob(join(self.DataPath, '*')) if basename(name) not in self.Exclude and 'index' not in name), key=lambda x: int(remove_letters(x)))

    def get_body(self):
        txt = make_lines(3)
        txt += head(bold('Old Diamonds Overview \n'))
        txt += self.build()
        return txt

    def build(self):
        header = ['Nr', 'Name', 'Thickness [&micro;m]', 'Feed Size [mm]', 'Beam Tests', 'Comments']
        rows = []
        for i, dia in enumerate(self.Diamonds):
            row = ['{:02d}'.format(i)]          # Nr
            row += [center_txt(dia)]            # Name
            row += [self.get_thickness(dia)]    # Thickness
            row += [self.get_size(dia)]         # Feed Size
            row += [self.get_beam_tests(dia)]   # Beam Tests
            row += [self.get_comment(dia)]      # Comments
            rows.append(row)
        return add_bkg(HTMLTable.table(rows, header_row=header, ), self.BkgCol)

    def get_size(self, dia):
        size = self.get_info(dia, 'Attributes', 'size')
        return center_txt(size if size else '?')

    def get_thickness(self, dia):
        thickness = self.get_info(dia, 'Attributes', 'thickness')
        return center_txt(thickness if thickness else '?')

    def get_beam_tests(self, dia):
        beam_tests = []
        for path in glob(join(self.DataPath, dia, 'BeamTests', '*')):
            name = basename(path)
            try:
                str_to_tc(basename(name))
                beam_tests.append(name)
            except ValueError:
                pass
        return beam_tests if beam_tests else center_txt('?')

    def get_comment(self, dia):
        with open(join(self.DataPath, dia, 'comment.txt')) as f:
            return ''.join(f.readlines()).replace('\n', '<br/>')


if __name__ == '__main__':
    z = OldTable()

