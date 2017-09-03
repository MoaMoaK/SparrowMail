from sparrowmail import app

server_name = app.config['SERVER_NAME'].split(':')
host = server_name[0]
port = int(server_name[1])
app.run(host=host, port=port)
