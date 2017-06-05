from binding import Observable,notifiable_property

class Node(Observable):
    def __init__(self, name = "unknown", parent=None):
        
        super(Node, self).__init__()
        
        self._name = name
        self._children = []
        self._parent = parent
        
        if parent is not None:
            parent.addChild(self)
    
    def typeInfo(self):
        return "NODE"

    @classmethod
    def typeInfo(cls):
        return "NODE"
    
    def addChild(self, child):
        self._children.append(child)
        child._parent = self

    def insertChild(self, position, child):
        
        if position < 0 or position > len(self._children):
            return False
        
        self._children.insert(position, child)
        child._parent = self
        return True

    def removeChild(self, position):
        
        if position < 0 or position > len(self._children):
            return False
        
        child = self._children.pop(position)
        child._parent = None

        return True

    def columnCount(self):
        return 2

    def name():
        def fget(self):return self._name
        def fset(self,value):self._name = value
        return locals()
    name = notifiable_property("name",**name())
##    name = property(**name())

    def child(self, row):
        return self._children[row]

    def getChildByName(self,name, case_sensitive= False):
        def equal_case_sensitive(a,b):
            return a == b
        def equal_case_insensitive(a,b):
            return a.lower() == b.lower()

        comparator = equal_case_sensitive if case_sensitive else equal_case_insensitive
                                   
        childs = [n for n in self._children if comparator(n.name,name)]#n.name == name]
        if len(childs)>0:
            return childs[0]
        else:
            return None
    
    def childCount(self):
        return len(self._children)
    
    def parent(self):
        return self._parent
    
    def row(self):
        if self._parent is not None:
            return self._parent._children.index(self)


    def log(self, tabLevel=-1):

        output     = ""
        tabLevel += 1
        
        for i in range(tabLevel):
            output += "\t"
        
        output += "|------" + self._name + "\n"
        
        for child in self._children:
            output += child.log(tabLevel)
        
        tabLevel -= 1
        output += "\n"
        
        return output

    def __repr__(self):
        return self.log()

    def data(self,column):
        if      column is 0: return self.name
        elif    column is 1: return self.typeInfo()
        

    def setData(self,column,value):
        if column is 0: self.name=value#.toPyObject())
        elif column is 1: pass

    def resource(self):
        return None

class ExperimentSettings(Node):
    def __init__(self, parent = None):
        super(ExperimentSettings,self).__init__("ExperimentSettings",parent)
        #this settings - separate class. shoy\uld be saved to file

        self.__working_directory = None
        self.__expeiment_name = None
        self.__measurement_name = None
        self.__measurement_count  = 0
        
        self.__calibrate_before_measurement = False
        self.__overload_rejecion = False

        self.__display_refresh = 10
        self.__averages = 100

        self.__use_homemade_amplifier = True
        self.__homemade_amp_coeff = 178
        self.__use_second_amplifier = True
        self.__second_amp_coeff = 100

        self.__load_resistance = 5000
        
        self.__need_measure_temperature = False
        self.__meas_gated_structure = True
        self.__meas_characteristic_type = 0; # 0 is output 1 is transfer


        self.__use_transistor_selector = False
        self.__transistor_list = None

        self.__use_set_vds_range = False
        self.__vds_range = None

        self.__use_set_vfg_range = False
        self.__vfg_range = None

        self.__front_gate_voltage = 0
        self.__drain_source_voltage = 0

    def get_column_count(self):
       return 24  # amount of properties in ExperimentSettings class

    def data(self,column):
        #self.__working_directory = None
        if column is 0: return self.working_directory
        #self.__expeiment_name = None
        elif column is 1: return self.expeiment_name
        #self.__measurement_name = None
        elif column is 2: return self.measurement_name
        #self.__measurement_count  = 0
        elif column is 3: return self.measurement_count

        
        #self.__calibrate_before_measurement = False
        elif column is 4: return self.calibrate_before_measurement
        #self.__overload_rejecion = False
        elif column is 5: return self.overload_rejecion

        #self.__display_refresh = 10
        elif column is 6: return self.display_refresh
        #self.__averages = 100
        elif column is 7: return self.averages

        #self.__use_homemade_amplifier = True
        elif column is 8: return self.use_homemade_amplifier
        #self.__homemade_amp_coeff = 178
        elif column is 9: return self.homemade_amp_coeff


        #self.__use_second_amplifier = True
        elif column is 10: return self.use_second_amplifier
        #self.__second_amp_coeff = 100
        elif column is 11: return self.second_amp_coeff

        #self.__load_resistance = 5000
        elif column is 12: return self.load_resistance

        #self.__need_measure_temperature = False
        elif column is 13: return self.need_measure_temperature

        #self.__meas_gated_structure = True
        elif column is 14: return self.meas_gated_structure
        #self.__meas_characteristic_type = 0; # 0 is output 1 is transfer
        elif column is 15: return self.meas_characteristic_type

        #self.__use_transistor_selector = False
        elif column is 16: return self.use_transistor_selector
        #self.__transistor_list = None
        elif column is 17: return self.transistor_list

        #self.__use_set_vds_range = False
        elif column is 18: return self.use_set_vds_range
        #self.__vds_range = None
        elif column is 19: return self.vds_range

        #self.__use_set_vfg_range = False
        elif column is 20: return self.use_set_vfg_range
        #self.__vfg_range = None
        elif column is 21: return self.vfg_range

        #self.__front_gate_voltage = 0
        elif column is 22: return self.front_gate_voltage
        #self.__drain_source_voltage = 0
        elif column is 23: return self.drain_source_voltage
        else:
            return None

    def setData(self,column, value):
         #self.__working_directory = None
        if column is 0: self.working_directory = value
        #self.__expeiment_name = None
        elif column is 1:  self.expeiment_name= value
        #self.__measurement_name = None
        elif column is 2:  measurement_name= value
        #self.__measurement_count  = 0
        elif column is 3:  measurement_count= value

        
        #self.__calibrate_before_measurement = False
        elif column is 4:  self.calibrate_before_measurement= value
        #self.__overload_rejecion = False
        elif column is 5:  self.overload_rejecion= value

        #self.__display_refresh = 10
        elif column is 6:  self.display_refresh= value
        #self.__averages = 100
        elif column is 7:  self.averages= value

        #self.__use_homemade_amplifier = True
        elif column is 8:  self.use_homemade_amplifier= value
        #self.__homemade_amp_coeff = 178
        elif column is 9:  self.homemade_amp_coeff= value


        #self.__use_second_amplifier = True
        elif column is 10:  self.use_second_amplifier= value
        #self.__second_amp_coeff = 100
        elif column is 11:  self.second_amp_coeff= value

        #self.__load_resistance = 5000
        elif column is 12:  self.load_resistance= value

        #self.__need_measure_temperature = False
        elif column is 13:  self.need_measure_temperature= value

        #self.__meas_gated_structure = True
        elif column is 14:  self.meas_gated_structure= value
        #self.__meas_characteristic_type = 0; # 0 is output 1 is transfer
        elif column is 15:  self.meas_characteristic_type= value

        #self.__use_transistor_selector = False
        elif column is 16:  self.use_transistor_selector= value
        #self.__transistor_list = None
        elif column is 17:  self.transistor_list= value

        #self.__use_set_vds_range = False
        elif column is 18:  self.use_set_vds_range= value
        #self.__vds_range = None
        elif column is 19:  self.vds_range= value

        #self.__use_set_vfg_range = False
        elif column is 20:  self.use_set_vfg_range= value
        #self.__vfg_range = None
        elif column is 21:  self.vfg_range= value

        #self.__front_gate_voltage = 0
        elif column is 22:  self.front_gate_voltage= value
        #self.__drain_source_voltage = 0
        elif column is 23:  self.drain_source_voltage= value

    @property
    def vds_range(self):
        return self.__vds_range

    @vds_range.setter
    def vds_range(self,value):
        self.__vds_range = value

    @property
    def vfg_range(self):
        return self.__vfg_range

    @vfg_range.setter
    def vfg_range(self,value):
        self.__vfg_range = value

    @property
    def front_gate_voltage(self):
        return self.__front_gate_voltage

    @front_gate_voltage.setter
    def front_gate_voltage(self,value):
        self.__front_gate_voltage = value

    @property
    def drain_source_voltage(self):
        return self.__drain_source_voltage

    @drain_source_voltage.setter
    def drain_source_voltage(self,value):
        self.__drain_source_voltage = value

    @property
    def working_directory(self):
        return self.__working_directory

    @working_directory.setter
    def working_directory(self,value):
        self.__working_directory = value

    #self.__expeiment_name = None
    @property
    def expeiment_name(self):
        return self.__expeiment_name

    @expeiment_name.setter
    def expeiment_name(self,value):
        self.__expeiment_name = value

    #self.__measurement_name = None
    @property
    def measurement_name(self):
        return self.__measurement_name

    @measurement_name.setter
    def measurement_name(self,value):
        self.__measurement_name = value

    #self.__measurement_count  = 0
    @property
    def measurement_count(self):
        return self.__measurement_count

    @measurement_count.setter
    def measurement_count(self,value):
        self.__measurement_count = value    


    #self.__calibrate_before_measurement = False
    @property
    def calibrate_before_measurement(self):
        return self.__calibrate_before_measurement

    @calibrate_before_measurement.setter
    def calibrate_before_measurement(self,value):
        self.__calibrate_before_measurement= value    

    #self.__overload_rejecion = False
    @property
    def overload_rejecion(self):
        return self.__overload_rejecion

    @overload_rejecion.setter
    def overload_rejecion(self,value):
        self.__overload_rejecion= value    

    #self.__display_refresh = 10
    @property
    def display_refresh(self):
        return self.__display_refresh

    @display_refresh.setter
    def display_refresh(self,value):
        self.__display_refresh= value    
    #self.__averages = 100
    @property
    def averages(self):
        return self.__averages

    @averages.setter
    def averages(self,value):
        self.__averages= value  

    #self.__use_homemade_amplifier = True
    @property
    def use_homemade_amplifier(self):
        return self.__use_homemade_amplifier

    @use_homemade_amplifier.setter
    def use_homemade_amplifier(self,value):
        self.__use_homemade_amplifier= value  


    #self.__homemade_amp_coeff = 178
    @property
    def homemade_amp_coeff(self):
        return self.__homemade_amp_coeff

    @homemade_amp_coeff.setter
    def homemade_amp_coeff(self,value):
        self.__homemade_amp_coeff= value  

    #self.__use_second_amplifier = True
    @property
    def use_second_amplifier(self):
        return self.__use_second_amplifier

    @use_second_amplifier.setter
    def use_second_amplifier(self,value):
        self.__use_second_amplifier= value 


    #self.__second_amp_coeff = 100
    @property
    def second_amp_coeff(self):
        return self.__second_amp_coeff

    @second_amp_coeff.setter
    def second_amp_coeff(self,value):
        self.__second_amp_coeff= value 

    #self.__load_resistance = 5000
    @property
    def load_resistance(self):
        return self.__load_resistance

    @load_resistance.setter
    def load_resistance(self,value):
        self.__load_resistance= value 
        
    #self.__need_measure_temperature = False
    @property
    def need_measure_temperature(self):
        return self.__need_measure_temperature

    @need_measure_temperature.setter
    def need_measure_temperature(self,value):
        self.__need_measure_temperature= value 

    #self.__meas_gated_structure = True
    @property
    def meas_gated_structure(self):
        return self.__meas_gated_structure

    @meas_gated_structure.setter
    def meas_gated_structure(self,value):
        self.__meas_gated_structure= value 
   
    #self.__meas_characteristic_type = 0; # 0 is output 1 is transfer
    @property
    def meas_characteristic_type(self):
        return self.__meas_characteristic_type

    @meas_characteristic_type.setter
    def meas_characteristic_type(self,value):
        self.__meas_characteristic_type= value

    #self.__use_transistor_selector = False
    @property
    def use_transistor_selector(self):
        return self.__use_transistor_selector

    @use_transistor_selector.setter
    def use_transistor_selector(self,value):
        self.__use_transistor_selector= value

    #self.__transistor_list = None
    @property
    def transistor_list(self):
        return self.__transistor_list

    @transistor_list.setter
    def transistor_list(self,value):
        self.__transistor_list= value

    #self.__use_set_vds_range = False
    @property
    def use_set_vds_range(self):
        return self.__use_set_vds_range

    @use_set_vds_range.setter
    def use_set_vds_range(self,value):
        self.__use_set_vds_range= value
    #self.__use_set_vfg_range = False
    @property
    def use_set_vfg_range(self):
        return self.__use_set_vfg_range

    @use_set_vfg_range.setter
    def use_set_vfg_range(self,value):
        self.__use_set_vfg_range= value
