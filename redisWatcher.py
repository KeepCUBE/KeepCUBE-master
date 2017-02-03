import redis
from termcolor import colored

class tag:
    ok = "[  "+colored("OK","green")+"  ] "
    info = "[ "+colored("INFO","yellow")+" ] "
    fail = "[ "+colored("FAIL","red")+" ] "
    warn = "[ \033[1;31mWARN\033[0m ] "
    dump = "[ "+colored("DUMP","cyan")+" ] "


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