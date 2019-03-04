#!/usr/bin/env python
# --------------------------------------------------------
#       script to create an overview html of the figures
# created on December 20th 2018 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from homepage import HomePage
from Utils import *
from DiaScan import DiaScan
import HTMLTable


class PicturePage(HomePage):

    def __init__(self, dia_scan, config='conf.ini'):
        HomePage.__init__(self, 'pic_test', config)
        self.DiaScan = dia_scan
        self.Body = ''

    def make(self):
        for run in self.DiaScan.Runs:
            self.make_run(run)
        self.make_tc()

    def make_tc(self):
        self.set_file_path(join(self.DiaScan.Path, 'figures.html'))
        self.make_tc_header()
        self.make_signal()
        self.make_signal_distributions()
        self.make_pulser()
        self.make_maps()
        self.set_body(self.Body)
        self.create()
        self.Body = ''

    def make_run(self, run):
        self.set_file_path(join(self.DiaScan.get_run_path(run), 'index.html'))
        self.Body += make_lines(2)
        self.make_run_header(run)
        self.make_tracking(run)
        self.make_occupancies(run)
        self.make_control(run)
        self.make_timing(run)
        self.make_run_maps(run)
        self.make_run_signal(run)
        self.make_run_pulser(run)
        self.set_body(self.Body)
        self.create()
        self.Body = ''

    def make_run_header(self, run):
        self.Body += make_lines(1)
        header = [head(bold(word)) for word in ['Diamond', add_spacings('Run'), 'Flux [kHz/cm{}]'.format(sup(2)), add_spacings('Bias [V]'), 'Date', 'Duration']]
        date = '{}, {}'.format(self.DiaScan.get_run_start(run), self.DiaScan.Year)
        dc = self.DiaScan
        row = [head(bold(center_txt(word))) for word in [dc.Diamond, dc.get_run_flux(run), dc.get_run_bias(run), date, dc.calc_run_duration(run)]]
        self.Body += add_bkg(HTMLTable.table([row], header_row=header), self.BackgroundColor)
        self.Body += '<hr>\n'

    def make_tc_header(self):
        self.Body += make_lines(3)
        dc = self.DiaScan
        header = [head(bold(word)) for word in ['Diamond', add_spacings('Run Plan'), add_spacings('Runs'), 'Flux [kHz/cm{}]'.format(sup(2)), add_spacings('Bias [V]'), 'Date', 'Duration']]
        date = '{}, {}'.format(self.DiaScan.get_run_start(dc.Runs[0]), dc.Year)
        row = [head(bold(center_txt(word))) for word in [dc.Diamond, dc.RunPlan, dc.get_runs_str(), dc.get_flux_str(), make_bias_str(dc.Bias), date, dc.Duration]]
        self.Body += add_bkg(HTMLTable.table([row], header_row=header), self.BackgroundColor)
        self.Body += '<hr>\n'

    def make_signal(self):
        self.Body += head(bold('Signal Pulse Height'))
        for pic in ['CombinedPulseHeights', 'PulseHeightZeroFlux', 'PedestalMeanFlux', 'PedestalSigmaFlux']:
            self.Body += embed_pdf(self.get_pic_path(pic))

    def make_signal_distributions(self):
        self.Body += head(bold('Signal Distribution'))
        for pic in ['SignalDistributions', 'SignalDistributionsLogY']:
            self.Body += embed_pdf(self.get_pic_path(pic))

    def make_pulser(self):
        self.Body += head(bold('Pulser Pulse Height'))
        for pic in ['CombinedPulserPulseHeights', 'PulserPedestalMeanFlux', 'PulserPedestalSigmaFlux']:
            self.Body += embed_pdf(self.get_pic_path(pic))

    def make_maps(self):
        self.Body += make_lines(1)
        self.Body += head(bold('Hit Maps'))
        for i in xrange(len(self.DiaScan.Runs)):
            self.Body += embed_pdf(self.get_pic_path('HitMap{:02d}'.format(i)))
        self.Body += make_lines(1)
        self.Body += head(bold('Signal Maps'))
        for i in xrange(len(self.DiaScan.Runs)):
            self.Body += embed_pdf(self.get_pic_path('SignalMap{:02d}'.format(i)))

    def make_tracking(self, run):
        # self.Body += make_lines(1)
        self.Body += head(bold('Tracking'))
        for pic in ['Chi2Tracks', 'Chi2X', 'Chi2Y', 'TrackAngleX', 'TrackAngleY']:
            self.Body += embed_pdf(self.get_pic_path(pic, run))

    def make_occupancies(self, run):
        self.Body += make_lines(1)
        self.Body += head(bold('Telescope Occupacies'))
        for i in xrange(4):
            self.Body += embed_pdf(self.get_pic_path('HitMap{}'.format(i), run))

    def make_control(self, run):
        self.Body += make_lines(1)
        self.Body += head(bold('Flux and Pulser Rate'))
        self.Body += embed_pdf(self.get_pic_path('FluxProfile', run), width=800, zoom=104)
        self.Body += embed_pdf(self.get_pic_path('PulserRate', run), width=800, zoom=104)
        self.Body += make_lines(1)
        self.Body += head(bold('Current and Event Alignment'))
        self.Body += embed_pdf(self.get_pic_path('Currents{}_{}_{}'.format(self.DiaScan.TestCampaign, self.DiaScan.Channel, run), run), width=800, zoom=104)
        self.Body += embed_pdf(self.get_pic_path('EventAlignment', run))

    def make_timing(self, run):
        self.Body += make_lines(1)
        self.Body += head(bold('Timing'))
        for pic in ['OriPeakPosVsTriggerCell', 'TimingComparison', 'FinePeakPosFit', 'FineCorrection']:
            self.Body += embed_pdf(self.get_pic_path(pic, run))

    def make_run_maps(self, run):
        self.Body += make_lines(1)
        self.Body += head(bold('Maps'))
        self.Body += embed_pdf(self.get_pic_path('HitMap', run))
        self.Body += embed_pdf(self.get_pic_path('SignalMap2D', run))

    def make_run_signal(self, run):
        self.Body += make_lines(1)
        self.Body += head(bold('Pulse Height'))
        self.Body += embed_pdf(self.get_pic_path('SignalDistribution', run))
        self.Body += embed_pdf(self.get_pic_path('PulseHeight10000', run))
        self.Body += embed_pdf(self.get_pic_path('PedestalDistributionFitAllCuts', run))

    def make_run_pulser(self, run):
        self.Body += make_lines(1)
        self.Body += head(bold('Pulser Pulser Height'))
        self.Body += embed_pdf(self.get_pic_path('PulserDistributionFit', run))
        self.Body += embed_pdf(self.get_pic_path('PedestalDistributionFitPulserBeamOn', run))

    def get_pic_path(self, name, run=None):
        return abs_html_path(join(self.DiaScan.Path if run is None else self.DiaScan.get_run_path(run), '{}.pdf'.format(name)))


if __name__ == '__main__':

    d = DiaScan('201510', '03', '1')
    z = PicturePage(d)
    z.make()
