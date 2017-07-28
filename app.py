from tornado import websocket, web, ioloop
import tornado.httpclient
import json

cl = []


hostOpenAM = "http://cloudfoundry.atosresearch.eu:8000/openam/"


def checkKey(testKey):
    client = tornado.httpclient.HTTPClient()
    URL = hostOpenAM+"json/users?_action=idFromSession"
    headers = { "iPlanetDirectoryPro":testKey,
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
        return False
    except Exception as e:
        # Other errors are possible, such as IOError.
        print("General error: " + str(e))
        return False
    finally:
        client.close()
    return True

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


class IndexHandler(web.RequestHandler):
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

class Login(web.RequestHandler):
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

        keyList = headers.get_list("X-Auth-Token")
        keyList.append(self.get_cookie("iPlanetDirectoryPro",None))

        for key in keyList:
            print("key :{}")
            if checkKey(key):
                # there is a valid key
                print("Valid!!")
                self.set_status(200)
                break
        else:
            #if we are, all the keys are invalid
            print("Not valid!!")
            self.set_status(401)

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
