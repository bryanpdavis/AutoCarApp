from time import sleep
import smbus
import traceback
bus = smbus.SMBus(1)
base_addr = 0x3E # address of the Sparkfun Line Follower Array P/N
register_a = 0X11 # address of Data Register A (I/O [7-0] of the embedded SX1509 bus extender

scoringarray = [109, 45,173,141,205,221,253, 245, 229,225,233,235,239,238,236]
centervalue = 7

# read and return a single byte at the I2C address "base_addr" offset by the "offset address"
def __distance(x,y):
    return abs(x-y)

def get_score():
	try:
		r_data = bus.read_byte_data(base_addr, register_a)
	except Exception as e:
		print(traceback.format_exc())

	#print("Raw Sensor Data:", r_data)
	if r_data == 0:
		return 1000
	elif r_data < 255:
		try:
			scoreindex = scoringarray.index(r_data)
			return __distance(centervalue, scoreindex)
		except:
			return -1
	else :
		return -1
	sleep(.25)
	
		