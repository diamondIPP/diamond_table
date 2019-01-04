#!/usr/bin/env python
# --------------------------------------------------------
#       class to create the table for the old diamonds
# created on January 4th 2019 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from Table import Table
from Utils import *
from glob import glob
from os.path import basename


class OldTable(Table):

    def __init__(self):
        Table.__init__(self)
        self.DataPath = join(self.DataPath, 'OLD')
        self.Diamonds = self.get_diamonds()

    def get_diamonds(self):
        return [basename(name) for name in glob(join(self.DataPath, '*')) if basename(name) not in self.Exclude and 'index' not in name]



if __name__ == '__main__':
    z = OldTable()

