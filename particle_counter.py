import pyqtgraph
import serial   # pip install pySerial
import sys
import json
import time
from datetime import datetime
import requests

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


class MultiGraphWidget(QWidget):
    def __init__(self,plot_count, parent=None,):
        QWidget.__init__(self, parent)
        self.graph = pg.PlotWidget(
            title="Example plot",
            labels={'left': 'Reading / mV'},
            axisItems={'bottom': TimeAxisItem(orientation='bottom')}
        )
        self.plot_count = plot_count
        self.graph.setXRange(timestamp(), timestamp() + 30)
        self.graph.autoRange()
        self.graph.showGrid(x=True, y=True)
        self.legend = self.graph.addLegend(offset=(1, 1), verSpacing=0, brush='#777777AA', labelTextSize='7pt')
 #       self.legend = self.graph.addLegend(offset=(1, 1), verSpacing=0, brush='#777777AA', labelTextSize='7pt')

        self.layout = QGridLayout(self)
        self.layout.addWidget(self.graph, 0, 0)

        self.pens = []
        for p in range(plot_count):
            self.pens.append(pyqtgraph.mkPen('k'))

        self.symbol_pens = []
        for p in range(plot_count):
            self.symbol_pens.append(pyqtgraph.mkPen('k'))

        self.plot_names = []
        for p in range(plot_count):
            self.plot_names.append('')

        self.symbols = []
        for p in range(plot_count):
            self.symbols.append(None)

        self.line_widths = []
        for p in range(plot_count):
            self.line_widths.append(1)

        self.plot_curves = []
        for c in range(plot_count):
           self.plot_curves.append(self.graph.plot(pen=self.pens[c]))

        self.plot_datas = []
        for d in range(plot_count):
            self.plot_datas.append({'x': [], 'y': []})

    def update_plot_styles(self):
        self.plot_curves.clear()
        for p in range(self.plot_count):
            self.plot_curves.append ( self.graph.plot(pen=self.pens[p],
                                                      width= self.line_widths[p],
                                                      name=self.plot_names[p],
                                                      symbol=self.symbols[p],
                                                      symbolSize=4,
                                                      symbolBrush= self.pens[p],
                                                      symbolPen=self.symbol_pens[p]
                                                      )
                                      )



    def update_widths(self, new_widths):
        for w in range(len(new_widths)):
            self.line_widths[w] = new_widths[w]
        #self.update_plot_styles()

    def update_symbols(self, new_symbols):
        for s in range(len(new_symbols)):
            self.symbols[s] = new_symbols[s]
        #self.update_plot_styles()

    def update_pens(self, new_pens):
        for p in range(len(new_pens)):
            self.pens[p]=new_pens[p]
        #self.update_plot_styles()

    def update_symbol_pens(self, new_pens):
        for p in range(len(new_pens)):
            self.symbol_pens[p]= new_pens[p]
        #self.update_plot_styles()

    def update_names(self, new_names):
        for n in range(len(new_names)):
            self.plot_names[n]=new_names[n]
        #self.update_plot_styles()

    def update_title(self, title):
        self.graph.setTitle(title)

    def update_labels(self, labelleft):
        self.graph.setLabels(left=labelleft)

    def update_plots(self, new_values):
        new_time = timestamp()
        for v in range(len(new_values)):
            self.plot_datas[v]['y'].append(new_values[v])
            self.plot_datas[v]['x'].append(new_time)

        for v in range(len(new_values)):
            if len(self.plot_datas[v]['y']) > 3600:
                self.plot_datas[v]['y'].pop(0)
                self.plot_datas[v]['x'].pop(0)

            self.plot_curves[v].setData(self.plot_datas[v]['x'], self.plot_datas[v]['y'])


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

        self.data_count = 0
        self.particle_history = []

        self.averages = [0.0,0.0,0.0,0.0,0.0,0.0]
        self.new_values = [0.0,0.0,0.0,0.0,0.0,0.0]

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


    def data_handler(self, status):     #we have new data
        self.data_count = self.data_count+1
        try:
            if len(status) > 0:
                #unload new values from json
                self.new_values[0] = int(status['Reg1'])
                self.new_values[1] = int(status['Reg2'])
                self.new_values[2] = int(status['Reg3'])
                self.new_values[3] = int(status['Reg4'])
                self.new_values[4] = int(status['Reg5'])
                self.new_values[5] = int(status['Reg6'])
                # Calculate averages
                for i in range(6):
                    self.averages[i] = self.averages[i] - (self.averages[i] / 60) + (self.new_values[i] / 60)

                for i in range(6):
                    item = QTableWidgetItem(str(self.new_values[i]))
                    item.setTextAlignment(Qt.AlignCenter+Qt.AlignVCenter)
                    self.device_table.setItem(0, i, item)

                for i in range(6):
                    item = QTableWidgetItem("{:0.2f}".format(self.averages[i]))
                    item.setTextAlignment(Qt.AlignCenter+Qt.AlignVCenter)
                    self.device_table.setItem(1, i, item)

                self.particle_graph.update_plots(self.new_values+self.averages)
                # Post the averages to the cloud since we have 60 seconds worth of data.
                if not (self.data_count % 60):
                    payload = {"field1": str(datetime.now()),
                               "field2": str(self.averages[0]),
                               "field3": str(self.averages[1]),
                               "field4": str(self.averages[2]),
                               "field5": str(self.averages[3]),
                               "field6": str(self.averages[4]),
                               "field7": str(self.averages[5])
                               }
                    url = 'https://api.thingspeak.com/update?api_key=BXQ29DOLHM9W26DK'
                    get_response = requests.post(url, payload)
                    print(get_response)

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
        self.device_table.setMinimumHeight(90)
        self.device_table.setMaximumHeight(90)
        self.device_table.setHorizontalHeaderLabels(
            ['0.3-0.5μm', '0.5-1.0μm', '1.0-2.5μm', '2.5-5.0μm', '5.0-7.5μm', '7.5-10.0μm'])

        # Set all the columns to width 100
        for i in range(5):
            self.device_table.setColumnWidth(i, 100)

        control_layout = QVBoxLayout()
        control_layout.addWidget(self.device_table)

        self.device_table.insertRow(0)
        self.device_table.setRowHeight(0, 20)
        self.device_table.insertRow(0)
        self.device_table.setRowHeight(0, 20)

        # -----------------------------------------------
        # Create  plot windows
        # -----------------------------------------------
        self.data_plot_layout = QSplitter()
        self.data_plot_layout.setOrientation(Qt.Vertical)

        self.particle_graph = MultiGraphWidget(12)
        self.particle_graph.update_title("Particles")
        self.particle_graph.update_labels("Particles / s")

        pens = ['k', 'k', 'k', 'k', 'k', 'k','r', 'g', 'y', 'b', 'cyan', 'w']
        self.particle_graph.update_pens(pens)

        pens = ['r', 'g', 'y', 'b', 'cyan', 'w', 'r', 'g', 'y', 'b', 'cyan', 'w']
        self.particle_graph.update_symbol_pens(pens)

        plot_names = ['0.3-0.5μm', '0.5-1.0μm', '1.0-2.5μm', '2.5-5.0μm', '5.0-7.5μm', '7.5-10.0μm','0.3-0.5μm Avg', '0.5-1.0μm Avg', '1.0-2.5μm Avg', '2.5-5.0μm Avg', '5.0-7.5μm Avg', '7.5-10.0μm Avg']
        self.particle_graph.update_names(plot_names)

        widths = [0,0,0,0,0,0,1,1,1,1,1,1]
        self.particle_graph.update_widths(widths)

        symbols = ['o', 'o', 'o', 'o', 'o','o', None, None, None, None, None, None,]
        self.particle_graph.update_symbols(symbols)

        self.particle_graph.update_plot_styles()

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
