from tornado import websocket, web, ioloop
import json

cl = []

class IndexHandler(web.RequestHandler):
    def get(self):
        self.render("index.html")

class SocketHandler(websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        if self not in cl:
            print(self)
            cl.append(self)

    def on_close(self):
        if self in cl:
            print("Cerrado"+str(self))
            cl.remove(self)

class ApiHandler(web.RequestHandler):

    @web.asynchronous
    def get(self, *args):
        self.finish()
        id = self.get_argument("id")
        value = self.get_argument("value")
        print("{} {}".format(id,value))
        data = {"id": id, "value" : value}
        data = json.dumps(data)
        for c in cl:
            c.write_message(data)

    @web.asynchronous
    def post(self):
        pass

class ProtectedTest(web.RequestHandler):
    def get(self):
        print("Entering protected...")
        argTest = self.get_argument("test","None")
        print(self.request.headers)
        print(argTest)
        #print(self.get_cookie("loginToken"))
        self.finish()



app = web.Application([
    (r'/', IndexHandler),
    (r'/ws', SocketHandler),
    (r'/api', ApiHandler),
    (r'/protected',ProtectedTest),
    (r'/(favicon.ico)', web.StaticFileHandler, {'path': '../'}),
    (r'/(rest_api_example.png)', web.StaticFileHandler, {'path': './'}),
])

if __name__ == '__main__':
    print("Starting...")
    app.listen(8888)
    ioloop.IOLoop.instance().start()
