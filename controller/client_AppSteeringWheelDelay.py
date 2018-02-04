import multiprocessing, requests, threading
import decimal
import random
import time
import os
import pygame
import xbox360_controller
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation, rc
from socket import *    # Import necessary modules
from queue import Queue
from multiprocessing.dummy import Pool as ThreadPool
from threading import *
from datetime import datetime, timedelta

# =============================================================================
# Exit the GUI program and close the network connection between the client 
# and server.
# =============================================================================
def quit_fun(event):
	top.quit()
	tcpCliSock.send(b'stop')
	tcpCliSock.close()

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

class WorkQueue:
    def __init__(self, threads=6):
        self.threads = threads
        
    def process(self, work):
        pool = ThreadPool(self.threads)
        results = pool.map(DelayedTask.process, work)
        pool.close()
        pool.join()

class DelayedTask:
    def __init__(self, func, delay, message):
        #print("DelayTask.__init__: {0}".format((func.__name__, delay, message)))
        self.func = func
        self.time = datetime.now() + timedelta(milliseconds=delay)
        self.message = message

    def process(self):
        delta =  self.time - datetime.now()
        lock = threading.Lock()
        lock.acquire()
        #x.append(len(x))
        #y.append(delta.total_seconds() * -1000)
        lock.release()
        if delta.total_seconds() > 0.01:
            print('DelayTask.Process: Sleeping {0} milliseconds\n'.format(round(delta.total_seconds() * 1000)))
            time.sleep(delta.total_seconds())
            self.func(self.message)

            
        elif delta.total_seconds() < 0.01 and delta.total_seconds() > 0:
            print('DelayTask.Process: Processing with {0} milliseconds remaining\n'.format(round(delta.total_seconds() * 1000)))
            self.func(self.message)
        else:
            print("DelayTask.Process: Processing task: {0} milliseconds late\n".format(round(delta.total_seconds() * -1000)))
            self.func(self.message)
        return True
    
    def __str__(self):
        return str((self.func.__name__, self.time, self.message))

def send(msg):
        tcpCliSock.send(str.encode(msg+';'))

def get(url):
    
    #print("Requesting {0}".format(url))
    #r = requests.get(url=url)
    time.sleep(.002)
    #print("get(url): Received response for {0} with Status Code {1}".format(url, r.status_code))
    
aggregatorq = multiprocessing.Queue()

def collector():
    bucket = []
    while len(bucket) <= 2:
        task = aggregatorq.get()
        #print("collector: aggregating Tasks\n")
        bucket.append(DelayedTask(task['func'], task['delay'], task['message']))
        
        if(len(bucket) == 2):
            bucket.sort(key=lambda x: x.time, reverse=False)
            firsttask = bucket[0]
            firsttime =  firsttask.time - datetime.now()
            if firsttime.total_seconds() >= 0:
                #print('collector: Sleeping {0} seconds until first task in bucket\n'.format(firsttime.total_seconds()))
                time.sleep(firsttime.total_seconds())
            queue = WorkQueue(2)
            queue.process(bucket)
            bucket.clear()
# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

DEBUG_APP = True
HOST = '192.168.1.240'    # Server(Raspberry Pi) IP address
PORT = 21567
BUFSIZ = 1024             # buffer size
ADDR = (HOST, PORT)

requestdelay = random.randint(1, 20)

def controller():
    print("Starting Controller\n")
    print("Initializing Socket\n")
    tcpCliSock = socket(AF_INET, SOCK_STREAM)   # Create a socket
    tcpCliSock.connect(ADDR)

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

    while done==False:
        # Event processing          
        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                done = True
            
        steering = my_controller.joystick.get_axis(0)
        speed = my_controller.joystick.get_axis(1)
        forwardpaddle = my_controller.joystick.get_button(4)
        backwardpaddle = my_controller.joystick.get_button(5)

        if steering > 0.1:
            cmd = 'offset=+' + str(int(steering * 70.0))
            aggregatorq.put({'func': send, 'delay': requestdelay, 'message': cmd})
        elif steering < 0.1:
            cmd = 'offset=' + str(int(steering * 70.0))
            aggregatorq.put({'func': send, 'delay': requestdelay, 'message': cmd})
        else:
            aggregatorq.put({'func': send, 'delay': requestdelay, 'message': 'home'})
        
        if forwardpaddle == 1:
            direction = FORWARD
        elif backwardpaddle == 1:
            direction = BACKWARD

        if speed < -.01:
            spd = (speed * -100.0)
            cmd = ''
            if direction == FORWARD:
                cmd = 'forward=' + str(int(spd))
            elif direction == BACKWARD:
                cmd = 'backward=' + str(int(spd))
            aggregatorq.put({'func': send, 'delay': requestdelay, 'message': cmd})
            stopped = False
        elif speed > -.01 and stopped == False:
            stopped = True
            aggregatorq.put({'func': send, 'delay': requestdelay, 'message': cmd})
        
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
        
t = threading.Thread(target=controller)
t2 = threading.Thread(target=collector)

# initialization function: plot the background of each frame
def init():
    line.set_data([], [])
    return line,

def animate(i):
    line.set_data(x, y)
    return line,

x = []
y = []

# call the animator.  blit=True means only re-draw the parts that have changed.
#anim = animation.FuncAnimation(fig, animate, init_func=init, interval=1, blit=True)

def main():
    t.start()
    t2.start()
    plt.show()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        pygame.quit ()
        #anim.event_source.stop()
        t.join()
        t2.join()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
