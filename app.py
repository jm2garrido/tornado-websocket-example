from tornado import websocket, web, ioloop
import tornado.httpclient
import json

cl = []


hostOpenAM = "http://cloudfoundry.atosresearch.eu:8000/openam/"

class IndexHandler(web.RequestHandler):
    def get(self):
        client = tornado.httpclient.HTTPClient()
        URL = hostOpenAM+"json/authenticate"
        #print(URL)
        headers = { "X-OpenAM-Username":"pepe",
                    "X-OpenAM-Password":"12345678",
                    "Content-Type":"application/json"
                    }
        request = tornado.httpclient.HTTPRequest(URL,method="POST",body="{}",headers=headers)
        response = client.fetch(request)
        print("Headers:")
        print(response.headers)
        print("Body:")
        print(response.body)
        body = json.loads(response.body.decode("UTF-8"))
        tokenId = body["tokenId"]

        if not self.get_cookie("mycookie"):
            self.set_cookie("iPlanetDirectoryPro", tokenId)
            print("Setting the cookie")
        else:
            print("Not setting the cookie")
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

class Authorizator(web.RequestHandler):
    def get(self):
        print("Entering authorizator")
        argTest = self.get_argument("test","None")
        headers = self.request.headers
        print(self.request.headers)
        print(argTest)
        print(self.request.cookies)
        if(("TENGOPASE" in headers.get_list("X-Auth-Token"))
            or
           (self.get_cookie("iPlanetDirectoryPro","") == "TENGOPASE")           
           ):
            self.set_status(200)
            print("Entering...")
        else:
            self.set_status(401)
            print("Get lost")
        self.finish()



app = web.Application([
    (r'/', IndexHandler),
    (r'/ws', SocketHandler),
    (r'/api', ApiHandler),
    (r'/protected',ProtectedTest),
    (r'/auth',Authorizator),
    (r'/(favicon.ico)', web.StaticFileHandler, {'path': '../'}),
    (r'/(rest_api_example.png)', web.StaticFileHandler, {'path': './'}),
])

if __name__ == '__main__':
    print("Starting...")
    app.listen(8888)
    ioloop.IOLoop.instance().start()
