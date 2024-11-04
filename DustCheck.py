import os
import sys
import PyQt5
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

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Creating Client name - should be unique
global clientname, CONNECTED
CONNECTED = False
r = random.randrange(1, 10000000)
clientname = "IOT_client-Id234-" + str(r)
DHT_topic = 'AirpurifierComputer/Dust'
update_rate = 9000  # in msec


class Mqtt_client():

    def __init__(self):
        # broker IP address:
        self.broker = ''
        self.topic = ''
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

    def get_broker(self):
        return self.broker

    def set_broker(self, value):
        self.broker = value

    def get_port(self):
        return self.port

    def set_port(self, value):
        self.port = value

    def get_clientName(self):
        return self.clientName

    def set_clientName(self, value):
        self.clientName = value

    def get_username(self):
        return self.username

    def set_username(self, value):
        self.username = value

    def get_password(self):
        return self.password

    def set_password(self, value):
        self.password = value

    def get_subscribeTopic(self):
        return self.subscribeTopic

    def set_subscribeTopic(self, value):
        self.subscribeTopic = value

    def get_publishTopic(self):
        return self.publishTopic

    def set_publishTopic(self, value):
        self.publishTopic = value

    def get_publishMessage(self):
        return self.publishMessage

    def set_publishMessage(self, value):
        self.publishMessage = value

    def on_log(self, client, userdata, level, buf):
        logging.debug(f"MQTT log: {buf}")

    def on_connect(self, client, userdata, flags, rc, props=None):
        global CONNECTED
        if rc == 0:
            logging.info("Connected successfully to broker")
            CONNECTED = True
            try:
                self.on_connected_to_form()
            except Exception as e:
                logging.error(f"Error while calling connected form callback: {e}")
        else:
            logging.error(f"Bad connection, Returned code={rc}")

    def on_disconnect(self, client, userdata, rc=0, props=None):
        global CONNECTED
        CONNECTED = False
        logging.warning(f"Disconnected from broker, result code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            m_decode = str(msg.payload.decode("utf-8", "ignore"))
            logging.info(f"Message received from topic {topic}: {m_decode}")
            mainwin.subscribeDock.update_mess_win(m_decode)
        except Exception as e:
            logging.error(f"Error processing received message: {e}")

    def connect_to(self):
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.clientname, clean_session=True)  # create new client instance
            self.client.on_connect = self.on_connect  # bind callback function
            self.client.on_disconnect = self.on_disconnect
            self.client.on_log = self.on_log
            self.client.on_message = self.on_message
            self.client.username_pw_set(self.username, self.password)
            logging.info(f"Connecting to broker {self.broker}:{self.port}")
            self.client.connect(self.broker, self.port)  # connect to broker
        except Exception as e:
            logging.error(f"Error while connecting to broker: {e}")

    def disconnect_from(self):
        try:
            self.client.disconnect()
            logging.info("Disconnected from broker")
        except Exception as e:
            logging.error(f"Error while disconnecting from broker: {e}")

    def start_listening(self):
        try:
            self.client.loop_start()
            logging.debug("Started MQTT loop")
        except Exception as e:
            logging.error(f"Error starting MQTT loop: {e}")

    def stop_listening(self):
        try:
            self.client.loop_stop()
            logging.debug("Stopped MQTT loop")
        except Exception as e:
            logging.error(f"Error stopping MQTT loop: {e}")

    def subscribe_to(self, topic):
        if CONNECTED:
            try:
                self.client.subscribe(topic)
                logging.info(f"Subscribed to topic: {topic}")
            except Exception as e:
                logging.error(f"Error subscribing to topic {topic}: {e}")
        else:
            logging.warning("Can't subscribe. Connection should be established first")

    def publish_to(self, topic, message):
        if CONNECTED:
            try:
                self.client.publish(topic, message)
                logging.info(f"Published message to {topic}: {message}")
            except Exception as e:
                logging.error(f"Error publishing to topic {topic}: {e}")
        else:
            logging.warning("Can't publish. Connection should be established first")


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

        self.eKeepAlive = QLineEdit()
        self.eKeepAlive.setValidator(QIntValidator())
        self.eKeepAlive.setText("60")

        self.eSSL = QCheckBox()

        self.eCleanSession = QCheckBox()
        self.eCleanSession.setChecked(True)

        self.eConnectbtn = QPushButton("Enable/Connect", self)
        self.eConnectbtn.setToolTip("Click to connect")
        self.eConnectbtn.clicked.connect(self.on_button_connect_click)
        self.eConnectbtn.setStyleSheet("background-color: gray")

        self.ePublisherTopic = QLineEdit()
        self.ePublisherTopic.setText(DHT_topic)

        self.Dust = QLineEdit()
        self.Dust.setText('')

        self.Humidity = QLineEdit()
        self.Humidity.setText('')

        formLayot = QFormLayout()
        formLayot.addRow("Turn On/Off", self.eConnectbtn)
        formLayot.addRow("Pub topic", self.ePublisherTopic)
        formLayot.addRow("Dust", self.Dust)

        widget = QWidget(self)
        widget.setLayout(formLayot)
        self.setTitleBarWidget(widget)
        self.setWidget(widget)
        self.setWindowTitle("Connect")

    def on_connected(self):
        self.eConnectbtn.setStyleSheet("background-color: green")

    def on_button_connect_click(self):
        try:
            self.mc.set_broker(self.eHostInput.text())
            self.mc.set_port(int(self.ePort.text()))
            self.mc.set_clientName(self.eClientID.text())
            self.mc.set_username(self.eUserName.text())
            self.mc.set_password(self.ePassword.text())
            self.mc.connect_to()
            self.mc.start_listening()
        except Exception as e:
            logging.error(f"Error on connect button click: {e}")

    def push_button_click(self):
        try:
            self.mc.publish_to(self.ePublisherTopic.text(), '"value":1')
        except Exception as e:
            logging.error(f"Error on publish button click: {e}")


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)

        # Init of Mqtt_client class
        self.mc = Mqtt_client()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(update_rate)  # in msec

        # general GUI settings
        self.setUnifiedTitleAndToolBarOnMac(True)

        # set up main window
        self.setGeometry(30, 600, 300, 150)
        self.setWindowTitle('Dust Check')

        # Init QDockWidget objects
        self.connectionDock = ConnectionDock(self.mc)

        self.addDockWidget(Qt.TopDockWidgetArea, self.connectionDock)

    def update_data(self):
        try:

            dustvalue = 21 + random.randrange(1, 100) / 10
            logging.debug(f'Updating time data: {dustvalue}')
            current_data = str(dustvalue)
            self.connectionDock.Dust.setText(str(dustvalue))
            self.mc.publish_to(DHT_topic, current_data)
        except Exception as e:
            logging.error(f"Error updating data: {e}")


app = QApplication(sys.argv)
mainwin = MainWindow()
mainwin.show()
app.exec_()
