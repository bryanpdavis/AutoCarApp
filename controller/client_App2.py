#!/usr/bin/env python
# -*- coding: utf-8 -*-
from tkinter import *
from socket import *      # Import necessary modules
import os
import pygame
import xbox360_controller

# top = Tk()   # Create a top window
# top.title('Raspberry Pi Smart Video Car Calibration')

ctrl_cmd = ['forward', 'backward', 'left', 'right', 'stop', 'read cpu_temp', 'home', 'distance', 'x+', 'x-', 'y+', 'y-', 'xy_home']

HOST = '192.168.1.240'    # Server(Raspberry Pi) IP address
PORT = 21567
BUFSIZ = 1024             # buffer size
ADDR = (HOST, PORT)

tcpCliSock = socket(AF_INET, SOCK_STREAM)   # Create a socket
tcpCliSock.connect(ADDR)                    # Connect with the server

# =============================================================================
# Get original offset configuration.
# =============================================================================


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

    def print(self, screen, textString):
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
# The function is to send the command forward to the server, so as to make the 
# car move forward.
# ============================================================================= 
def forward_fun(event):
	print('forward')
	tcpCliSock.send('forward')

def backward_fun(event):
	print('backward')
	tcpCliSock.send('backward')

def left_fun(event):
	print('left')
	tcpCliSock.send('left')

def right_fun(event):
	print('right')
	tcpCliSock.send('right')

def stop_fun(event):
	print('stop')
	tcpCliSock.send('stop')

def home_fun(event):
	print('home')
	tcpCliSock.send('home')

def x_increase(event):
	print('x+')
	tcpCliSock.send('x+')

def x_decrease(event):
	print('x-')
	tcpCliSock.send('x-')

def y_increase(event):
	print('y+')
	tcpCliSock.send('y+')

def y_decrease(event):
	print('y-')
	tcpCliSock.send('y-')

def xy_home(event):
	print('xy_home')
	tcpCliSock.send('xy_home')

# =============================================================================
# Exit the GUI program and close the network connection between the client 
# and server.
# =============================================================================
def quit_fun(event):
	top.quit()
	tcpCliSock.send('stop')
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

# Initialize the joysticks
pygame.joystick.init()

# Get ready to print
textPrint = TextPrint()

# =============================================================================
# Setup the Game Loop
# =============================================================================

done = False

my_controller = xbox360_controller.Controller(0)

while done==False:
    # Event processing
    for event in pygame.event.get():

        left_x, left_y = my_controller.get_left_stick()
        
        if event.type == pygame.QUIT:
            done = True
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == xbox360_controller.A:
                 tcpCliSock.send(b'forward')
        elif event.type == pygame.JOYBUTTONUP:
            if event.button == xbox360_controller.A:
                 tcpCliSock.send(b'stop')
        
        if int(round(left_x)) > 0:
            cmd = 'offset=' + str(int(left_x * 10))
            tcpCliSock.send(str.encode('right'))
        elif int(round(left_x)) < 0:
            cmd = 'offset=' + str(int(left_x * 10))
            tcpCliSock.send(str.encode('left'))
        else:
            tcpCliSock.send(b'home')
        
    # Drawing code
    screen.fill(BLACK)
    textPrint.reset()

    # Get count of joysticks
    joystick_count = pygame.joystick.get_count()

    textPrint.print(screen, "Number of joysticks: {}".format(joystick_count) )
    textPrint.indent()

    # For each joystick:
    for i in range(joystick_count):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()

        textPrint.print(screen, "Joystick {}".format(i) )
        textPrint.indent()

        # Get the name from the OS for the controller/joystick
        name = joystick.get_name()
        textPrint.print(screen, "Joystick name: {}".format(name) )

        # Usually axis run in pairs, up/down for one, and left/right for the other.
        axes = joystick.get_numaxes()
        textPrint.print(screen, "Number of axes: {}".format(axes) )
        textPrint.indent()

        for i in range( axes ):
            axis = joystick.get_axis( i )
            textPrint.print(screen, "Axis {} value: {:>6.3f}".format(i, axis) )
        textPrint.unindent()

        buttons = joystick.get_numbuttons()
        textPrint.print(screen, "Number of buttons: {}".format(buttons) )
        textPrint.indent()

        for i in range( buttons ):
            button = joystick.get_button( i )
            textPrint.print(screen, "Button {:>2} value: {}".format(i,button) )
        textPrint.unindent()

        # Hat switch. All or nothing for direction, not like joysticks.
        # Value comes back in a tuple.
        hats = joystick.get_numhats()
        textPrint.print(screen, "Number of hats: {}".format(hats) )
        textPrint.indent()

        for i in range( hats ):
            hat = joystick.get_hat( i )
            textPrint.print(screen, "Hat {} value: {}".format(i, str(hat)) )
        textPrint.unindent()

        textPrint.unindent()

    # Go ahead and update the screen with what we've drawn.
    pygame.display.flip()
    clock.tick(REFRESH_RATE)


pygame.quit ()
