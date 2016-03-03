import socket
import threading
import sqlite3
import os
import urllib.parse

class Mensaje():
	def __init__(self,msg):
		s = 0
		pars = []
		data = []

		for l in msg.split("\n"):
			if s == 0:
				w = l.split(" ")
				self.method = w[0]
				self.resource = w[1]
				self.httpversion = w[2]
				s = 1
			elif s == 1:
				if len(l.replace("\r","")) == 0:
					s = 2
				else:
					pars.insert(len(pars),l.split(": "))
			elif s == 2:
				for w in l.split("&"):
					data.insert(len(data),w.split("="))
		self.data = data

def main():
	print("Creando servidor ["+socket.gethostname()+", puerto = 80]...")
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind(("localhost", 80))
	serversocket.listen(50)
	print("Esperando clientes...")
	while True:
		clientsocket, address = serversocket.accept()
		print("cliente " + str(address) + " conectado")
		threading.Thread(target = servircliente,args=(clientsocket))
		servircliente(clientsocket)

def responder(cliente,status,msg,content):
	content = "<html><head></head><body>"+content+"</body></html>"
	cliente.send(("HTTP/1.1 "+	str(status)+" "+msg+"\n\n"+content+"\n\n").encode("latin-1"))

def servircliente(cliente):
	msg = ""
	while True:
		try:
			msg = msg+cliente.recv(1).decode("latin-1")
			cliente.settimeout(0.1)
		except:
			break
	m = Mensaje(msg)

	print(m.method,m.resource,m.data)

	if m.method != 'POST':
		responder(cliente,405,"Method Not Allowed","Sólo se acepta POST")
	elif not m.resource.endswith("registro.php"):
		responder(cliente,404,"Not Found","	Recurso no encontrado")
	else:
		c = guardar(m.data[0][1],m.data[1][1],m.data[2][1],m.data[3][1],m.data[4][1])
		html = """
			<h1>Petición correcta</h1>
			<h2>Personas registradas</h2>
			<table>
				<tr>
					<th>Nombre</th>
					<th>Correo</th>
					<th>Password</th>
					<th>Género</th>
					<th>Escuela</th>
				</tr>"""
		for row in c.execute('select*from persona'):
			html = html +"""
				<tr>
					<td>"""+urllib.parse.unquote(row[0])+"""</td>
					<td>"""+row[1] +"""</td>
					<td>"""+row[2]+"""</td>
					<td>"""+row[3]+"""</td>
					<td>"""+row[4]+"""</td>
				</tr>
			"""
		html = html +"</table>"
		responder(cliente,200,"OK",html)
	cliente.close()

def guardar(nombre,correo,password,genero,escuela):
	conn = sqlite3.connect(os.path.dirname(os.path.abspath(__file__))+'/personas.db')
	c = conn.cursor()
	
	c.execute('''CREATE TABLE IF NOT EXISTS persona(nombre text, correo text, password text,genero text,escuela text)''')
	c.execute('INSERT INTO persona values(?,?,?,?,?)',(nombre,correo,password,genero,escuela))
	conn.commit()
	return c

if __name__ == '__main__':
	main()