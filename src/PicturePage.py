#!/usr/bin/env python
# --------------------------------------------------------
#       script to create an overview html of the figures
# created on December 20th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from homepage import HomePage
from Utils import *
from DiaScan import DiaScan


class PicturePage(HomePage):

    def __init__(self, config, dia_scan):
        HomePage.__init__(self, config, 'pic_test')
        self.DiaScan = dia_scan

    def make(self):
        body = make_lines(3)
        body += head(bold('Tracking'))
        path = abs_html_path(join(self.DiaScan.get_run_path(123), 'TrackAngleX.pdf'))
        # self.set_body(make_figure(join(self.DiaScan.get_run_path(148), 'SignalMap2D.pdf'), width=250))
        body += embed_pdf(self.get_pic_path(123, 'Chi2All'), width=300, height=350)
        body += embed_pdf(self.get_pic_path(123, 'TrackAngleX'), width=300, height=350)
        body += embed_pdf(self.get_pic_path(123, 'TrackAngleY'), width=300, height=350)
        self.set_body(body)
        self.create()

    def get_pic_path(self, run, name):
        return abs_html_path(join(self.DiaScan.get_run_path(run), '{}.pdf'.format(name)))


if __name__ == '__main__':

    conf = ConfigParser()
    d = dirname(dirname(realpath(__file__)))
    conf.read(join(d, 'conf.ini'))

    d = DiaScan('201510', '01', '2')
    z = PicturePage(conf, d)
    z.make()
