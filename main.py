import machine
import ssd1306
import time
import gc
import mqtt

# Adafruit configuration
AIO_SERVER = "io.adafruit.com"
AIO_PORT = 1883
AIO_USER = "Joel055"
AIO_KEY = "xxx_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
AIO_CLIENT_ID = "Joel-Heltec"
AIO_TEMPERATURE_FEED = "Joel055/feeds/temperature"
AIO_MEMORY_FEED = "Joel055/feeds/memory-usage"
failCount = 0

# Setup the Analog to Digital pin for the temp sensor
adc = machine.ADC()
apin = adc.channel(pin = 'P16')

# Setup the I2C pins
i2c_scl = machine.Pin('P4', mode = machine.Pin.OUT, pull = machine.Pin.PULL_UP)
i2c_sda = machine.Pin('P3', mode = machine.Pin.OUT, pull = machine.Pin.PULL_UP)
i2c = machine.I2C(0, machine.I2C.MASTER, baudrate = 100000, pins = (i2c_sda,i2c_scl))
time.sleep_ms(500)

# Start OLED
oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

# Updates OLED with the newest temp, memory, connection status
def updateOLED(temp, mem, connection):
    oled.text("Connection: " + connection, 0, 0)
    oled.text("Temp: " + temp  + " *C", 0, 25)
    oled.text("RAM: " + mem + " %", 0, 55)
    oled.show()
    oled.fill(0)

# Poll the temp sensor and measure memory usage
def pollData():
    avergeTemp = 0
    memUsage = 0

    # Poll the sensor 1000 times and wait 5 seconds, 10 times
    for i in range (0,10):
        for y in range(0,1000):
            millivolts = apin.voltage()
            avergeTemp += millivolts
            memUsage += gc.mem_alloc()

        time.sleep(5)

    # Convert the polled voltages to celcius
    conv = (milivolts - 5000000) / 10
    # Get the temperature by calculating the averge value of the polls
    tempStr = str(round(conv / 10000, 1))
    # Get the averge memory utilization
    memUsageStr = str(round(((memUsage / 10000) / 67008) * 100))
    # Free memory
    gc.collect()

    return tempStr, memUsageStr


def sendData(data):
    global failCount
    print("Publishing: (Temp: {0}, RAM: {1}) ... ".format(data[0], data[1]), end='')

    try:
        client.publish(topic=AIO_TEMPERATURE_FEED, msg = data[0])
        client.publish(topic=AIO_MEMORY_FEED, msg = data[1])

    except Exception as e:
        print("FAILED\n", e)
        failCouint += 1
        return "FAIL"

    else:
        print("DONE")
        return "OK"

# Initialize connection
print("\nConnecting to adafruit ...", end = " ")
oled.text("Connecting ...", 0, 0)
oled.show()
oled.fill(0)

try:
    client = mqtt.MQTTClient(AIO_CLIENT_ID, AIO_SERVER, AIO_PORT, AIO_USER, AIO_KEY)
    client.connect()

except Exception as e:
    print("FAIL\n", e)

else:
    print("SUCCESS\n")

while True:
    # Restart after 5 failed connection attempts
    if failCount == 5:
        machine.reset()

    newPoll = pollData()
    updateOLED(newPoll[0], newPoll[1], sendData(newPoll))