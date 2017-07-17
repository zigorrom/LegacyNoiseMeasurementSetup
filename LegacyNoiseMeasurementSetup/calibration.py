
class Calibration:
    def __init__(self, use_preamplifier = True, use_second_amplifier = True):
        super().__init__()
        self.cabilration_data = {
            "second_amplifier":None,
            "preamplifier": None
            }
        
        self._use_preamplifier = use_preamplifier
        self._use_second_amplifier = use_second_amplifier

        self._preamplifier_gain = None
        self._preamplifier_calibration_curve = None

        self._second_amplifier_gain = None
        self._second_amplifier_calibration_curve = None




    def load_calibration_data(self):
        pass



    def apply_calibration(self, noise_spectrum):

        return noise_spectrum

    #def divide_by_amplification_coefficient(self,
    