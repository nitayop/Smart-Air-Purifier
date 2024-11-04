import os
import sys

import random
import logging
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import paho.mqtt.client as mqtt
import time
import datetime
from mqtt_init import *
from datetime import datetime

# Setup logging configuration
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout),
                              logging.FileHandler("app.log", mode='w')])

currentDateAndTime = datetime.now()

# Global variables
global clientname, CONNECTED
CONNECTED = False
r = random.randrange(1, 10000)
clientname = "IOT_client-Id234-" + str(r)
DHT_topic = 'AirpurifierComputer/Time'
update_rate = 10000  # in msec


class Mqtt_client():

    def __init__(self):
        self.broker = ''
        self.port = ''

        self.clientname = ''
        self.username = ''
        self.password = ''
        self.subscribeTopic = ''
        self.publishTopic = ''
        self.publishMessage = ''
        self.on_connected_to_form = ''

    # Setters and getters
    def set_on_connected_to_form(self, on_connected_to_form):
        self.on_connected_to_form = on_connected_to_form

    def set_broker(self, value):
        self.broker = value

    def set_port(self, value):
        self.port = value

    def set_clientName(self, value):
        self.clientname = value

    def set_username(self, value):
        self.username = value

    def set_password(self, value):
        self.password = value

    def set_subscribeTopic(self, value):
        self.subscribeTopic = value

    def set_publishTopic(self, value):
        self.publishTopic = value

    def set_publishMessage(self, value):
        self.publishMessage = value

    def on_log(self, client, userdata, level, buf):
        logging.debug("log: " + buf)

    def on_connect(self, client, userdata, flags, rc, props):
        global CONNECTED
        if rc == 0:
            logging.info("Connected OK")
            CONNECTED = True
            if self.on_connected_to_form:
                self.on_connected_to_form()
        else:
            logging.error(f"Bad connection. Returned code={rc}")

    def on_disconnect(self, client, userdata, flags, rc=0, props=None):
        global CONNECTED
        CONNECTED = False
        logging.info(f"Disconnected. Result code {rc}")

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        m_decode = str(msg.payload.decode("utf-8", "ignore"))
        logging.info(f"Message received from {topic}: {m_decode}")
        mainwin.subscribeDock.update_mess_win(m_decode)

    def connect_to(self):
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.clientname, clean_session=True)
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_log = self.on_log
            self.client.on_message = self.on_message
            self.client.username_pw_set(self.username, self.password)
            logging.info(f"Connecting to broker {self.broker}")
            self.client.connect(self.broker, self.port)
        except Exception as e:
            logging.error(f"Failed to connect to broker: {str(e)}")

    def disconnect_from(self):
        try:
            self.client.disconnect()
            logging.info("Disconnected from broker")
        except Exception as e:
            logging.error(f"Error during disconnect: {str(e)}")

    def start_listening(self):
        try:
            self.client.loop_start()
            logging.info("MQTT listening started")
        except Exception as e:
            logging.error(f"Failed to start listening: {str(e)}")

    def stop_listening(self):
        try:
            self.client.loop_stop()
            logging.info("MQTT listening stopped")
        except Exception as e:
            logging.error(f"Failed to stop listening: {str(e)}")

    def subscribe_to(self, topic):
        if CONNECTED:
            try:
                self.client.subscribe(topic)
                logging.info(f"Subscribed to {topic}")
            except Exception as e:
                logging.error(f"Failed to subscribe to {topic}: {str(e)}")
        else:
            logging.error("Cannot subscribe, connection not established")

    def publish_to(self, topic, message):
        if CONNECTED:
            try:
                self.client.publish(topic, message)
                logging.info(f"Published message to {topic}: {message}")
            except Exception as e:
                logging.error(f"Failed to publish to {topic}: {str(e)}")
        else:
            logging.error("Cannot publish, connection not established")


class ConnectionDock(QDockWidget):
    """Main """

    def __init__(self, mc):
        QDockWidget.__init__(self)

        self.mc = mc
        self.mc.set_on_connected_to_form(self.on_connected)
        self.eHostInput = QLineEdit()
        self.eHostInput.setInputMask('999.999.999.999')
        self.eHostInput.setText(broker_ip)

        self.ePort = QLineEdit()
        self.ePort.setValidator(QIntValidator())
        self.ePort.setMaxLength(4)
        self.ePort.setText(broker_port)

        self.eClientID = QLineEdit()
        global clientname
        self.eClientID.setText(clientname)

        self.eUserName = QLineEdit()
        self.eUserName.setText(username)

        self.ePassword = QLineEdit()
        self.ePassword.setEchoMode(QLineEdit.Password)
        self.ePassword.setText(password)

        self.eConnectbtn = QPushButton("Enable/Connect", self)
        self.eConnectbtn.setToolTip("Click to connect")
        self.eConnectbtn.clicked.connect(self.on_button_connect_click)
        self.eConnectbtn.setStyleSheet("background-color: gray")

        self.ePublisherTopic = QLineEdit()
        self.ePublisherTopic.setText(DHT_topic)

        self.Time = QLineEdit()
        self.Time.setText('')

        formLayout = QFormLayout()
        formLayout.addRow("Turn On/Off", self.eConnectbtn)
        formLayout.addRow("Pub topic", self.ePublisherTopic)
        formLayout.addRow("Time", self.Time)

        widget = QWidget(self)
        widget.setLayout(formLayout)
        self.setTitleBarWidget(widget)
        self.setWidget(widget)
        self.setWindowTitle("Connect")

    def on_connected(self):
        self.eConnectbtn.setStyleSheet("background-color: green")
        logging.info("Connected button state updated to green")

    def on_button_connect_click(self):
        try:
            self.mc.set_broker(self.eHostInput.text())
            self.mc.set_port(int(self.ePort.text()))
            self.mc.set_clientName(self.eClientID.text())
            self.mc.set_username(self.eUserName.text())
            self.mc.set_password(self.ePassword.text())
            self.mc.connect_to()
            self.mc.start_listening()
            logging.info("Connect button clicked and processing connection")
        except Exception as e:
            logging.error(f"Error during connect button click: {str(e)}")


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)

        self.mc = Mqtt_client()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(update_rate)

        self.setGeometry(30, 600, 300, 150)
        self.setWindowTitle('Time Check')

        self.connectionDock = ConnectionDock(self.mc)

        self.addDockWidget(Qt.TopDockWidgetArea, self.connectionDock)

    def update_data(self):
        try:

            #current_data = str(currentDateAndTime.hour)
            current_data = '03'#str(random.randrange(0,23))
            logging.debug(f'Updating time data: {current_data}')

            self.connectionDock.Time.setText(current_data)
            self.mc.publish_to(DHT_topic, current_data)
        except Exception as e:
            logging.error(f"Error during update_data: {str(e)}")


app = QApplication(sys.argv)
mainwin = MainWindow()
mainwin.show()
app.exec_()
