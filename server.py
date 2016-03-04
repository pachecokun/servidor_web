import socket
import threading
import sqlite3
import os
import urllib.parse

"""Clase para obtener la información de una petición"""
class Mensaje():
	"""Constructor: crea un nuevo objeto de tipo Mensaje
	a partir de una petición http"""
	def __init__(self,msg):
		s = 0
		pars = []
		data = []

		for l in msg.split("\n"): #separamos lineas
			if s == 0: #obtenemos datos de petición
				w = l.split(" ")
				self.method = w[0]
				self.resource = w[1]
				self.httpversion = w[2]
				s = 1
			elif s == 1: #obtenemos headers
				if len(l.replace("\r","")) == 0:
					s = 2
				else:
					pars.insert(len(pars),l.split(": "))
			elif s == 2: #obtenemos parametros POST
				for w in l.split("&"):
					data.insert(len(data),w.split("="))
		self.data = data

def main():
	print("Creando servidor ["+socket.gethostname()+", puerto = 80]...")
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind(("localhost", 80))
	serversocket.listen(50)
	print("Esperando clientes...")
	while True: #aceptamos clientes
		clientsocket, address = serversocket.accept()
		print("cliente " + str(address) + " conectado")
		threading.Thread(target = servircliente,args=(clientsocket))
		servircliente(clientsocket)

"""Envía al cliente una respuesta HTTP"""
def responder(cliente,status,msg,content):
	content = """
	<html>
		<head>
			<link rel="stylesheet" href="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css">
			<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.12.0/jquery.min.js"></script>
			<script src="http://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/js/bootstrap.min.js"></script>
		</head>
		<body style="background-image: url(https://appcyla.files.wordpress.com/2015/02/m1.jpg);color:#CCCCCC;">
			<div class="container">
				"""+content+"""
			</div>
		</body>
	</html>
	"""
	cliente.send(("HTTP/1.1 "+	str(status)+" "+msg+"\n\n"+content+"\n\n").encode("utf-8"))

"""Recibe y procesa una petición de un cliente"""
def servircliente(cliente):
	msg = ""
	while True: #Lee la petición
		try:
			msg = msg+cliente.recv(1).decode("latin-1")
			cliente.settimeout(0.1)
		except:
			break
	m = Mensaje(msg) #creamos objeto Mensaje a partir de texto recibido

	print(m.method,m.resource,m.data)

	if m.method != 'POST': #Verificamos método
		responder(cliente,405,"Method Not Allowed","""<div class="alert alert-danger"><strong>Error 405: </strong>Sólo se acepta método POST</div>""")
	elif not m.resource.endswith("registro.php"): #verificamos recurso solicitado
		responder(cliente,404,"Not Found","""<div class="alert alert-danger"><strong>Error 404: </strong>Recurso no encontrado</div>""")
	else:
		errores = "" #validamos campos
		if len(m.data)<5:
			errores = errores+"<strong>Error: </strong>Debe seleccionar un género<br>"
		if len(m.data[0][1])== 0:
			errores = errores+"<strong>Error: </strong>El campo nombre es obligatorio<br>"
		if len(m.data[1][1])== 0:
			errores = errores+"<strong>Error: </strong>El campo correo es obligatorio<br>"
		if len(m.data[2][1])== 0:
			errores = errores+"<strong>Error: </strong>El campo password es obligatorio<br>"

		if len(errores)>0: #si hay errores, los notifica
			errores = """<div class="alert alert-danger">"""+errores+"""</div>"""
			responder(cliente,200,"OK",errores)
		else: #si no hay errores se guarda un nuevo registro
			c = guardar(m.data[0][1],m.data[1][1],m.data[2][1],m.data[3][1],m.data[4][1])
			#respondemos con una página de confirmación
			html = """
				<h1>Petición correcta</h1>
				<h2>Personas registradas</h2>
				<table class="table">
					<tr>
						<th>Nombre</th>
						<th>Correo</th>
						<th>Password</th>
						<th>Género</th>
						<th>Escuela</th>
					</tr>"""
			for row in c.execute('select*from persona'): #mostramos los usuarios registrados
				html = html +"""
					<tr>
						<td>"""+row[0].replace("+"," ")+"""</td>
						<td>"""+row[1] +"""</td>
						<td>"""+row[2]+"""</td>
						<td>"""+row[3]+"""</td>
						<td>"""+row[4]+"""</td>
					</tr>
				"""
			html = html +"</table>"
			responder(cliente,200,"OK",urllib.parse.unquote(html))
	cliente.close() #cerramos conexión

"""Guarda una persona en la base de datos"""
def guardar(nombre,correo,password,genero,escuela):
	conn = sqlite3.connect(os.path.dirname(os.path.abspath(__file__))+'/personas.db') #abrimos archivo de BD
	c = conn.cursor()

	c.execute('''CREATE TABLE IF NOT EXISTS persona(nombre text, correo text, password text,genero text,escuela text)''') #creamos BD si no existe
	c.execute('INSERT INTO persona values(?,?,?,?,?)',(nombre,correo,password,genero,escuela)) #Guardamos registro
	conn.commit() #guardamos cambios en BD
	return c

if __name__ == '__main__':
	main()
