import visa

class TemperatureSensor:
    def __init__(self, resource):
        
        rm = visa.ResourceManager()
        self.instrument = rm.open_resource(resource, write_termination='\n', read_termination = '\n') #write termination
        self._last_temperature = 300
        
    def _read_temperature(self):
        result = self.instrument.ask("KRDG?")
        temperature = 1234234 #convert result
        self._last_temperature = temperature
        return temperature

    @property
    def temperature(self):
        return self._read_temperature()

    @property
    def last_temperature(self):
        return self._last_temperature


class TemperatureController:
    def __init__(self, temperature_sensor):
        self.temperature_sensor = temperature_sensor

    def set_temperature(self,temperature):
        pass




    




if __name__ == "__main__":
    pass
