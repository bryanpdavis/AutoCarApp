#!/usr/bin/env python
import RPi.GPIO as GPIO
import video_dir
import car_dir
import motor
import os

from socket import *
from time import ctime          # Import necessary modules   

ctrl_cmd = ['forward', 'backward', 'left', 'right', 'stop', 'read cpu_temp', 'home', 'distance', 'x+', 'x-', 'y+', 'y-', 'xy_home']

busnum = 1          # Edit busnum to 0, if you uses Raspberry Pi 1 or 0

HOST = ''           # The variable of HOST is null, so the function bind( ) can be bound to all valid addresses.
PORT = 21567
BUFSIZ = 1024       # Size of the buffer
ADDR = (HOST, PORT)

tcpSerSock = socket(AF_INET, SOCK_STREAM)    # Create a socket.
tcpSerSock.bind(ADDR)    # Bind the IP address and port number of the server. 
tcpSerSock.listen(5)     # The parameter of listen() defines the number of connections permitted at one time. Once the 
                         # connections are full, others will be rejected. 

video_dir.setup(busnum=busnum)
car_dir.setup(busnum=busnum)
motor.setup(busnum=busnum)     # Initialize the Raspberry Pi GPIO connected to the DC motor. 
video_dir.home_x_y()
car_dir.home()
#change test

while True:
	print 'Waiting for connection...'
	# Waiting for connection. Once receiving a connection, the function accept() returns a separate 
	# client socket for the subsequent communication. By default, the function accept() is a blocking 
	# one, which means it is suspended before the connection comes.
	tcpCliSock, addr = tcpSerSock.accept() 
	print '...connected from :', addr     # Print the IP address of the client connected with the server.
	
	lastCmd = ''

	while True:
		msgs = ''
		recdata = tcpCliSock.recv(BUFSIZ)    # Receive data sent from the client. 
		# Analyze the command received and control the car accordingly.
		msgs = recdata.split(';')
		
		for data in msgs:
			if not data:
				break
			if lastCmd == data:
				break

			lastCmd = data
			if data == ctrl_cmd[6]:
				print 'recv home cmd'
				car_dir.home()
			elif data == ctrl_cmd[4]:
				print 'recv stop cmd'
				motor.ctrl(0)
			elif data == ctrl_cmd[5]:
				print 'read cpu temp...'
				temp = cpu_temp.read()
				tcpCliSock.send('[%s] %0.2f' % (ctime(), temp))
			elif data[0:5] == 'speed':     # Change the speed
				print data
				numLen = len(data) - len('speed')
				if numLen == 1 or numLen == 2 or numLen == 3:
					tmp = data[-numLen:]
					print 'tmp(str) = %s' % tmp
					spd = int(tmp)
					print 'spd(int) = %d' % spd
					if spd < 24:
						spd = 24
					motor.setSpeed(spd)
			elif data[0:7] == 'offset=':
				print 'offset called, data = ', data
				offset = int(data[7:]) + 28
				car_dir.calibrate(offset)
			elif data[0:8] == 'forward=':
				print 'data =', data
				spd = data.split('=')[1]
				try:
					spd = int(spd)
					motor.setSpeed(spd)
					motor.forward()
				except:
					print 'Error speed =', spd
			elif data[0:9] == 'backward=':
				print 'data =', data
				spd = data.split('=')[1]
				try:
					spd = int(spd)
					motor.setSpeed(spd)
					motor.backward()
				except:
					print 'ERROR , speed =', spd
			elif data[0:8] == 'network=':
    				print 'data =', data
				spd = data.split('=')[1]
				try:
					spd = int(spd)
					os.system('sudo tc qdisc del dev wlan0 root')
					os.system('sudo tc qdisc add dev wlan0 root netem delay {0}ms'.format(spd))
				except:
					print 'ERROR , speed =', spd

			else:
				print 'Command Error! Cannot recognize command: ' + data

tcpSerSock.close()


