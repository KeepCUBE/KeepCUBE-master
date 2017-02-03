import redis
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
    return True


def SVB(dsc):
    print tag.info + "Sending command " + dsc + " via BlueTooth"
    return True


def SVW(dsc):
    print tag.info + "Sending command " + dsc + " via WiFi"
    return True


def log(level, message):
    print getattr(tag, level) + message
    filename = "redis-log-" + strftime("%Y-%m-%d", gmtime())
    file = open(filename, 'a')
    file.write(strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " " + level + " >> " + message + "\r\n")


def validate_dsc(command):
    return (
        True if command.startswith('#') and command.endswith(';') and command[1].isupper() and command[2].isupper() and
                command[3].isupper() else False)


log("ok", "Process started")
r = redis.StrictRedis(host='localhost', port=6379, db=0)
p = r.pubsub()
try:
    p.subscribe('test')
    log("ok", "Subscription active")
except:
    log("fail", "Subscription failed")
message = p.get_message()
while (True):
    message = p.get_message()
    if (message):
        log("dump", "Received new message: " + str(message['data']))
        if (validate_dsc(str(message['data']))):
            head = message['data'][1:4]
            log("dump", "Extracted head: " + head)
            body = message['data'][4:-1]
            log("dump", "Extracted body: " + body)
            possibles = globals().copy()
            possibles.update(locals())
            method = possibles.get(head)
            if not method:
                log("fail", "Method %s is not implemented" % head)
            else:
                method(body)
                log("ok", "Done processing command " + message['data'])
        else:
            log("warn", "Message is not valid DSC command")
