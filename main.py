import machine
import network
import time
from umqtt.simple import MQTTClient

import breakout_scd41
from breakout_bme69x import BreakoutBME69X, STATUS_HEATER_STABLE
from pimoroni_i2c import PimoroniI2C
from pimoroni import BREAKOUT_GARDEN_I2C_PINS

# -------------------------------------------------
# WIFI
# -------------------------------------------------

SSID = ""
PASSWORD = ""

# -------------------------------------------------
# MQTT
# -------------------------------------------------

MQTT_BROKER = ""
MQTT_PORT = 
MQTT_CLIENT = "pico-env"

TOPIC_BASE = "sensors/office"

# -------------------------------------------------
# LED
# -------------------------------------------------

led = machine.Pin("LED", machine.Pin.OUT)
led.value(1)

# -------------------------------------------------
# WIFI CONNECT
# -------------------------------------------------

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if not wlan.isconnected():
        print("Connecting to WiFi...")
        wlan.connect(SSID, PASSWORD)

        while not wlan.isconnected():
            time.sleep(1)

    print("WiFi connected:", wlan.ifconfig())

# -------------------------------------------------
# MQTT CONNECT
# -------------------------------------------------

def connect_mqtt():
    client = MQTTClient(MQTT_CLIENT, MQTT_BROKER, port=MQTT_PORT)
    client.connect()
    print("Connected to MQTT")
    return client

# -------------------------------------------------
# PUBLISH HELPER
# -------------------------------------------------

def publish(client, topic, value):
    full_topic = f"{TOPIC_BASE}/{topic}"

    try:
        client.publish(full_topic, str(value))
        print("Published:", full_topic, value)

    except Exception as e:
        print("MQTT publish failed:", e)

# -------------------------------------------------
# CONNECT NETWORK
# -------------------------------------------------

connect_wifi()
client = connect_mqtt()

# -------------------------------------------------
# I2C + SENSORS
# -------------------------------------------------

i2c = PimoroniI2C(**BREAKOUT_GARDEN_I2C_PINS)

# SCD41
breakout_scd41.init(i2c)
breakout_scd41.start()

# BME69x
bme = BreakoutBME69X(i2c, 0x76)

print("Sensors started...")
print("------------------")

# -------------------------------------------------
# MAIN LOOP
# -------------------------------------------------

while True:

    # ---------- BME69x ----------

    temperature_bme, pressure, humidity_bme, gas, status, _, _ = bme.read()

    heater = status & STATUS_HEATER_STABLE

    publish(client, "temperature", round(temperature_bme, 2))
    publish(client, "humidity", round(humidity_bme, 2))
    publish(client, "pressure", round(pressure, 2))
    publish(client, "gas", int(gas))

    # ---------- SCD41 ----------

    if breakout_scd41.ready():

        co2, temperature_scd, humidity_scd = breakout_scd41.measure()

        publish(client, "co2", co2)
        publish(client, "temperature_scd", round(temperature_scd, 2))
        publish(client, "humidity_scd", round(humidity_scd, 2))

    print("------------------")

    time.sleep(60)
