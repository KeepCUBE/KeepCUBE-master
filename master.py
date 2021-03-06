from termcolor import colored
import os
import datetime
import serial
import MySQLdb
import urllib2
import socket
import sys
import time
from multiprocessing import Process,Queue
from thread import *
from time import gmtime
from time import strftime
import threading
from threading import Thread

class tag:
    ok = "[ "+colored("OK","green")+" ] "
    info = "[ "+colored("INFO","yellow")+" ] "
    fail = "[ "+colored("FAIL","red")+" ] "
    warning = "[ \033[1;31mWARNING\033[0m ] "
    detect = "[ "+colored("DETECT","cyan")+" ] "

DBUpdate_cache = [None]*3

ser = serial.Serial(
        port='/dev/ttyUSB0',
        baudrate = 9600)

HOST = ''   # Symbolic name, meaning all available interfaces
PORT = 8888 # Arbitrary non-privileged port


db = MySQLdb.connect(host="localhost", user="root",passwd="kosticka", db="kc")
cur = db.cursor()
print tag.ok + "MySQL: connected"

peekedByte = None
peekingByte = None

def listGetInt(list):
        value = ""
        while True:
                byte = list.pop(0)
                if byte.isdigit():
                        value = str(value) + str(byte)
                else:
                        list.insert(0,byte)
                        break
        return value

def serialPeek():
        global peekedByte
        global peekingByte
        if peekedByte == None:
                peekingByte = ser.read(1)
                peekedByte = peekingByte
                return peekingByte
        else:
                return peekedByte

def serialRead():
        global peekedByte
        global peekingByte
        if peekedByte == None:
                return ser.read()
        else:
                peekedByte = None
                return peekingByte

def serialGetInt():
        value = ""
        while str(serialPeek()).isdigit() or serialPeek() == "-":
                value = str(value) + str(serialRead())
        return value

#_____________________data do atmega328_____________________

#__________data pres serial__________

def sendLocal(data):
        ser.write(data)

#__________ovladani switchu___________

def switchOn(switch_id):
        #db.commit()
        out = None
        cur.execute("SELECT on_code FROM switches WHERE switch_id = " + str(switch_id))
        out = cur.fetchone()
        if(out):
                print tag.info + "Sending request to turn switch ID " + str(switch_id) + " on, using code " + str(out[0]) + " ."
                sendLocal("#DBC;" + str(out[0]) + ";E")
        else:
                print "out: " + out
                print tag.fail + "NoneType exception: is the switch ID " + str(switch_id) + " really in a databse ?"


def switchOff(switch_id):
        #db.commit()
        out = None
        cur.execute("SELECT off_code FROM switches WHERE switch_id = " + str(switch_id))
        out = cur.fetchone()
        if(out):
                print tag.info + "Sending request to turn switch ID " + str(switch_id) + " off, using code " + str(out[0]) + " ."
                sendLocal("#DBC;" + str(out[0]) + ";E")
        else:
                 print tag.fail + "NoneType exception: is the switch ID " + str(switch_id) + " really in a databse ?"

#__________zmena barvy________________

def changeColor(address,r,g,b):
        sendLocal("#DCC" + str(address)  + str(r) + str(g) + str(b) + "E")
        print "change color to: " + r + g + b + " on address: " + address


#__________pozadavky__________________

def getLocalData(data):
        if data == "temp":
                sendLocal("#DST00E")
        elif data == "hum":
                sendLocal("#DSH00E")
        elif data == "pres":
                sendLocal("#DSP00E")



#____________________THREAD - TCP com______________________

def clientthread(conn):
    #Sending message to connected client
    conn.send('SRVCONF\n') #send only takes string
    conn.settimeout(10.0)
    try:
        data = conn.recv(7)
        if data != "CLNCONF":
                print tag.fail + "Wrong client verification !"
                sys.exit()
    except socket.timeout:
        print tag.fail + "Client verification not received !"
        sys.exit()
    conn.setblocking(1)
    print tag.ok + "Client connection stabilized"
    #infinite loop so that function do not terminate and thread do not end.
    while True:
        #Receiving from client
        data = conn.recv(1024)
        data = list(data)
        #___________receiving from app___________
        while  data:
                #print data
                if data.pop(0) == '#':
                        dsc = data.pop(0)
                        if dsc == 'D':
                                dsc = data.pop(0)
                                if dsc == 'T':
                                        dsc = data.pop(0)
                                        if dsc == 'S':
                                                switch_id = listGetInt(data)
                                                data.pop(0) #issue poping A (action) here, verify if it is actually there
                                                if data.pop(0) == '0': #issue command end(E) not verified
                                                        switchOff(switch_id)
                                                else:
                                                        switchOn(switch_id)
                                elif dsc == 'C':
                                        dsc = data.pop(0)
                                        if dsc == 'C':
                                                address = str(data.pop(0)) + str(data.pop(0))
                                                r = str(data.pop(0)) + str(data.pop(0))
                                                g = str(data.pop(0)) + str(data.pop(0))
                                                b = str(data.pop(0)) + str(data.pop(0))
                                                changeColor(address,r,g,b)
   #came out of loop
    conn.close()

#__________________THREAD - DB Update______________________

def updateDBThread():
        print tag.ok + "updateDBThread: started"
        global DBUpdate_cache
        while(1):
                time.sleep(2)
                DBUpdate_cache = [None]*3
                sendLocal("#DST00E")
                sendLocal("#DSH00E")
                sendLocal("#DSP00E")
                print tag.info + "updateDBThread: 3 DS requests sent"
                time.sleep(1)
                count = 0
                while (DBUpdate_cache[0] == None and DBUpdate_cache[1] == None and DBUpdate_cache[2] == None):
                        count = count + 1
                        if count >= 10:
                                break
                        time.sleep(1)
                if count < 10:
                        print ""
                        sql = ("""INSERT INTO sensor_readings (temperature, humidity, pressure) VALUES (%s,%s,%s)""",(DBUpdate_cache[0], DBUpdate_cache[1], DBUpdate_cache[2]))
                        cur.execute(*sql)
                        db.commit()
                        print tag.info + "updateDBThread: values inserted into the database (temp: " + DBUpdate_cache[0] + " hum: " +  DBUpdate_cache[1] + " press: " + DBUpdate_cache[2] + ")"
                else:
                        print tag.warning + "updateDBThread: entire respond NOT received after 10 attempts"
                time.sleep(20)

#_________________THREAD - Serial receive handling______________

def receiverThread():
        print tag.ok + "receiverThread(serial): started"
        global DBUpdate_cache
        while(1):
                if ser.inWaiting() > 0:
                        #print tag.detect + "receiverThread(serial): "+str(ser.inWaiting())+" incoming bytes detected"
                        #print tag.detect + "receriverThread(serial): received -> " + str(ser.read(ser.inWaiting()))
                        if serialPeek() == "#":
                                print tag.detect + "receiverThread(serial): incoming msg detected"
                                time.sleep(0.1)
                                serialRead()
                                if ser.inWaiting() > 0:
                                        oznaceni = serialRead()
                                        if(oznaceni == "R"):
                                                oznaceni = serialRead()
                                                if(oznaceni == "R"):
                                                        oznaceni = serialRead()
                                                        if(oznaceni == "T"):
                                                                DBUpdate_cache[0] = serialGetInt()
                                                        elif(oznaceni == "P"):
                                                                DBUpdate_cache[2] = serialGetInt()
                                                        elif(oznaceni == "H"):
                                                                DBUpdate_cache[1] = serialGetInt()
                                                        serialRead() #issue1, end (E) validation not handled
                        else:
                                serialRead()
                else:
                        time.sleep(1);


#_______________tady to zacina___________________________

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print tag.ok + 'Socket created'

#Try to bind socket to ip and port
try:
    s.bind((HOST, PORT))
except socket.error as msg:
    print tag.fail + 'Socket bind failed. Error : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()

s.listen(10)
print tag.ok + 'Socket now listening'

#Start receiving data from serial
p1 = Thread(target = receiverThread)
p1.start()

#Start updating DB every 10mins
p2 = Thread(target = updateDBThread)
#p2.start()

try:
        while 1:
                conn, addr = s.accept()
                print tag.ok + 'Connected with ' + addr[0] + ':' + str(addr[1])
                start_new_thread(clientthread ,(conn,))
        s.close()
except KeyboardInterrupt:
        print "   " + tag.fail + 'Keyboard interrupt'
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        print "socket closed"
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
