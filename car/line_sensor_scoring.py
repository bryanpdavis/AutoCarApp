import smbus
from time import ctime, sleep

bus = smbus.SMBus(1)
base_addr = 0x3E # address of the Sparkfun Line Follower Array P / N
register_a = 0X11 # address of Data Register A(I / O[7 - 0] of the embedded SX1509 bus extender

scoringarray = [109, 45,173,141,205,221,253, 245, 229,225,233,235,239,238,236]
centervalue = 7

def w_byte(offset_addr, value):
	bus.write_byte_data(base_addr, offset_addr, value)
	return -1

def distance(x, y):
	return abs(x - y)


def get_line_follower_score(offset_addr):
	r_data = bus.read_byte_data(base_addr, offset_addr)
	if r_data == 0:
		return 1000
	elif r_data < 255:
		try:
			scoreindex = scoringarray.index(r_data)
			return distance(centervalue, scoreindex)
		except:
			return -1
		else :
			return -1


STOPPED = 0
RUNNING = 1
SCORE = 1000

while True:
	print get_line_follower_score(register_a)