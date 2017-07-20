import numpy as np
import json

class CalibrationInfo:
    def __init__(self):
        super().__init__()



class Calibration:
    def __init__(self, use_preamplifier = True, use_second_amplifier = True):
        super().__init__()
        self.calibration_data_info = {}
        self.calibration_data = {}
        
        self._use_preamplifier = use_preamplifier
        self._use_second_amplifier = use_second_amplifier
        
        self._spectrum_ranges = {}
        
        self.load_calibration_data()
            
        #self.load_calibration_data()

    def init_spectrum_range_calibration(self, spectrum_ranges):
        pass

    def load_calibration_data(self):
        try:
            with open("calibration_data.dat","r") as f:
                self.calibration_data_info = json.load(f)

            for k,v in self.calibration_data_info.items():
                freq_resp_filename = v["frequency_response_filename"]
                calibration_curve_filename = v["calibration_curve_filename"]
                freq_resp = np.loadtxt(freq_resp_filename)
                calib_curve = np.loadtxt(calibration_curve_filename)
                self.calibration_data[k] = {"frequency_response":freq_resp, "calibration_curve": calib_curve}
                #ampl_data = self.calibration_data[k]
                #freq_resp = ampl_data["frequency_response"]
                #calib_curve = ampl_data["calibration_curve"]
                #np.savetxt(freq_resp_filename, freq_resp)
                #np.savetxt(calibration_curve_filename, calib_curve)

            return True
        except Exception as e:
            return False
        
        #self.cablibration_data['preamplifier'] = {"frequency_response":None, "calibration_curve": None}
        #self.cablibration_data['second_amplifier'] = {"frequency_response":None, "calibration_curve": None}
        
    def save_calibration_data(self):
        with open("calibration_data.dat","w") as f:
            json.dump(self.calibration_data_info,f)

        for k,v in self.calibration_data_info.items():
            freq_resp_filename = v["frequency_response_filename"]
            calibration_curve_filename = v["calibration_curve_filename"]
            ampl_data = self.calibration_data[k]
            freq_resp = ampl_data["frequency_response"]
            calib_curve = ampl_data["calibration_curve"]
            np.savetxt(freq_resp_filename, freq_resp)
            np.savetxt(calibration_curve_filename, calib_curve)


    def add_amplifier(self, amplifier_name, amplifier_id, frequencies, frequency_response, calibration_curve):
        min_freq = frequencies[0]
        max_freq = frequencies[-1]
        self.calibration_data_info[amplifier_name] = {"ID": amplifier_id,"min_freq":min_freq,"max_freq": max_freq, "frequency_response_filename": "{0}_{1}.dat".format(amplifier_name,"freq_resp"), "calibration_curve_filename": "{0}_{1}.dat".format(amplifier_name,"calibration_curve")}
        self.calibration_data[amplifier_name] = {"frequency_response":frequency_response, "calibration_curve": calibration_curve}

    def _apply_calibration(self, amplifier, gain, spectrum_data):
        freq, data = spectrum_data
        calibration_curve = self.cabilration_data[amplifier]["calibration_curve"][freq]
        freq_response_sqr = self.cabilration_data[amplifier]["freq_response"][freq] 
        gain_sqr = gain*gain
        result = data/(gain_sqr*freq_response_sqr) - calibration_curve
        return result



    def apply_calibration(self, noise_spectrum):

        return noise_spectrum

    #def divide_by_amplification_coefficient(self,
    

if __name__ == "__main__":
    c = Calibration(None)
    arr = np.ones((10,2)).T
    freq = np.ones(10)
    print(arr)
    c.add_amplifier("preamp", 1, freq,arr,arr)
    c.save_calibration_data()
    #size = 10
    #arr = np.ones((size,2)).T
    #ampl = 178
    #freq,data = arr

    #print(data)
    #calibration_curve = np.random.rand(size)
    #print(calibration_curve)
    #freq_response = 178 * np.random.rand(size)
    #print(freq_response)
    #result = data/(freq_response*freq_response) - calibration_curve
    #print(result)


    
    