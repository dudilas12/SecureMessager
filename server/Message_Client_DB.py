import sqlite3
from datetime import datetime
import logging

#intiallize logging format
FORMAT = "%(filename)s: in line %(lineno)d\n%(message)s"
logging.basicConfig(filename='Debug.log', filemode= "w", level=logging.DEBUG
                    , format= FORMAT)
ID_POS = 0
NAME_POS = 1
PK_POS = 2
#class for implementing the data base
class MessageUDB:
    def __init__(self):
        """
        object intiallizer
        creates the tables if not already created
        """
        self.conn = sqlite3.connect('server.db')
        self.conn.text_factory = bytes
        try:

            self.conn.execute('''CREATE TABLE clients
                                 (ID TEXT PRIMARY KEY     NOT NULL,
                                 name          TEXT    NOT NULL,
                                 public_key           TEXT     NOT NULL,
                                 LastSeen TEXT);''')

            self.conn.execute('''CREATE TABLE messages
                                 (ID INTEGER PRIMARY KEY  AUTOINCREMENT,
                                 ToClient  TEXT        TEXT    NOT NULL,
                                 FromClient TEXT    NOT NULL,
                                 Type char(1),
                                 Content Blob);''')
        except:
            pass
            logging.debug("error in creating tables")
            #Handle the situation of already existing table


    def InsertMessage(self, IDTO, IDFROM, Type, Content ):
        """
        Inserting new Message into data base

        raises an error if error detected
        """

        #intiallizing the current date as Last Seen
        LastSeen = datetime.today().strftime("")

        try:
            #exectuting Insert
            self.conn.execute("""Insert Into messages(ToClient, FromClient, Type, Content) Values
            (?,?,?,?)
            """, [IDTO, IDFROM, Type, Content])
            self.conn.commit()

            cur = self.conn.cursor()

            querry = """SELECT ID From messages
                        WHERE ID >= (SELECT ID From messages)
                        
            """
            cur.execute(querry)
            return cur.fetchall()[0][0]

        except:
            #handeling error situation
            raise

    def InsertClient(self, ID, Name, PublicKey):
        """
        Inserting new Client into data base
        inserting the current date as Last seen

        raises an error if clone ID detected
        """

        # intiallizing the current date as Last Seen
        LastSeen = datetime.today().strftime("")

        try:
            # exectuting Insert
            print("data base")
            self.conn.execute("""Insert Into clients Values
            (?,?,?,datetime('now'))
            """, [ID, Name, PublicKey])
            self.conn.commit()

        except:
            # handeling clone situation
            logging.error("ID already exists")
            raise

    def getPublicKey(self, id):
        cur = self.conn.cursor()

        querry = f"SELECT * From clients"
        cur.execute(querry)
        for i in cur.fetchall():
            if id == i[ID_POS]:
                return i[PK_POS]
        return b''


    def Exists(self, attr, value):
        cur = self.conn.cursor()
        try:
            querry = f"SELECT {attr} From clients"
            cur.execute(querry)
            print(value)
            for i in cur.fetchall():
                if value in i:
                    return True
            return False
        except:
            logging.debug("wrong attribute")
            return False

    def getMsgByID(self,id):
        cur = self.conn.cursor()


        cur.execute("""SELECT * From messages
                                WHERE ToClient >= ?

                    """, [id])

        return cur.fetchall()



    def delMsgByID(self, ID):
        self.conn.execute("Delete From messages Where ToClient = ?",[ID])
        self.conn.commit()


    def updateTime(self, ID):
        self.conn.execute("Update clients Set LastSeen = datetime('now')  Where ID = ?",[ID])
        self.conn.commit()


    def showClients(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * from clients")
        print(cur.fetchall())

    def showMessages(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * from messages")
        print(cur.fetchall())

    def retClients(self):
        cur = self.conn.cursor()
        cur.execute("SELECT ID, Name from clients")
        return (cur.fetchall())

    def retMessages(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * from messages")
        return (cur.fetchall())

    def close(self):
        self.conn.close()



MessageUDB()