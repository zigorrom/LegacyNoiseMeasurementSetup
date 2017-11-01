from experiment_handler import Experiment
import modern_fans_controller as mfans
#import modern_agilent_u2542a as mdaq
#import modern_fans_smu as msmu

def get_fans_ai_channels_from_number(number):
    assert isinstance(number, int), "Number should be integer"
    assert (number>0 and number<9),"Wrong channel number!"
    return mfans.FANS_AI_CHANNELS(number)

class FANSExperimtnt(Experiment):
    def __init__(self, input_data_queue = None, stop_event = None):
        Experiment.__init__(False, input_data_queue, stop_event)
         
    def initialize_hardware(self):
        resource = self.hardware_settings.fans_controller_resource
        self._fans_controller = mfans.FANS_CONTROLLER(resource)

        sample_motor_pin = get_ao_box_channel_from_number(self.hardware_settings.sample_motor_channel)
        gate_motor_pin = get_ao_box_channel_from_number(self.hardware_settings.gate_motor_channel)
        sample_relay = get_ao_box_channel_from_number(self.hardware_settings.sample_relay_channel)
        gate_relay = get_ao_box_channel_from_number(self.hardware_settings.gate_relay_channel)

        sample_feedback_pin = mfans.FANS_AI_CHANNELS.AI_CH_6
        gate_feedback_pin = mfans.FANS_AI_CHANNELS.AI_CH_7
        main_feedback_pin = mfans.FANS_AI_CHANNELS.AI_CH_8

        #self._fans_smu = msmu.FANS_SMU(self._fans_controller
 

if __name__ == "__main__":

    print(get_fans_ai_channels_from_number(1))
    print(get_fans_ai_channels_from_number(8))