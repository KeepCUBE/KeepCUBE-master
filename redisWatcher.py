import redis
from termcolor import colored


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


def validate_dsc(command):
    return (
    True if command.startswith('#') and command.endswith(';') and command[1].isupper() and command[2].isupper() and
            command[3].isupper() else False)


print tag.ok + "Process started"
r = redis.StrictRedis(host='localhost', port=6379, db=0)
p = r.pubsub()
try:
    p.subscribe('test')
    print tag.ok + "Subscribing active"
except:
    print tag.fail + "Subscribing failed"
while (True):
    message = p.get_message()
    if (message):
        print tag.dump + "Received new message: " + str(message['data'])
        if (validate_dsc(str(message['data']))):
            head = message['data'][1:4]
            print tag.dump + "Extracted head: " + head
            body = message['data'][4:-1]
            print tag.dump + "Extracted body: " + body
            if head == 'SVA':
                SVA(body)
                print tag.ok + "Done processing command " + str(message['data'])
            elif head == 'SVB':
                SVB(body)
                print tag.ok + "Done processing command " + str(message['data'])
            elif head == 'SVW':
                SVW(body)
                print tag.ok + "Done processing command " + str(message['data'])
            else:
                print tag.warn + "DSC was not recognized or is not supported"
        else:
            print tag.warn + "Message is not valid DSC command"
