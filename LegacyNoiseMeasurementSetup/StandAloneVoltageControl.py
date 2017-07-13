import sys
from fans_smu import ManualSMU, voltage_setting_function
from fans_controller import FANS_AO_channel, FANS_CONTROLLER
from fans_constants import *
from PyQt4 import uic, QtGui, QtCore
from communication_layer import get_available_gpib_resources, get_available_com_resources

mainViewBase, mainViewForm = uic.loadUiType("UI_VoltageControl.ui")
class VoltageControlView(mainViewBase,mainViewForm):
    def __init__(self,parent = None):
        super(mainViewBase,self).__init__(parent)
        self.setupUi(self)
        self._gpib_resources = get_available_gpib_resources()
        self.ui_controller_resource.addItems(self._gpib_resources)
        self._initialized = False
        self._fans_controller = None
        self._fans_smu = None


    @QtCore.pyqtSlot()
    def on_ui_initialize_clicked(self):
        selected_resource = self.ui_controller_resource.currentIndex()
        resource = self._gpib_resources[selected_resource]
        self._fans_controller = FANS_CONTROLLER(resource)
        self._fans_smu = ManualSMU(self._fans_controller, AO_BOX_CHANNELS.ao_ch_1, AO_BOX_CHANNELS.ao_ch_4,AO_BOX_CHANNELS.ao_ch_9, AO_BOX_CHANNELS.ao_ch_12, 5000)
        self._initialized = True

    @QtCore.pyqtSlot()
    def on_ui_ds_positiv_clicked(self):
        if not self._initialized:
            return
        print("ui_ds_positiv")
        self._fans_smu.set_drain_source_polarity_positiv()


    @QtCore.pyqtSlot()
    def on_ui_ds_negativ_clicked(self):
        if not self._initialized:
            return
        print("ui_ds_negativ")
        self._fans_smu.set_drain_source_polarity_negativ()

    @QtCore.pyqtSlot()
    def on_ui_gs_positiv_clicked(self):
        if not self._initialized:
            return
        print("ui_gs_positiv")
        self._fans_smu.set_gate_polarity_positiv()


    @QtCore.pyqtSlot()
    def on_ui_gs_negativ_clicked(self):
        if not self._initialized:
            return
        print("ui_gs_negativ")
        self._fans_smu.set_gate_polarity_negativ()

    @QtCore.pyqtSlot()
    def on_ui_ds_move_left_fast_clicked(self):
        if not self._initialized:
            return
        print("ui_ds_move_left_fast")
        self._fans_smu.move_ds_motor_left_fast()

    @QtCore.pyqtSlot()
    def on_ui_ds_move_left_clicked(self):
        if not self._initialized:
            return
        print("ui_ds_move_left")
        self._fans_smu.move_ds_motor_left()

    @QtCore.pyqtSlot()
    def on_ui_move_right_clicked(self):
        if not self._initialized:
            return
        print("ui_move_right")
        self._fans_smu.move_ds_motor_right()

    @QtCore.pyqtSlot()
    def on_ui_move_right_fast_clicked(self):
        if not self._initialized:
            return
        print("ui_move_right_fast")
        self._fans_smu.move_ds_motor_right_fast()

    @QtCore.pyqtSlot()
    def on_ui_gs_move_left_fast_clicked(self):
        if not self._initialized:
            return
        print("ui_gs_move_left_fast")
        self._fans_smu.move_gate_motor_left_fast()

    @QtCore.pyqtSlot()
    def on_ui_gs_move_left_clicked(self):
        if not self._initialized:
            return
        print("ui_gs_move_left")
        self._fans_smu.move_gate_motor_left()

    @QtCore.pyqtSlot()
    def on_ui_gs_move_right_clicked(self):
        if not self._initialized:
            return
        print("ui_gs_move_right")
        self._fans_smu.move_gate_motor_right()

    @QtCore.pyqtSlot()
    def on_ui_gs_move_right_fast_clicked(self):
        if not self._initialized:
            return
        print("ui_gs_move_right_fast")
        self._fans_smu.move_gate_motor_right_fast()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName("Voltage Control")
    #app.setStyle("cleanlooks")

    #css = "QLineEdit#sample_voltage_start {background-color: yellow}"
    #app.setStyleSheet(css)
    #sample_voltage_start

    wnd = VoltageControlView()
    wnd.show()

    sys.exit(app.exec_())