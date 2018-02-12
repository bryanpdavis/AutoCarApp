#!/usr/bin/python

#- * -coding: utf - 8 - * -

import RPi.GPIO as GPIO
import threading
import time
import video_dir
import car_dir
import motor
import os
import smbus
import sys
import line_follower_score as line_follower
from multiprocessing import Process
from threading import *
from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
from time import ctime, sleep# Import necessary modules
from datetime import datetime, timedelta

ctrl_cmd = [
	'forward',
	'backward',
	'left',
	'right',
	'stop',
	'read cpu_temp',
	'home',
	'distance',
	'x+',
	'x-',
	'y+',
	'y-',
	'xy_home',
]

busnum = 1
HOST = ''           # The variable of HOST is null, so the function bind( ) can be bound to all valid addresses.
PORT = 21567
PORT2 = 21568
BUFSIZ = 2048       # Size of the buffer
ADDR = (HOST, PORT)
ADDR2 = (HOST, PORT2)

video_dir.setup(busnum=busnum)
car_dir.setup(busnum=busnum)
motor.setup(busnum=busnum)     # Initialize the Raspberry Pi GPIO connected to the DC motor. 
video_dir.home_x_y()
car_dir.home()
#change test

bus = smbus.SMBus(1)
base_addr = 0x3E # address of the Sparkfun Line Follower Array P / N
register_a = 0X11 # address of Data Register A(I / O[7 - 0] of the embedded SX1509 bus extender

scoringarray = [
	254,
	252,
	253,
	249,
	251,
	243,
	247,
	231,
	239,
	207,
	223,
	159,
	191,
	63,
	127,
]
centervalue = 7

def CarController(socket):
	while True:
		print 'Waiting for connection to car controller service...'
		# Waiting for connection. Once receiving a connection, the function accept() returns a separate 
		# client socket for the subsequent communication. By default, the function accept() is a blocking 
		# one, which means it is suspended before the connection comes.
		clientSocket, addr = socket.accept()
		print '...connected to car controller service:', addr     # Print the IP address of the client connected with the server.

		lastCmd = ''

		while True:
				msgs = ''
				recdata = clientSocket.recv(BUFSIZ)
				# Receive data sent from the client. 
				# Analyze the command received and control the car accordingly.
				msgs = recdata.split(';')
				#print("Received", len(msgs), "new messages")
				for data in msgs:
					if not data:
						break
					
					if lastCmd == data:
						print("Last Command:", lastCmd, "Current Data:", data, "Ignoring")
						break

					if data == ctrl_cmd[0]:
						print 'motor moving forward'
						motor.forward()
					elif data == ctrl_cmd[1]:
						print 'recv backward cmd'
						motor.backward()
					elif data == ctrl_cmd[2]:
						print 'recv left cmd'
						car_dir.turn_left()
					elif data == ctrl_cmd[3]:
						print 'recv right cmd'
						car_dir.turn_right()
					elif data == ctrl_cmd[6]:
						print 'recv home cmd'
						car_dir.home()
					elif data == ctrl_cmd[4]:
						print 'recv stop cmd'
						motor.ctrl(0)
					elif data == ctrl_cmd[5]:
						print 'read cpu temp...'
						temp = cpu_temp.read()
						tcpCliSock.send('[%s] %0.2f' % (ctime(), temp))
					elif data[0:5] == 'speed':
						#print data
						numLen = len(data) - len('speed')
						if numLen == 1 or numLen == 2 or numLen == 3:
							tmp = data[-numLen:]
							#print 'tmp(str) = %s' % tmp
							spd = int(tmp)
							#print 'spd(int) = %d' % spd
							if spd < 24:
								spd = 24
							motor.setSpeed(spd)
					elif data[0:8] == 'network=':
						print 'network =', data
						spd = data.split('=')[1]
						try:
							spd = int(spd)
							os.system('sudo tc qdisc del dev wlan0 root')
							os.system('sudo tc qdisc add dev wlan0 root netem delay {0}ms'.format(spd))
						except:
							print 'ERROR , speed =', spd
					elif data[0:7] == 'offset=':
							#print 'offset called, data = ', data
							offset = int(data[7:]) + 28
							car_dir.calibrate(offset)
					elif data[0:8] == 'forward=':
						#print 'data =', data
						spd = data.split('=')[1]
						try:
							spd = int(spd)
							motor.setSpeed(spd)
							motor.forward()
						except:
							print 'Error speed =', spd
					elif data[0:9] == 'backward=':
						#print 'data =', data
						spd = data.split('=')[1]
						try:
							spd = int(spd)
							motor.setSpeed(spd)
							motor.backward()
						except:
							print 'ERROR , speed =', spd

					else:
						print 'Command Error! Cannot recognize command: ' + data

def LineSensor(socket):
	try:
		while True:
			print 'Waiting for connection to line sensor service...'
			# Waiting for connection. Once receiving a connection, the function accept() returns a separate 
			# client socket for the subsequent communication. By default, the function accept() is a blocking 
			# one, which means it is suspended before the connection comes.
			clientSocket, addr = socket.accept()
			print '...connected to line sensor service:', addr     # Print the IP address of the client connected with the server.
			start_time = datetime.now()
			next_time = datetime.now()
			lastCommand = ''
			while True:
				try:
					#print("Line Sensor Loop")
					score = line_follower.get_score()
					#print("Score:", score)
					if len(str(score)) > 0 and score != "None":
						#print("Score found, passing to score tests")
						pass
					else:
						#print("Score not found, continuing next iteration")
						continue
					
					if score == 1000 and lastCommand != '1000':
						try:
							print('Lap\n')
							clientSocket.send(str(score)+";")
							lastCommand = '1000'
							#print('Current Time', datetime.now())
							#print('Next Time: ', (datetime.now() + timedelta(milliseconds=250)))
							next_time = (datetime.now() + timedelta(milliseconds=250))
						except Exception as e:
							print(e)
							raise
					elif next_time < datetime.now() and score != -1:
						try:
							#print("Time to send new data", score)
							if score <= 7:
								lastCommand = score
								clientSocket.send(str(score)+";")
								next_time = (datetime.now() + timedelta(milliseconds=250))
						except Exception as e:
							print(e)
				except Exception as e:
					print(e)
	except Exception as e:
		print(e)


tcpSerSock = socket(AF_INET, SOCK_STREAM)    # Create a socket.
tcpSerSock.bind(ADDR)    # Bind the IP address and port number of the server. 
tcpSerSock.listen(5)     # The parameter of listen() defines the number of connections permitted at one time. Once the 
                         # connections are full, others will be rejected. 

lineSensorSock = socket(AF_INET, SOCK_STREAM)    # Create a socket.
lineSensorSock.bind(ADDR2)    # Bind the IP address and port number of the server. 
lineSensorSock.listen(5)     # The parameter of listen() defines the number of connections permitted at one time. Once the 
                         # connections are full, others will be rejected. 

t = Process(target=CarController, args=(tcpSerSock,))
t.daemon = True
t2 = Process(target=LineSensor, args=(lineSensorSock,))
t2.daemon = True

def main():
	t.start()
	t2.start()
	while True:
			time.sleep(.001)

if __name__ == '__main__':
	try:
		main()
	except (KeyboardInterrupt, SystemExit):
		pass
	finally:
		t.join()
		t2.join()
		print('closing tcpSocket')
		tcpSerSock.close()
		print('closing lineSocket')
		lineSensorSock.close()
		print('Sockets Closed')
		sys.exit(0)
		os._exit(0)
		
			