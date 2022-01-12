import serial   # pip install pySerial
import sys
import json
import time
from datetime import datetime

from PyQt5.QtGui import QIcon       # pip install PyQT5
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import pyqtgraph as pg  # pyqtgraph is used to display the data pip install pyqtgraph


class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLabel(text='Time', units=None)
        self.enableAutoSIPrefix(False)

    def tickStrings(self, values, scale, spacing):
        if spacing < 1:
            return [datetime.fromtimestamp(value).strftime("%H:%M:%S.%f") for value in values]
        if spacing < 30:
            return [datetime.fromtimestamp(value).strftime("%H:%M:%S") for value in values]
        else:
            return [datetime.fromtimestamp(value).strftime("%H:%M") for value in values]


def timestamp():
    return int(time.mktime(datetime.now().timetuple()))


class SixGraphWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.graph = pg.PlotWidget(
            title="Example plot",
            labels={'left': 'Reading / mV'},
            axisItems={'bottom': TimeAxisItem(orientation='bottom')}
        )
        self.graph.setXRange(timestamp(), timestamp() + 30)
        self.graph.autoRange()
        self.graph.showGrid(x=True, y=True)
        self.legend = self.graph.addLegend(offset=(1, 1), verSpacing=-6, brush='#777777AA', labelTextSize='7pt')

        self.layout = QGridLayout(self)
        self.layout.addWidget(self.graph, 0, 0)

        self.pen1 = 'w'
        self.pen2 = 'w'
        self.pen3 = 'w'
        self.pen4 = 'w'
        self.pen5 = 'w'
        self.pen6 = 'w'

        self.plotCurve1 = self.graph.plot(pen=self.pen1)
        self.plotCurve2 = self.graph.plot(pen=self.pen2)
        self.plotCurve3 = self.graph.plot(pen=self.pen3)
        self.plotCurve4 = self.graph.plot(pen=self.pen4)
        self.plotCurve5 = self.graph.plot(pen=self.pen5)
        self.plotCurve6 = self.graph.plot(pen=self.pen6)

        self.plotData1 = {'x': [], 'y': []}
        self.plotData2 = {'x': [], 'y': []}
        self.plotData3 = {'x': [], 'y': []}
        self.plotData4 = {'x': [], 'y': []}
        self.plotData5 = {'x': [], 'y': []}
        self.plotData6 = {'x': [], 'y': []}

    def update_pens(self, p1, p2, p3, p4, p5, p6):
        self.pen1 = p1
        self.pen2 = p2
        self.pen3 = p3
        self.pen4 = p4
        self.pen5 = p5
        self.pen6 = p6
        self.plotCurve1 = self.graph.plot(pen=self.pen1)
        self.plotCurve2 = self.graph.plot(pen=self.pen2)
        self.plotCurve3 = self.graph.plot(pen=self.pen3)
        self.plotCurve4 = self.graph.plot(pen=self.pen4)
        self.plotCurve5 = self.graph.plot(pen=self.pen5)
        self.plotCurve6 = self.graph.plot(pen=self.pen6)

    def update_names(self, n1, n2, n3, n4, n5, n6):
        self.plotCurve1 = self.graph.plot(name=n1, pen=self.pen1)
        self.plotCurve2 = self.graph.plot(name=n2, pen=self.pen2)
        self.plotCurve3 = self.graph.plot(name=n3, pen=self.pen3)
        self.plotCurve4 = self.graph.plot(name=n4, pen=self.pen4)
        self.plotCurve5 = self.graph.plot(name=n5, pen=self.pen5)
        self.plotCurve6 = self.graph.plot(name=n6, pen=self.pen6)

    def update_title(self, title):
        self.graph.setTitle(title)

    def update_labels(self, labelleft):
        self.graph.setLabels(left=labelleft)

    def update_plots(self, v1, v2, v3, v4, v5, v6):
        self.plotData1['y'].append(v1)
        self.plotData2['y'].append(v2)
        self.plotData3['y'].append(v3)
        self.plotData4['y'].append(v4)
        self.plotData5['y'].append(v5)
        self.plotData6['y'].append(v6)

        self.plotData1['x'].append(timestamp())
        self.plotData2['x'].append(timestamp())
        self.plotData3['x'].append(timestamp())
        self.plotData4['x'].append(timestamp())
        self.plotData5['x'].append(timestamp())
        self.plotData6['x'].append(timestamp())

        if len(self.plotData1['y']) > 3600:
            self.plotData1['y'].pop(0)
            self.plotData2['y'].pop(0)
            self.plotData3['y'].pop(0)
            self.plotData4['y'].pop(0)
            self.plotData5['y'].pop(0)
            self.plotData6['y'].pop(0)
            self.plotData1['x'].pop(0)
            self.plotData2['x'].pop(0)
            self.plotData3['x'].pop(0)
            self.plotData4['x'].pop(0)
            self.plotData5['x'].pop(0)
            self.plotData6['x'].pop(0)

        self.plotCurve1.setData(self.plotData1['x'], self.plotData1['y'])
        self.plotCurve2.setData(self.plotData2['x'], self.plotData2['y'])
        self.plotCurve3.setData(self.plotData3['x'], self.plotData3['y'])
        self.plotCurve4.setData(self.plotData4['x'], self.plotData4['y'])
        self.plotCurve5.setData(self.plotData5['x'], self.plotData5['y'])
        self.plotCurve6.setData(self.plotData6['x'], self.plotData6['y'])


class StatusSignals(QObject):
    status_notification = pyqtSignal(dict)


class SerialDataThread(QRunnable):
    def __init__(self, port_name):
        super().__init__()
        self.port_name = port_name
        self.serialPort = serial.Serial(self.port_name, 9600, timeout=0,
                                        parity=serial.PARITY_EVEN, rtscts=0, stopbits=1)
        self.signals = StatusSignals()

    def run(self):
        header = False
        max_size = 30
        payload = []
        self.serialPort.flushInput()
        while 1:
            if self.serialPort.in_waiting > 0:
                data_byte = self.serialPort.read()
                #        print(ord(dataByte),end=',')
                if header:
                    if len(payload) < max_size:
                        payload.append(ord(data_byte))
                    else:  # watch out for the end of data character '0x03'
                        if ord(data_byte) == 0x03:
                            # print(payload)
                            header = False
                            pm1_reg = int(payload[0]) | int(payload[1]) << 8 | int(payload[2]) << 16 | int(
                                payload[3]) << 24
                            pm25_reg = int(payload[4]) | int(payload[5]) << 8 | int(payload[6]) << 16 | int(
                                payload[7]) << 24
                            pm10_reg = int(payload[8]) | int(payload[9]) << 8 | int(payload[10]) << 16 | int(
                                payload[11]) << 24
                            #                    print()
                            #                    print(PM1_Reg,PM25_Reg,PM10_Reg )

                            reg1 = int(payload[12]) | int(payload[13]) << 8
                            reg2 = int(payload[14]) | int(payload[15]) << 8
                            reg3 = int(payload[15]) | int(payload[17]) << 8

                            reg4 = payload[20] | payload[21] << 8
                            reg5 = payload[22] | payload[23] << 8
                            reg6 = payload[24] | payload[25] << 8

                            print(reg1, reg2, reg3, reg4, reg5, reg6)
                            status = str("{}")
                            j_status = json.loads(status)
                            j_status['Reg1'] = str(reg1)
                            j_status['Reg2'] = str(reg2)
                            j_status['Reg3'] = str(reg3)
                            j_status['Reg4'] = str(reg4)
                            j_status['Reg5'] = str(reg5)
                            j_status['Reg6'] = str(reg6)
                            self.signals.status_notification.emit(j_status)

                else:
                    if ord(data_byte) == 0x02:
                        header = True
                        payload.clear()
        #               print("Payload length is "+str(len(payload)))


class AppForm(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('Particle Counts')

        self.particle_history = []

# Create the GUI elements.

        self.file_menu = self.menuBar().addMenu("&File")
        self.create_menu()

        self.main_frame = QWidget()
        self.create_main_frame()

        self.create_status_bar()

#  Create the thread pool
        self.pool = QThreadPool()
        self.pool.setMaxThreadCount(32)
        self.threadCount = self.pool.maxThreadCount()

        # create the worker thread that gets the data from the serial port
        worker = SerialDataThread('COM27')
        worker.signals.status_notification.connect(self.data_handler)
        self.pool.start(worker)


# Create the timer which will ping the items and make sure they are still alive.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer_interval = 1000                  # This is very aggressive checking.  Should be 10000 (10s)
        self.timer.start(self.timer_interval)

    def data_handler(self, status):
        # print("status_handler- " + str(status))
        try:
            if len(status) > 0:
                reg_value1 = QTableWidgetItem(str(status['Reg1']))
                reg_value1.setTextAlignment(Qt.AlignCenter+Qt.AlignVCenter)
                self.device_table.setItem(0, 0, reg_value1)

                reg_value2 = QTableWidgetItem(str(status['Reg2']))
                reg_value2.setTextAlignment(Qt.AlignCenter + Qt.AlignVCenter)
                self.device_table.setItem(0, 1, reg_value2)

                reg_value3 = QTableWidgetItem(str(status['Reg3']))
                reg_value3.setTextAlignment(Qt.AlignCenter + Qt.AlignVCenter)
                self.device_table.setItem(0, 2, reg_value3)

                reg_value4 = QTableWidgetItem(str(status['Reg4']))
                reg_value4.setTextAlignment(Qt.AlignCenter + Qt.AlignVCenter)
                self.device_table.setItem(0, 3, reg_value4)

                reg_value5 = QTableWidgetItem(str(status['Reg5']))
                reg_value5.setTextAlignment(Qt.AlignCenter + Qt.AlignVCenter)
                self.device_table.setItem(0, 4, reg_value5)

                reg_value6 = QTableWidgetItem(str(status['Reg6']))
                reg_value6.setTextAlignment(Qt.AlignCenter + Qt.AlignVCenter)
                self.device_table.setItem(0, 5, reg_value6)

                new_value1 = int(status['Reg1'])
                new_value2 = int(status['Reg2'])
                new_value3 = int(status['Reg3'])
                new_value4 = int(status['Reg4'])
                new_value5 = int(status['Reg5'])
                new_value6 = int(status['Reg6'])
                self.particle_graph.update_plots(new_value1, new_value2, new_value3, new_value4, new_value5, new_value6)

        except Exception as e:
            print(repr(e))
            pass

    def on_timer(self):
        pass

    def create_main_frame(self):
        # ---------------------------------------------------------------
        # Control Layout
        # ---------------------------------------------------------------
        self.device_table = QTableWidget(0, 6)
        self.device_table.verticalHeader().setVisible(False)     # hides row numbers
        self.device_table.setMinimumWidth(602)
        self.device_table.setMaximumWidth(602)
        self.device_table.setMinimumHeight(45)
        self.device_table.setMaximumHeight(45)
        self.device_table.setHorizontalHeaderLabels(
            ['0.3-0.5μm', '0.5-1.0μm', '1.0-2.5μm', '2.5-5.0μm', '5.0-7.5μm', '7.5-10.0μm'])
        self.device_table.setColumnWidth(0, 100)    # 0.3-0.5μm
        self.device_table.setColumnWidth(1, 100)    # 0.5-1.0μm
        self.device_table.setColumnWidth(2, 100)    # 1.0-2.5μm
        self.device_table.setColumnWidth(3, 100)    # 2.5-5.0μm
        self.device_table.setColumnWidth(4, 100)    # 5.0-7.5μm
        self.device_table.setColumnWidth(5, 100)    # 7.5-10.0μm

        control_layout = QVBoxLayout()
        control_layout.addWidget(self.device_table)
        self.device_table.insertRow(0)
        self.device_table.setRowHeight(0, 20)

        # -----------------------------------------------
        # Create  plot windows
        # -----------------------------------------------
        self.data_plot_layout = QSplitter()
        self.data_plot_layout.setOrientation(Qt.Vertical)

        self.particle_graph = SixGraphWidget()
        self.particle_graph.update_title("Particles")
        self.particle_graph.update_labels("Particles / s")
        self.particle_graph.update_pens('r', 'g', 'y', 'b', 'cyan', 'w')
        self.particle_graph.update_names('0.3-0.5μm', '0.5-1.0μm', '1.0-2.5μm', '2.5-5.0μm', '5.0-7.5μm', '7.5-10.0μm')
        self.data_plot_layout.addWidget(self.particle_graph)

        control_layout.addWidget(self.data_plot_layout)

        self.main_frame.setLayout(control_layout)
        self.setCentralWidget(self.main_frame)

    def create_status_bar(self):
        self.status_text = QLabel("")
        self.statusBar().addWidget(self.status_text, 1)

    def create_menu(self):
        quit_action = self.create_action("&Quit", slot=self.close, shortcut="Ctrl+Q", tip="Close the application")
        self.add_actions(self.file_menu, (None, quit_action))

    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(self, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            pass
        if checkable:
            action.setCheckable(True)
        return action


def main():
    app = QApplication(sys.argv)
    form = AppForm()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()
    