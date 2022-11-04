LEN_HEADER = 23
from  Message_Client_DB import *
import socket
from uuid_Generator import *
import struct
import threading



#constants
VER_LEN = 1
TYPE_LEN = 1
CODE_LEN = 2
SIZE_LEN = 4
NAME_LEN = 255
MSG_ID_LEN =4
PUBLIC_KEY_LEN = 160
UUID_LEN =16
TXT_HEADER_LEN = 21

ID_INDEX =0
TO_CLIENT_INDEX =1
FROM_CLIENT_INDEX =2
TYPE_INDEX =3
CONTENT_INDEX =4

VERSION = 2

#request codes
REGISTER_CODE = 1000
RECEIVE_LIST_CODE = 1001
PUBLIC_KEY_CODE = 1002
MSG_CODE = 1003
PULL_CODE = 1004

#answer codes
SUC_REGISTER = 2000
CLIENT_LIST = 2001
PUBLIC_REQ = 2002
REC_MSG = 2003
PULL_MSG= 2004
ERROR = 9000

#globals
mutex = threading.Lock()




def ResName(name):
    name = name.decode()
    index = name.find('\0')
    return name[:index].encode()

def packName(name):
    name = name.decode()
    ln = len(name)
    #pack name to 255byte bit array
    return (name + '\0' + (NAME_LEN - ln -1) * ' ').encode()



def convertBitArray(bitArray):
    i = 0
    for bit in bitArray:
        i = (i << 1) | bit

    return i



#defines a class for a recieved messaged format
class RecvMsg:
    def __init__(self, id, vers, code, size, msg):
        self.id = id
        self.version = vers
        self.code = code
        self.size = size
        self.msg = msg

#defines a class for a sent message format
class SentMsg:
    def __init__(self, vers, code, size, msg):
        self.version = vers
        self.code = code
        self.size = size
        self.msg = msg

    def toBitArr(self):
        bitVer = self.version.to_bytes(VER_LEN,"little")
        bitCode = self.code.to_bytes(CODE_LEN, "little")
        bitSize = self.size.to_bytes(SIZE_LEN, "little")
        bitMsg = self.msg


        return bitVer + bitCode + bitSize + bitMsg

class TxtMsg:
    def __init__(self, bitMsg):
        header = bitMsg[0:TXT_HEADER_LEN]

        id = header[:16]
        type = header[16:17]
        size = int.from_bytes(header[17:], "little")
        print(size)
        print(type)
        msg = bitMsg[TXT_HEADER_LEN:]


        self.id = id
        self.type = type
        self.size = size
        self.msg = msg


class PulledMsg:
    def __init__(self, cID, mID, type, size, msg):
        self.cID = cID
        self.mID = mID
        self.type = type
        self.size = size
        self.msg = msg

    def toBitArr(self):
        bitClientID = self.cID
        bitMsgID = self.mID.to_bytes(MSG_ID_LEN,"little")
        bitType = self.type
        print((self.type))
        bitSize = self.size.to_bytes(SIZE_LEN, "little")
        bitMsg = self.msg


        return bitClientID + bitMsgID + bitType+ bitSize + bitMsg





class Client:
    def __init__(self, sock):
        self.client = sock


    def recvMsg(self):
        header = self.client.recv(LEN_HEADER)

        id = header[:16]
        vers = int.from_bytes(header[16:17], "little")
        code =int.from_bytes(header[17:19], "little")
        size = int.from_bytes(header[19:], "little")
        print(size)
        print(code)
        print(vers)
        msg = self.client.recv(size)

        RMsg = RecvMsg(id, vers, code, size,msg)
        return RMsg


    def sendMsg(self, msg):
        self.client.send(msg.toBitArr())




    def handleMsg(self, ms):
        code = ms.code
        if code == REGISTER_CODE:
            self.register(ms)
        elif code == RECEIVE_LIST_CODE:
            self.clientList(ms)
        elif code == PUBLIC_KEY_CODE:
            self.getPrivateKey(ms)
        elif code == MSG_CODE:
            self.getTxtMsg(ms)
        elif code == PULL_CODE:
            self.pullMsgs(ms)



    def register(self, ms):
        curMsg = ms.msg
        name = ResName(curMsg[:NAME_LEN])
        publicKey = curMsg[NAME_LEN:]


        retID = ""

        #critical
        mutex.acquire()
        db = MessageUDB()

        if not db.Exists("name", name):
            retID = uuidGen()
            db.updateTime(retID)
            retMsg = SentMsg(VERSION, SUC_REGISTER, len(retID), retID)

            db.InsertClient(retID, name, publicKey)
        else:
            retMsg = SentMsg(VERSION, ERROR, 0, b"")
        db.close()
        #end critical
        mutex.release()

        self.sendMsg(retMsg)




    def clientList(self, ms):
        # critical
        mutex.acquire()
        logging.debug("start mutex section")
        db = MessageUDB()
        db.updateTime(ms.id)
        clients = db.retClients()
        db.close()
        logging.debug("end mutex section")
        # end critical
        mutex.release()

        bitClients = b''
        for clt in clients:
            bitName = packName(clt[1])
            bitID = clt[0]
            bitClients += bitID + bitName
        print(bitClients)
        retMsg = SentMsg(VERSION, CLIENT_LIST, len(bitClients), bitClients)
        self.sendMsg(retMsg)

    def getPrivateKey(self, ms):
        id = ms.msg

        # critical
        mutex.acquire()
        db = MessageUDB()
        db.updateTime(ms.id)
        pKey = db.getPublicKey(id)
        db.close()
        # end critical
        mutex.release()

        retMsg = SentMsg(VERSION, PUBLIC_REQ, len(id + pKey), id + pKey)
        self.sendMsg(retMsg)

    def getTxtMsg(self, ms):
        txtMsg = TxtMsg(ms.msg)



        # critical
        mutex.acquire()
        db = MessageUDB()
        db.updateTime(ms.id)
        msgID = db.InsertMessage(txtMsg.id, ms.id, txtMsg.type, txtMsg.msg)
        db.close()
        # end critical
        mutex.release()
        bitmsgID = msgID.to_bytes(MSG_ID_LEN, "little")

        retMsg = SentMsg(VERSION, REC_MSG, len(txtMsg.id + bitmsgID), txtMsg.id + bitmsgID )
        self.sendMsg(retMsg)


    def pullMsgs(self,ms):
        clientID = ms.id
        msgBitArr = b""


        # critical
        mutex.acquire()
        db = MessageUDB()
        db.updateTime(ms.id)
        msgList = db.getMsgByID(clientID)
        db.close()
        # end critical
        mutex.release()

        for m in msgList:
            curMsg = PulledMsg(m[FROM_CLIENT_INDEX], m[ID_INDEX], m[TYPE_INDEX], len(m[CONTENT_INDEX]), m[CONTENT_INDEX])
            msgBitArr += curMsg.toBitArr()

        retMsg = SentMsg(VERSION, PULL_MSG, len(msgBitArr), msgBitArr)
        self.sendMsg(retMsg)

        # critical
        mutex.acquire()
        db = MessageUDB()
        msgList = db.delMsgByID(clientID)
        db.close()
        # end critical
        mutex.release()






