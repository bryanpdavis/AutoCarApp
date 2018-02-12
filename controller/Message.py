from socket import *

# =============================================================================
# Message handling class
# =============================================================================

BUFSIZ = 2048

class Messenger:
	def __init__(self, address, debug=False):
		self.debug = debug
		print("Initializing Socket @", address)
		if not self.debug:
			tcpCliSock = socket(AF_INET, SOCK_STREAM)   # Create a socket
			tcpCliSock.connect(address)
			print('Connected...')
			self.clientSocket = tcpCliSock
        
	def send(self, message):
		#print("Sending message", message)
		try:
			if not self.debug:
				self.clientSocket.send(str.encode(message + ";"))
		except Exception as e:
			print("Error occurred", e)

		#print("Message sent: " + str(message))

	def receive(self, id):
		if not self.debug:
			recdata = self.clientSocket.recv(BUFSIZ)
			#print('received data', str(recdata), " for id: ", id)
			return recdata.decode()
		else:
			return "Debug"
	
	def close(self):
		self.clientSocket.close()