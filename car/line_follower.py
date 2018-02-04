from time import sleep
import smbus
bus = smbus.SMBus(1)
base_addr = 0x3E # address of the Sparkfun Line Follower Array P/N
register_a = 0X11 # address of Data Register A (I/O [7-0] of the embedded SX1509 bus extender

# write a single byte to the I2C address "base_addr" offset by the "offset address"

def w_byte(offset_addr, value):
        bus.write_byte_data(base_addr, offset_addr, value)
        return -1

# read and return a single byte at the I2C address "base_addr" offset by the "offset address"

def r_byte(offset_addr):
        r_data=bus.read_byte_data(base_addr, offset_addr)
        return (r_data)
#
# loop and print
while True:
        print "Data Register A = ", r_byte(register_a)
        sleep(0.25)
