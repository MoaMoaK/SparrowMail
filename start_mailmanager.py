from sparrowmail import app

server_name = app.config['SERVER_NAME']
if server_name :
    split_name = server_name.split(':')
    host = split_name[0]
    port = int(split_name[1])
    app.run(host=host, port=port)
else :
    app.run()
