import struct
import random
import math
import time

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor
from twisted.internet import task
from twisted.web import static, server
from autobahn.websocket import WebSocketServerFactory, WebSocketServerProtocol, listenWS


class BinaryStream:
    def __init__(self):
        self.byte_struct = struct.Struct("!b")
        self.ubyte_struct = struct.Struct("!B")
        self.int_struct = struct.Struct("!i")
        self.short_struct = struct.Struct("!h")

    def put_data(self, data):
        self.data = data
        self.len_data = len(data)
        self.pos = 0

    def read_data_left(self):
        return self.data[self.pos:]

    def read_byte(self):
        size = 1
        byte = self.data[self.pos:self.pos + size]
        byte, = self.byte_struct.unpack(byte)
        self.pos += size
        return byte

    def read_ubyte(self):
        size = 1
        byte = self.data[self.pos:self.pos + size]
        byte, = self.ubyte_struct.unpack(byte)
        self.pos += size
        return byte

    def read_int(self):
        size = 4
        _int = self.data[self.pos:self.pos + size]
        _int, = self.int_struct.unpack(_int)
        self.pos += size
        return _int

    def read_short(self):
        size = 2
        short = self.data[self.pos:self.pos + size]
        short, = self.short_struct.unpack(short)
        self.pos += size
        return short

    def read_UTF(self):
        print "UTF", repr(self.data)
        size = 2
        length = self.data[self.pos:self.pos + size]
        length, = self.short_struct.unpack(length)
        self.pos += size
        string = self.data[self.pos:self.pos + length]
        string, = struct.unpack("!" + str(length) + "s", string)
        self.pos += length
        return string

    def working(self):
        if self.pos == self.len_data:
            return False
        else:
            return True

bs = BinaryStream()


connections = []


def read_policy():
    with file("crossdomain.xml", 'rb') as f:
        policy = f.read(10001)
        print "policy", policy
        return policy


def broadcast(msg):
    for connection in connections:
        connection.send_message(msg)


class Sender:  # Ugly
    def __init__(self):
        self.pending_msgs = ""

    def send(self, msg):
        self.pending_msgs += msg


class DefaultConnection:
    bs = bs
    broadcast = broadcast
    connections = connections  # Super ugly !

    def connectionMade(self):
        connections.append(self)
        self.on_connection()

    def connectionLost(self, reason):
        connections.remove(self)
        self.on_close(reason)

    def dataReceived(self, msg):
        # print "msg", repr(msg)
        if msg == '<policy-file-request/>\0':
            print "POLIIIIIIIIIIIICE"
            self.transport.write(read_policy() + "\0")
        self.on_message(msg)

    ###

    def send_now(self, msg):  # Todo : Rename send_now ?wtf?
        # print "sending", repr(msg)
        self.transport.write(msg)


class WSConnection:
    bs = bs
    broadcast = broadcast
    connections = connections

    def onOpen(self):
        print "Connected on WS"
        connections.append(self)
        self.on_connection()

    def connectionLost(self, reason):
        connections.remove(self)
        self.on_close(reason)

    def onMessage(self, msg, binary):
        # print "WS MESSAGE > ", msg
        self.on_message(msg)

    ###

    def send_now(self, msg):
        self.sendMessage(msg, True)


class Manager:
    def __init__(self, appmanager, apprate, netrate):
        self.appmanager = appmanager
        self.l = task.LoopingCall(self.netloop)
        self.l.start(netrate)

        self.l = task.LoopingCall(self.apploop)
        self.l.start(apprate)

    def apploop(self):
        self.appmanager.update()

    def netloop(self):
        self.appmanager.net_update()
        for connection in connections:
            connection.send_now(connection.pending_msgs)
            connection.pending_msgs = ""


def start_server(port, appmanager, protocol, apprate, netrate):
    port = 9999
    manager = Manager(appmanager, apprate, netrate)  # TODO remove manager = ?

    DefaultConnection.__bases__ += (Protocol, protocol, Sender)  # WTF inheritance
    echofactory = Factory()
    echofactory.protocol = DefaultConnection
    reactor.listenTCP(port, echofactory)
    # WEBSOOOOOCKKEEEET
    WSConnection.__bases__ += (WebSocketServerProtocol, protocol, Sender)
    factory = WebSocketServerFactory("ws://localhost:" + str(port + 1))
    factory.protocol = WSConnection
    listenWS(factory)
    print "Server initialized"
    reactor.run()
