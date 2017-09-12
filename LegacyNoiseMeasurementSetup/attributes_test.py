def unit_decorator(unit,description):
    def decorator(func):
        setattr(func, "unit", unit)
        setattr(func, "description", description)
        
        return func
    return decorator


class a:
    def __init__(self):
        self._temp = 123

    @unit_decorator("volts", "voltage variable")
    def temperature(self):
        return self._temp

    #@temperature.setter
    #def temperature(self,value):
    #    self._temp = value


obj = a()
print(dir(a.temperature))

