import multiprocessing, requests, threading
import decimal
import random
import time
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation, rc

from socket import *
from time import ctime
from queue import Queue
from multiprocessing.dummy import Pool as ThreadPool
from threading import Thread
from datetime import datetime, timedelta

class WorkQueue:
    def __init__(self, threads=10):
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
        x.append(len(x))
        y.append(delta.total_seconds() * -1000)
        lock.release()
        if delta.total_seconds() > 0.01:
            #print('DelayTask.Process: Sleeping {0} milliseconds\n'.format(round(delta.total_seconds() * 1000)))
            time.sleep(delta.total_seconds())
            self.func(self.message)

            
        elif delta.total_seconds() < 0.01 and delta.total_seconds() > 0:
            #print('DelayTask.Process: Processing with {0} milliseconds remaining\n'.format(round(delta.total_seconds() * 1000)))
            self.func(self.message)
        else:
            #print("DelayTask.Process: Processing task: {0} milliseconds late\n".format(round(delta.total_seconds() * -1000)))
            self.func(self.message)
        return True
    
    def __str__(self):
        return str((self.func.__name__, self.time, self.message))

def send(msg):
    
    #print("Requesting {0}".format(url))
    #r = requests.get(url=url)
    tcpCliSock.send(str.encode(msg.decode()+';'))
    print("Sent message", msg.decode())
    #print("get(url): Received response for {0} with Status Code {1}".format(url, r.status_code))
    
aggregatorq = multiprocessing.Queue()

# First set up the figure, the axis, and the plot element we want to animate
fig = plt.figure()
ax = plt.axes(xlim=(0,2000), ylim = (0,1000))
line, = ax.plot([], [], lw=2)
plt.axhline(1000, color='black')
plt.axhline(2000, color='black')
plt.ylabel('Delayed in Milliseconds')
plt.xlabel('Processed Tasks')

# initialization function: plot the background of each frame
def init():
    line.set_data([], [])
    return line,

def animate(i):
    line.set_data(x[:i], y[:i])
    return line,

x = []
y = []

def collector():
    bucket = []
    while True:
        task = aggregatorq.get()
        #print("collector: aggregating Tasks\n")
        bucket.append(DelayedTask(task['func'], task['delay'], task['message']))
        bucket.sort(key=lambda x: x.time, reverse=False)
        queue = WorkQueue(10)
        queue.process(bucket)
        bucket.clear()
        
        #if(len(bucket) == 10):
            

HOST = ''           # The variable of HOST is null, so the function bind( ) can be bound to all valid addresses.
PORT = 23567
BUFSIZ = 1024       # Size of the buffer
ADDR = (HOST, PORT)

tcpSerSock = socket(AF_INET, SOCK_STREAM)    # Create a socket.
tcpSerSock.bind(ADDR)    # Bind the IP address and port number of the server. 
tcpSerSock.listen(5)     # The parameter of listen() defines the number of connections permitted at one time. Once the 
                         # connections are full, others will be rejected. 

DEBUG_APP = True
CAR_HOST = '192.168.1.240'    # Server(Raspberry Pi) IP address
CAR_PORT = 21567
CAR_BUFSIZ = 1024             # buffer size
CAR_ADDR = (CAR_HOST, CAR_PORT)

tcpCliSock = socket(AF_INET, SOCK_STREAM)   # Create a socket
tcpCliSock.connect(CAR_ADDR)

def controller():
    #print("Starting Controller\n")
    #finishtime = datetime.now() + timedelta(seconds=5)
    #print("controller: Will finish at {0}\n".format(finishtime))

    lastCmd = ''

    while True:
        #print('Waiting for connection...')
        tcpCliSock, addr = tcpSerSock.accept()
        #print('...connected from :', addr)

        while True:
            msgs = ''
            recdata = tcpCliSock.recv(BUFSIZ)

            msgs = recdata.split(b';')
		
            for data in msgs:
                if not data:
                    break
                if lastCmd == data:
                    break

                lastCmd = data
                print("Received Command", data)
                requestdelay = random.randint(1, 20)
                aggregatorq.put({'func': send, 'delay': requestdelay, 'message': data})
        
t = threading.Thread(target=controller)
t2 = threading.Thread(target=collector)

# call the animator.  blit=True means only re-draw the parts that have changed.
anim = animation.FuncAnimation(fig, animate, init_func=init, interval=1, blit=True)

def main():
    t.start()
    t2.start()
    plt.show()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        anim.event_source.stop()
        t.join()
        t2.join()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
