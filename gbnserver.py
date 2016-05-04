import socket,sys,threading,pickle,random,time
from datetime import datetime
from decimal import *

ack_port = 65432

def main():
    #print socket.gethostname()
    global server_sock
    hostname = socket.gethostname()
    port =  7735
    server_sock.bind((hostname,port))
    filename = sys.argv[2]
    p = sys.argv[3]
    #random.seed(datetime.now())
    starttime = time.time()
    receive(server_sock,filename,p)
    endtime = time.time()
    print 'time taken is '+str(endtime-starttime)
    exit()

class receive():

    def __init__(self,soc,filename,p):
        self.f = filename
        self.p = p
        self.soc = soc
        self.ack_soc = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.rdt_receive()

    def rdt_receive(self):
        fp = open(self.f,'wb')
        Flag = True
        self.expected_seqnum =0
        while Flag:
            data,addr=self.soc.recvfrom(102400)
            self.host=socket.gethostbyaddr(addr[0])[0]
            seq_num,checksum,data_type,message = pickle.loads(data)
            #print 'received data with seq_num '+str(seq_num)
            if data_type == '0b0101010101010101':
                valid=self.verify_checksum(checksum,message)
                #print 'received seq num is ' + str(seq_num)
                if valid and self.expected_seqnum ==seq_num :
                    if message=='0000end1111' :
                        #print 'recieved end message'
                        Flag = False
                    else :
                        rv=self.send_ack(seq_num)
                        if rv : fp.write(message)
        fp.close()
        self.soc.close()
        self.ack_soc.close()

    def verify_checksum(self,checksum,message):
        pos = len(message)
        if (pos & 1):
            pos -=1
            sum = ord(message[pos])
        else :
            sum = 0
        while pos >0:
            pos -=2
            sum+= (ord(message[pos+1])<<8) + ord(message[pos])
        sum = (sum >>16) + (sum & 0xffff)
        sum  += (sum>>16)

        result = (~sum) &  0xffff
        result = result >>8 | ((result &0xff)<<8)

        if result  == checksum:
            return True
        else :
            return False

    def send_ack(self,seq_num):
        r=random.random()
        if Decimal(r) > Decimal(self.p) :
            #print "packet success"
            ack_field = '0b1010101010101010'
            ack_num = int(seq_num)+1
            checksum_field = '0b0000000000000000'
            ack_pkt_list = [ack_num,checksum_field,ack_field]
            ack_pkt = pickle.dumps(ack_pkt_list)
            #print "sending ack with expected seq num is "+str(self.expected_seqnum)
            self.ack_soc.sendto(ack_pkt,(self.host,ack_port))
            self.expected_seqnum +=1
            #print 'expected seq number is '+ str(self.expected_seqnum)
            return 1
        else :
            print "Packet loss, sequence number ="+str(seq_num)
            return 0


if __name__=="__main__":
    global server_sock
    if len(sys.argv)  != 4 :
        print 'please enter all the arguments'
        exit()
    server_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    main()
