#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tkinter import *
from socket import *
from threading import *     # Import necessary modules
import os
import pygame
import xbox360_controller
import time

# top = Tk()   # Create a top window
# top.title('Raspberry Pi Smart Video Car Calibration')

ctrl_cmd = ['forward', 'backward', 'left', 'right', 'stop', 'read cpu_temp', 'home', 'distance', 'x+', 'x-', 'y+', 'y-', 'xy_home']
DEBUG_APP = True
HOST = '192.168.1.240'    # Server(Raspberry Pi) IP address
PORT = 21567
BUFSIZ = 1024             # buffer size
ADDR = (HOST, PORT)

tcpCliSock = socket(AF_INET, SOCK_STREAM)   # Create a socket
tcpCliSock.connect(ADDR)                    # Connect with the server

#Testing
# =============================================================================
# Get original offset configuration.
# =============================================================================

class Message:
    def send(self, msg):
        tcpCliSock.send(str.encode(msg+';'))

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# This is a simple class that will help us print to the screen
# It has nothing to do with the joysticks, just outputing the
# information.
class TextPrint:
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 30)

    def printText(self, screen, textString):
        textBitmap = self.font.render(textString, True, WHITE)
        screen.blit(textBitmap, [self.x, self.y])
        self.y += self.line_height

    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 30

    def indent(self):
        self.x += 20

    def unindent(self):
        self.x -= 20

# =============================================================================
# Exit the GUI program and close the network connection between the client 
# and server.
# =============================================================================
def quit_fun(event):
	top.quit()
	tcpCliSock.send(b'stop')
	tcpCliSock.close()

# =============================================================================
# Setup the Pygame
# =============================================================================

pygame.init()

size = [500, 800]
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Joystick Tester")
REFRESH_RATE = 20

# Used to manage how fast the screen updates
clock = pygame.time.Clock()

# Setup mixer for playing sounds
#pygame.mixer.init()
#pygame.mixer.music.load(file)

# Initialize the joysticks
pygame.joystick.init()

# Get ready to print
textPrint = TextPrint()

# =============================================================================
# Setup the Game Loop
# =============================================================================

done = False
FORWARD = 1
BACKWARD = -1
my_controller = xbox360_controller.Controller(0)
message = Message()
stopped = True
direction = FORWARD
DELAY = 0.0;

networklatency = 0
network_can_go_up = True
network_can_go_down = True
current_steering = 0

cmd = 'network=' + str(networklatency)
message.send(cmd)

while done==False:
    # Event processing
    for event in pygame.event.get():
        
        if event.type == pygame.QUIT:
            done = True
        
    steering = my_controller.joystick.get_axis(0)

    if current_steering != steering:
        current_steering = steering
        if steering > 0.1:
            cmd = 'offset=+' + str(int(steering * 70.0))
            message.send(cmd)
        elif steering < 0.1:
            cmd = 'offset=' + str(int(steering * 70.0))
            message.send(cmd)
        else:
            message.send('home')

    networkup = my_controller.joystick.get_button(11)
    networkdown = my_controller.joystick.get_button(10)
    
    if networkup == 0:
        network_can_go_up = True
    
    if networkdown == 0:
        network_can_go_down = True

    if networkup == 1 and network_can_go_up:
        network_can_go_up = False
        networklatency = networklatency + 10
        cmd = 'network=' + str(networklatency)
        print("Network latency set to ", networklatency)
        message.send(cmd)
    elif networkdown == 1 and network_can_go_down:
        network_can_go_down = False
        if networklatency > 0:
            networklatency = networklatency - 10
            print("Network latency set to ", networklatency)

        cmd = 'network=' + str(networklatency)
        message.send(cmd)

    forwardpaddle = my_controller.joystick.get_button(4)
    backwardpaddle = my_controller.joystick.get_button(5)

    if forwardpaddle == 1:
        direction = FORWARD
    elif backwardpaddle == 1:
        direction = BACKWARD
    
    speed = my_controller.joystick.get_axis(1)
    
    if speed < -.01:
        spd = (speed * -100.0)
        cmd = ''
        if direction == FORWARD:
            cmd = 'forward=' + str(int(spd))
            print("Forward", "Speed set to", cmd)
        elif direction == BACKWARD:
            cmd = 'backward=' + str(int(spd))
            print("Backward", "Speed set to", cmd)
        message.send(cmd)
        stopped = False
    elif speed > -.01 and stopped == False:
        stopped = True
        message.send('stop')
    
    #Drawing code
    textPrint.reset()
    screen.fill(BLACK);

    if DEBUG_APP == True:
        # Get count of joysticks
        joystick_count = pygame.joystick.get_count()

        textPrint.printText(screen, "Number of joysticks: {}".format(joystick_count) )
        textPrint.indent()

        #For each joystick:
        for i in range(joystick_count):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()

            textPrint.printText(screen, "Joystick {}".format(i) )
            textPrint.indent()

        # Get the name from the OS for the controller/joystick
            name = joystick.get_name()
            textPrint.printText(screen, "Joystick name: {}".format(name) )

        # Usually axis run in pairs, up/down for one, and left/right for the other.
            axes = joystick.get_numaxes()
            textPrint.printText(screen, "Number of axes: {}".format(axes) )
            textPrint.indent()

            for i in range( axes ):
                axis = joystick.get_axis( i )
                textPrint.printText(screen, "Axis {} value: {:>6.3f}".format(i, axis) )
            textPrint.unindent()

            buttons = joystick.get_numbuttons()
            textPrint.printText(screen, "Number of buttons: {}".format(buttons) )
            textPrint.indent()

            for i in range( buttons ):
                button = joystick.get_button( i )
                textPrint.printText(screen, "Button {:>2} value: {}".format(i,button) )
            textPrint.unindent()

        # Hat switch. All or nothing for direction, not like joysticks.
        # Value comes back in a tuple.
            hats = joystick.get_numhats()
            textPrint.printText(screen, "Number of hats: {}".format(hats) )
            textPrint.indent()

            for i in range( hats ):
                hat = joystick.get_hat( i )
                textPrint.printText(screen, "Hat {} value: {}".format(i, str(hat)) )
            textPrint.unindent()

            textPrint.unindent()

    # Go ahead and update the screen with what we've drawn.
    pygame.display.flip()
    clock.tick(REFRESH_RATE)


pygame.quit ()
