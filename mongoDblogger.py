from datetime import datetime, timezone
from pymongo import MongoClient
import json

import logging
import random
import sys

import paho.mqtt.client as mqtt
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from mqtt_init import *


# MongoDB setup
mongo_connection_string = "mongodb+srv://arn951:BvRnT4CnBqnGPhEi@airpurifier.nkjv2.mongodb.net/"
client = MongoClient(mongo_connection_string)
db = client["AirPurifierDB"]  # Specify your database name
collection = db["AirMessages"]  # Specify your collection name

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Creating Client name - should be unique
global clientname
r = random.randrange(1, 100000)
clientname = "IOT_client-Id-" + str(r)
dust_topic = 'AirpurifierComputer/Dust'
temperature_topic = 'AirpurifierComputer/Temperature'
time_topic = 'AirpurifierComputer/Time'
publish_topic = 'SmartAirpurifierManagerApp'
global ON
ON = False


class Mqtt_client():

    def __init__(self):
        self.broker = ''
        self.port = 0
        self.clientname = ''
        self.username = ''
        self.password = ''
        self.on_connected_to_form = ''
        self.temperature = 0
        self.dust = 0
        self.time = ''

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
        return self.clientname

    def set_clientName(self, value):
        self.clientname = value

    def get_username(self):
        return self.username

    def set_username(self, value):
        self.username = value

    def get_password(self):
        return self.password

    def set_password(self, value):
        self.password = value

    def on_log(self, client, userdata, level, buf):
        logging.debug(f"MQTT log: {buf}")

    def on_connect(self, client, userdata, flags, rc, props):
        if rc == 0:
            logging.info("Connected successfully to broker")
            try:
                self.on_connected_to_form()
            except Exception as e:
                logging.error(f"Error while calling connected form callback: {e}")
        else:
            logging.error(f"Bad connection, Returned code={rc}")

    def on_disconnect(self, client, userdata, rc=0, props=None):
        logging.warning(f"Disconnected from broker, result code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            m_decode = str(msg.payload.decode("utf-8", "ignore"))
            logging.info(f"Message received from topic {topic}: {m_decode}")

            if topic == dust_topic:
                self.dust = float(m_decode)
            elif topic == temperature_topic:
                self.temperature = float(m_decode)
            elif topic == time_topic:
                self.time = m_decode

            self.check_conditions()
        except Exception as e:
            logging.error(f"Error processing message from topic {msg.topic}: {e}")

    def save_to_mongodb(self, message):
        try:
            document = {
                "message": message,
                "timestamp": datetime.now(timezone.utc)
            }
            collection.insert_one(document)
            logging.info("Message saved to MongoDB.")
        except Exception as e:
            logging.error(f"Error saving message to MongoDB: {e}")


    def check_conditions(self):
        try:
            logging.debug(f"Condition met ? self.temperature:{self.temperature} > 28 or self.dust?{self.dust} > 22 or self.time:{self.time} == 03")

            if self.temperature > 28:
                message = f"It's time to filter the air due to temperature ({self.temperature}) > 28"
                logging.info(message)
                self.save_to_mongodb(message)

            if self.dust > 22:
                message = f"It's time to filter the air due to dust ({self.dust}) > 22"
                logging.info(message)
                self.save_to_mongodb(message)

            if self.time == "03":
                message = f"It's time to filter the air due to time ({self.time}) == 03"
                logging.info(message)
                self.save_to_mongodb(message)

        except Exception as e:
            logging.error(f"Error checking conditions: {e}")

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
        try:
            self.client.subscribe(topic)
            logging.info(f"Subscribed to topic: {topic}")
        except Exception as e:
            logging.error(f"Error subscribing to topic {topic}: {e}")

    def publish_to(self, topic, message):
        try:
            self.client.publish(topic, message)
            logging.info(f"Published message to {topic}: {message}")
        except Exception as e:
            logging.error(f"Error publishing to topic {topic}: {e}")


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
        self.eConnectbtn.setToolTip("click me to connect")
        self.eConnectbtn.clicked.connect(self.on_button_connect_click)
        self.eConnectbtn.setStyleSheet("background-color: gray")

        self.eSubscribeTopic = QLineEdit()
        self.eSubscribeTopic.setText(f"{dust_topic}, {temperature_topic}, {time_topic}")

        self.ePushtbtn = QPushButton("", self)
        self.ePushtbtn.setToolTip("Push me")
        self.ePushtbtn.setStyleSheet("background-color: gray")

        formLayout = QFormLayout()
        formLayout.addRow("Turn On/Off", self.eConnectbtn)
        formLayout.addRow("Sub topics", self.eSubscribeTopic)
        formLayout.addRow("Status", self.ePushtbtn)

        widget = QWidget(self)
        widget.setLayout(formLayout)
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
            for topic in self.eSubscribeTopic.text().split(', '):
                self.mc.subscribe_to(topic)
        except Exception as e:
            logging.error(f"Error on connect button click: {e}")

    def update_btn_state(self, text):
        global ON
        if ON:
            self.ePushtbtn.setStyleSheet("background-color: gray")
            ON = False
        else:
            self.ePushtbtn.setStyleSheet("background-color: red")
            ON = True


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)

        # Init of Mqtt_client class
        self.mc = Mqtt_client()

        # general GUI settings
        self.setUnifiedTitleAndToolBarOnMac(True)

        # set up main window
        self.setGeometry(30, 300, 300, 150)
        self.setWindowTitle('mongoDblogger')

        # Init QDockWidget objects
        self.connectionDock = ConnectionDock(self.mc)

        self.addDockWidget(Qt.TopDockWidgetArea, self.connectionDock)


app = QApplication(sys.argv)
mainwin = MainWindow()
mainwin.show()
app.exec_()





