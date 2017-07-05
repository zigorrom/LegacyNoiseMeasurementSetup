from PyQt4 import QtCore


class ExperimentWriter(QtCore.QObject):
    def __init__(self, working_directory, experiment_name = None, measurement_name = None, measurement_counter = 0, parent = None):
        super().__init__(parent)
        self._working_directory = working_directory
        self._experiment_name = experiment_name
        self._measurement_name = measurement_name
        self._measurement_counter = measurement_counter
        self.__experiment_file_extension = "dat"
        self.__measurement_file_extension = "dat"
        self._experiment_file = None
        self._measurement_file = None

    @property
    def working_directory(self):
        return self._working_directory

    @working_directory.setter
    def working_directory(self,value):
        self._working_directory = value


    def open_experiment(self, experiment_name):
        if self._experiment_file: 
            self.close_experiment()
        
        self._experiment_name = experiment_name
        filepath = join(self._working_directory, "{0}.{1}".format(self._experiment_name,self.__experiment_file_extension))
        self._experiment_file = open(filepath, 'wb')
        self._write_experiment_header()


    def close_experiment(self):
        if self._experiment_file and not self._experiment_file.closed:
            self._experiment_file.close()
            


    def open_measurement(self, measurement_name, measurement_counter):
        if self._measurement_file:
            self.close_measurement()

        self._measurement_name = measurement_name
        self._measurement_counter = measurement_counter
        filepath = join(self._working_directory, "{0}_{1}.{2}".format(self._measurement_name,self._measurement_counter, self.__measurement_file_extension))
        self._measurement_file = open(filepath,"wb")
        self._write_measurement_header()

    def _write_experiment_header(self):
        pass

    def _write_measurement_header(self):
        pass

    def close_measurement(self):
        if self._measurement_file and not self._measurement_file.closed:
            self._measurement_file.close()

    def write_experiment_info(self,info):
        pass

    def write_measurement(self,data):
        pass


if __name__=="__main__":
    pass