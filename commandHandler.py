from termcolor import colored
import re
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

print tag.ok + "Process started."

# SAMPLE VARIABLES
commands = ["#DTSC123456789E", "#DTSC123456E", "#DCCI01CabcdefE", "#HOAX", "#COOKIE"]

# DB CONNECTION
db = MySQLdb.connect(host="localhost", user="root",passwd="kosticka", db="kc")
cur = db.cursor()
print tag.ok + "MySQL connected successfully."

# FUNCTIONS
def commandValid(command):
    "This function validates command, that means that command starts with '#' and ends with 'E'."
    print tag.info + "Validating command. "
    return(True if command.startswith('#') and command.endswith('E') else False)

def getCommandInfo(command):
    print tag.info + "Searching for command in DB."
    cur.execute("SELECT * FROM dsc_dictionary WHERE head = '"+command[1] + command[2] + command[3]+"'")
    return cur.fetchone()


# MAIN ROUTINE
for command in commands:
    print tag.info + "Processing command " + command
    if not commandValid(command):
        print tag.warning + "Command not valid. Skipping."
        continue
    else:
        print tag.ok + "Command valid."
        commandInfo = getCommandInfo(command)
        if commandInfo:
            print tag.detect + "Command found under id " + str(commandInfo[0])
            print tag.info + "Checking regex"
            regex = re.compile(commandInfo[2])
            if regex.match(command):
                print tag.ok + "Command matches its regex."
                print tag.info + "Getting command body."
                command = command[4:-1]
                print tag.ok + "Got " + command
                print tag.info +"Exploding by parameters."
                commandParams = re.findall('[A-Z][^A-Z]*',command)
                print tag.ok + "Done exploding."
                print tag.info + "Creating param dictionary."
                paramList = {}
                for commandParam in commandParams:
                    paramList[commandParam[0]] = commandParam[1:]
                print tag.ok + "Done. Got:"
                print paramList
                print tag.ok + "Done processing."
            else:
                print tag.warning + "Command doesn't match its regex. Skipping."
                continue
        else:
            print tag.warning + "Command not found in DB. Skipping."
            continue
