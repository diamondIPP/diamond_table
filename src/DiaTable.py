#!/usr/bin/env python
# --------------------------------------------------------
#       Diamond Table
# created on April 25th 2017 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

import HTMLTable
from Table import Table
from Utils import *


class DiaTable(Table):

    def __init__(self):
        Table.__init__(self)

    def get_body(self, dia_scans):
        txt = make_lines(3)
        txt += head(bold('Overview of all RunPlans for {}'.format(dia_scans.values()[0][0].Diamond)))
        txt += self.build(dia_scans)
        return txt

    def build(self, dia_scans):

        dia = dia_scans.values()[0][0].Diamond
        header = ['#rs2#Beam Test',
                  '#rs2#Irradiation<br>[n/cm<sup>2</sup>]',
                  '#rs2#Nr. ',
                  '#rs2#Type',
                  '#rs2#Digitiser',
                  '#rs2#Position',
                  '#rs2#Runs',
                  '#cs2#Attenuators',
                  '#rs2#Bias [V]',
                  '#rs2#Leakage<br>Current',
                  '#cs4#Pulser',
                  '#cs4#Signal',
                  '#rs2#Start',
                  '#rs2#Duration']
        rows = [[center_txt(text) for text in ['Diamond', 'Pulser', 'Type', 'Mean', 'Corr.', 'Ped.', 'Pulse Height', 'Corr', 'Ped.', 'Noise [&sigma;]']]]  # sub header

        def make_pic_link(pic_name, name, use_name=True, ftype='pdf'):
            return [make_abs_link(join(dc.Path, '{}.{}'.format(pic_name, ftype)), name, center=True, use_name=use_name)]

        for tc, lst in dia_scans.iteritems():
            if not lst:
                continue
            row = ['#rs{n}#{tc}'.format(n=len(lst), tc=center_txt(tc))]                                 # Test Campaign
            row += ['#rs{n}#{irr}'.format(n=len(lst), irr=self.get_irradiation(tc, dia))]               # Irradiation
            for i, dc in enumerate(lst):
                rp_str = make_rp_string(dc.RunPlan)
                row = row if not i else []
                row += [make_abs_link(join(dc.Path, 'index.php'), rp_str, center=True)]                 # Nr
                row += [center_txt(dc.Type)]                                                            # Run Plan Type
                row += [center_txt(dc.Digitiser)]                                                       # Digitiser
                row += [center_txt(dc.DiaPosition)]                                                     # Diamond Position
                row += [make_abs_link(join(dc.Path, 'index.html'), dc.get_runs_str(), center=True)]     # Runs
                row += [center_txt(dc.Attenuator)]                                                      # Diamond Attenuators
                row += [center_txt(dc.PulserAttenuator)]                                                # Pulser Attenuators
                row += [right_txt(make_bias_str(dc.Bias))]                                              # Bias
                row += make_pic_link('PhPulserCurrent', 'Plot', use_name=False)                         # Leakage Current
                row += [dc.PulserType]                                                                  # Pulser Type
                if dc.Type == 'voltage scan':
                    row += make_pic_link('PulserVoltageScan', 'Plot', False)                            # Pulser Pulse Height
                    row += [center_txt('-')]                                                            # Pulser Pulse Height (corrected)
                    row += make_pic_link('PulserPedestalMeanVoltage', 'Plot', use_name=False)
                    row += make_pic_link('SignalVoltageScan', 'Plot', False)
                    row += [center_txt('-')]                                                            # makes no sense for Voltage Scan
                    row += make_pic_link('PedestalMeanVoltage', 'Plot', False)
                    row += make_pic_link('PedestalSigmaVoltage', dc.get_noise())
                else:
                    row += make_pic_link('CombinedPulserPulseHeights', dc.get_pulser())                 # Pulser Pulse Height
                    row += [dc.get_corrected_pulser()]                                                  # Pulser Pulse Height (corrected)
                    row += make_pic_link('PulserPedestalMeanFlux', 'Plot', use_name=False)              # Pulser Pedestal
                    row += make_pic_link('CombinedPulseHeights', dc.get_signal())                       # Pulse Height
                    row += [dc.get_corrected_signal()]                                                  # Pulse Height (corrected)
                    row += make_pic_link('PedestalMeanFlux', 'Plot', use_name=False)                    # Signal Pedestal
                    row += make_pic_link('PedestalSigmaFlux', dc.get_noise())                           # Noise
                row += [t_to_str(dc.StartTime)]                                                         # Start Time
                row += [dc.Duration]                                                                    # Duration
                rows.append(row)

        return add_bkg(HTMLTable.table(rows, header_row=header), color=self.BkgCol)


if __name__ == '__main__':
    z = DiaTable()
