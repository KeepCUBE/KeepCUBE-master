import redis
from termcolor import colored

class tag:
    ok = "[  "+colored("OK","green")+"  ] "
    info = "[ "+colored("INFO","yellow")+" ] "
    fail = "[ "+colored("FAIL","red")+" ] "
    warn = "[ \033[1;31mWARN\033[0m ] "
    dump = "[ "+colored("DUMP","cyan")+" ] "

def validate_dsc(command):
    return (True if command.startswith('#') and command.endswith(';') and command[1].isupper() and command[2].isupper() and command[3].isupper() else False)

print tag.ok + "Process started"
r = redis.StrictRedis(host='localhost',port=6379, db=0)
p = r.pubsub()
try:
    p.subscribe('test')
    print tag.ok + "Subscribing active"
except:
    print tag.fail + "Subscribing failed"
while(True):
    message = p.get_message()
    if(message):
        print tag.dump + "Received new message: " + str(message['data'])
        print tag.info + "Valid DSC?: " + str(validate_dsc(str(message['data'])))
        if(validate_dsc(str(message['data']))):
            head = message['data'][1:3]
            print tag.dump + "Extracted head: " + head
            body = message['data'][4:-1]
            print tag.dump + "Extracted body: " + body