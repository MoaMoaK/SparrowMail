from sparrowmail import app

server_host = app.config['SERVER_HOST']
server_port = app.config['SERVER_PORT']

if server_name :
    if server_port :
        app.run(host=server_host, port=server_port)
    else :
        app.run(host=server_host)
else :
    if server_port :
        app.run(port=server_port)
    else :
        app.run()
