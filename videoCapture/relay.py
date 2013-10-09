import socket, time

def switchRelayOn(relay):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('192.168.0.200', 17494))
    if relay == 0:
        val = 101
    elif relay == 1:
        val = 102
    elif relay == 2:
        val = 103
    elif relay == 3:
        val = 104
    elif relay == 4:
        val = 105
    elif relay == 5:
        val = 106
    elif relay == 6:
        val = 107
    elif relay == 7:
        val = 108
    else:
        raise ValueError('relay has to be an int in 0..7')
    s.send(chr(val))
    time.sleep(0.01)
    s.close()
        
def switchRelayOff(relay):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('192.168.0.200', 17494))
    if relay == 0:
        val = 111
    elif relay == 1:
        val = 112
    elif relay == 2:
        val = 113
    elif relay == 3:
        val = 114
    elif relay == 4:
        val = 115
    elif relay == 5:
        val = 116
    elif relay == 6:
        val = 117
    elif relay == 7:
        val = 118
    else:
        raise ValueError('relay has to be an int in 0..7')
    
    s.send(chr(val))
    time.sleep(0.01)
    s.close()
    
if __name__ == "__main__":    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--relay', 
                        help="relay port",
                        type=int, default=0)
    parser.add_argument('--on', 
                        dest='signal',action='store_true')
    parser.add_argument('--off', 
                        dest='signal',action='store_false')
    
    parser.set_defaults(signal=True)
    
    args = parser.parse_args()
    
    print args

    if args.signal:
        switchRelayOn(args.relay)
    else:
        switchRelayOff(args.relay)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    