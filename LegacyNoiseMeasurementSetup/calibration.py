import numpy as np

class CalibrationInfo:
    def __init__(self):
        super().__init__()



class Calibration:
    def __init__(self, spectrum_ranges, use_preamplifier = True, use_second_amplifier = True):
        super().__init__()
        self.cabilration_data = {
            "second_amplifier":None,
            "preamplifier": None
            }
        
        self._use_preamplifier = use_preamplifier
        self._use_second_amplifier = use_second_amplifier

        self._preamplifier_frequency_response = None
        self._preamplifier_calibration_curve = None

        self._second_amplifier_frequency_response = None
        self._second_amplifier_calibration_curve = None

        self._spectrum_ranges = spectrum_ranges
        



    def load_calibration_data(self):
        
        pass


    def _apply_calibration(self, amplifier, gain, spectrum_data):
        freq, data = spectrum_data
        calibration_curve = self.cabilration_data[amplifier]["calibration_curve"][freq]
        freq_response = self.cabilration_data[amplifier]["freq_response"][freq]
        
        result = data/(freq_response*freq_response) - calibration_curve
        return result



    def apply_calibration(self, noise_spectrum):

        return noise_spectrum

    #def divide_by_amplification_coefficient(self,
    

if __name__ == "__main__":
    size = 10
    arr = np.ones((size,2)).T
    freq,data = arr
    calibration_curve = np.random.rand(size)
    freq_response = np.random.rand(size)
    
    result = data/(freq_response*freq_response) - calibration_curve
    print(result)


    
    