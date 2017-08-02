from tornado import websocket, ioloop
import tornado.httpclient
import tornado.gen
import tornado.web
import json

cl = []


hostOpenAM = "http://cloudfoundry.atosresearch.eu:8000/openam/"
hostCache = "http://localhost/openam/"

@tornado.gen.coroutine
def checkKey(testKey):
    #client = tornado.httpclient.HTTPClient()
    client = tornado.httpclient.AsyncHTTPClient()
    #URL = hostOpenAM+"json/users?_action=idFromSession"
    URL = hostCache+"json/users?_action=idFromSession"
    headers = { "iPlanetDirectoryPro":testKey,
                "Content-Type":"application/json"
              }
    request = tornado.httpclient.HTTPRequest(URL,method="POST",body="{}",headers=headers)
    try:
        response = yield client.fetch(request)
        #print("Headers:")
        #print(response.headers)
        #print("Body:")
        #print(response.body)
        body = json.loads(response.body.decode("UTF-8"))
    except tornado.httpclient.HTTPError as e:
        # HTTPError is raised for non-200 responses; the response
        # can be found in e.response.
        if e.response.code == 401:
            print("Unauthorized")    
        else:
            print("Error: " + str(e))
        #return False
        raise tornado.gen.Return(False)
    except Exception as e:
        # Other errors are possible, such as IOError.
        print("General error: " + str(e))
        raise tornado.gen.Return(False)
    #if we are here, the return code is 200, it is valid
    print("Valid")
    raise tornado.gen.Return(True)

def login(user,password):
    client = tornado.httpclient.HTTPClient()
    URL = hostOpenAM+"json/authenticate"
    #print(URL)
    headers = { "X-OpenAM-Username":user,
                "X-OpenAM-Password":password,
                "Content-Type":"application/json"
                }
    request = tornado.httpclient.HTTPRequest(URL,method="POST",body="{}",headers=headers)
    try:
        response = client.fetch(request)
        #print("Headers:")
        #print(response.headers)
        #print("Body:")
        #print(response.body)
        body = json.loads(response.body.decode("UTF-8"))
        
    except tornado.httpclient.HTTPError as e:
        # HTTPError is raised for non-200 responses; the response
        # can be found in e.response.
        if e.response.code == 401:
            print("Unauthorized")    
        else:
            print("Error: " + str(e))
        return None
    except Exception as e:
        # Other errors are possible, such as IOError.
        print("General error: " + str(e))
        return None
    finally:
        client.close()
        
    tokenId = body["tokenId"]
    return tokenId


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        tokenId = login("pepe","12345678")

        if tokenId:
            if not self.get_cookie("mycookie"):
                self.set_cookie("iPlanetDirectoryPro", tokenId)
                print("Setting the cookie")
            else:
                print("Not setting the cookie")
        else:
            print("Login worked bad")
        self.render("index.html")

class Login(tornado.web.RequestHandler):
    def get(self):
        user = self.get_argument("user",None)
        password = self.get_argument("pass", None)

        if not(user and password):
            self.set_status(401)
            self.finish()    
            return

        tokenId = login(user, password)
        # preparing the answer
        if tokenId:
            answer = { "tokenId":tokenId }
            self.write_message(answer)
        else:
            self.set_status(401)
        self.finish()


    def post(self):
        get(self)

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

class ApiHandler(tornado.web.RequestHandler):

    @tornado.web.asynchronous
    def get(self, *args):
        self.finish()
        id = self.get_argument("id")
        value = self.get_argument("value")
        print("{} {}".format(id,value))
        data = {"id": id, "value" : value}
        data = json.dumps(data)
        for c in cl:
            c.write_message(data)

    @tornado.web.asynchronous
    def post(self):
        pass

class ProtectedTest(tornado.web.RequestHandler):
    def get(self):
        print("Entering protected...")
        argTest = self.get_argument("test","None")
        print(self.request.headers)
        print(argTest)
        #print(self.get_cookie("loginToken"))
        self.finish()

class Authorizator(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        print("Entering authorizator")
        argTest = self.get_argument("test","None")
        headers = self.request.headers
        print(self.request.headers)
        print(argTest)
        print(self.request.cookies)

        keyList = headers.get_list("X-Auth-Token")
        keyList.append(self.get_cookie("iPlanetDirectoryPro",None))

        for key in keyList:
            print("key :{}".format(key))
            checked = yield checkKey(key)
            if checked:
                # there is a valid key
                print("Valid!!")
                self.set_status(200)
                break
        else:
            #if we are, all the keys are invalid
            print("Not valid!!")
            self.set_status(401)

        self.finish()


app = tornado.web.Application([
    (r'/', IndexHandler),
    (r'/ws', SocketHandler),
    (r'/api', ApiHandler),
    (r'/protected',ProtectedTest),
    (r'/auth',Authorizator),
    (r'/(favicon.ico)', tornado.web.StaticFileHandler, {'path': '../'}),
    (r'/(rest_api_example.png)', tornado.web.StaticFileHandler, {'path': './'}),
])

if __name__ == '__main__':
    print("Starting...")
    app.listen(8888)
    ioloop.IOLoop.instance().start()
