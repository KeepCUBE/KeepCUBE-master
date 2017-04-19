import redis
import serial
from dscParser import parse_dsc
from termcolor import colored
from time import gmtime, strftime


class tag:
    ok = "[  " + colored("OK", "green") + "  ] "
    info = "[ " + colored("INFO", "yellow") + " ] "
    fail = "[ " + colored("FAIL", "red") + " ] "
    warn = "[ \033[1;31mWARN\033[0m ] "
    dump = "[ " + colored("DUMP", "cyan") + " ] "


def SVA(dsc):
    print tag.info + "Sending command " + dsc + " via ATMega"
    ser.write(dsc)
    return True


def SVB(dsc):
    print tag.info + "Sending command " + dsc + " via BlueTooth"
    return True


def SVW(dsc):
    print tag.info + "Sending command " + dsc + " via WiFi"
    return True


def log(level, message):
    print getattr(tag, level) + message
    filename = "redis-log-" + strftime("%Y-%m-%d", gmtime()) + ".log"
    file = open(filename, 'a')
    file.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " " + level + " | " + message + "\r\n")


def validate_dsc(command):
    return (
        True if command.startswith('#') and command.endswith(';') and command[1].isupper() and command[2].isupper() and
                command[3].isupper() else False)


log("ok", "Process started")
r = redis.StrictRedis(host='localhost', port=6379, db=0)
p = r.pubsub()
try:
    p.subscribe('keep')
    log("ok", "Subscription active")
except:
    log("fail", "Subscription failed")
message = p.get_message()
ser = serial.Serial("/dev/ttyAMA0", 9600, timeout = 1)
if(ser.isOpen() == False):
    ser.open()
log("ok", "Serial opened.")
while (True):
    message = p.get_message()
    if (message):
        log("dump", "Received new message: " + str(message['data']))
        dsc = parse_dsc(message['data'])
        if(dsc != False):
            possibles = globals().copy()
            possibles.update(locals())
            method = possibles.get(dsc['head'])
            if not method:
                log("fail", "Method %s is not implemented" % dsc['head'])
            else:
                if False in dsc['body']:
                    log("fail", "No parameters found!")
                else:
                    if 'C' not in dsc['body']:
                        log("fail", "Command parameter not found!")
                    else:
                        method(dsc['body']['C'])
                        log("ok", "Done processing command " + message['data'])
        else:
            log("fail", "Message was not valid DSC command")