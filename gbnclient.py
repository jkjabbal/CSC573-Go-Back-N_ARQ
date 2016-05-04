import sys,threading,socket,pickle,time

window = [0,0]
lastsent =-1
lastack=-1
ackexpected =-1
lock = threading.Lock()
pkts =0

def main():
    global server_port
    global server_ip
    server_name = sys.argv[1]
    server_port = sys.argv[2]
    file_name = sys.argv[3]
    window_size = sys.argv[4]
    MSS = sys.argv[5]
    server_ip = socket.gethostbyname(server_name)
    receiver()
    filesender(file_name,MSS,window_size)
    return

class filesender(threading.Thread):

    def __init__(self,file_name,MSS,window_size):
        threading.Thread.__init__(self)
        self.f =file_name
        self.M = MSS
        self.N = window_size
        self.r = receiver
        self.start()

    def run(self):
        self.read_file()

    def read_file(self):
        file_content=[]
        global pkts
        with open(self.f,'rb') as fp:
            while True:
                file_chunk=fp.read(int(self.M))
                if file_chunk:
                    file_content.append(file_chunk)
                else:
                    break

        self.final_pkts = self.parse_pkt(file_content)
        pkts  =  len(self.final_pkts)
        self.rdt_send()


    def rdt_send(self):
        global lock
        global lastack
        global window
        global lastsent
        global ackexpected
        global client_soc
        global pkts

        lock.acquire()
        #if pkts < self.N : 
         #   self.N = pkts
        window[1]=window[0]+int(self.N)-1
        lock.release()
        #print 'total number of pkts is '+str(len(self.final_pkts))
        while lastack != len(self.final_pkts)-1:
            starttime = time.time()
            for i in range(int(window[0]),int(window[1])+1):
                #print 'sending packet '+str(i)
                client_soc.sendto(self.final_pkts[i],(server_ip,int(server_port)))
            lastsent = int(window[1])
            ackexpected = int(window[0])
            self.timeout(starttime)
            #print 'last sent value is  '+ str(lastsent)

        end_message='0000end1111'
        seq_num = len(self.final_pkts)
        checksum =  self.checksum(end_message)
        end_pkt_list = [seq_num,checksum,self.data_field,end_message]
        end_pkt = pickle.dumps(end_pkt_list)
        client_soc.sendto(end_pkt,(server_ip,int(server_port)))
        #print 'here at the exit'
        client_soc.close()
        exit()

    def timeout(self,starttime):
        #print 'entered timeout'
        global window
        global lastack
        global lastsent
        global ackexpected

        while True :
            if time.time()-starttime > 0.1 :
                if lastack >= ackexpected:
                    lock.acquire()
                    #print 'window values are '+ str(window[0])+' '+str(window[1])
                    #print 'last ack received is '+str(lastack)
                    window[1]=window[1]+int(lastack)-window[0]+1
                    if window[1]>=len(self.final_pkts):
                        window[1]=len(self.final_pkts)-1
                    window[0]=int(lastack)+1
                    #print 'new window values are '+str(window[0])+' '+str(window[1])
                    lock.release()
                    break
                else :
                    print 'Timeout, sequence number ='+str(ackexpected)
                    break

    def parse_pkt(self,file_content):
        self.data_field = '0b0101010101010101'
        final_pkts =[]
        seq_num=0
        for item in file_content:
            pkt_list = [seq_num,self.checksum(item),self.data_field,item]
            seq_num+=1
            final_pkts.append(pickle.dumps(pkt_list))
        return final_pkts

    def checksum(self,data):
        pos =  len(data)
        if (pos & 1) :
            pos -=1
            sum = ord(data[pos])
        else:
            sum=0
        while pos >0 :
            pos -=2
            sum+=(ord(data[pos+1])<<8) + ord(data[pos])
        sum = (sum >>16) + (sum & 0xffff)
        sum += (sum>>16)

        result = (~sum) & 0xffff
        result  = result >>8 | ((result & 0xff)<<8)
        return result


class receiver(threading.Thread):
    def  __init__(self):
        threading.Thread.__init__(self)
        self.host = socket.gethostname()
        self.ack_port = 65432
        self.ack_soc = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.ack_soc.bind((self.host,self.ack_port))
        self.start()

    def run(self):
        self.receive_ack()

    def receive_ack(self):
        global lastack
        global pkts
        global client_soc
        while True:
            #print "checking for ack's"
            ack_pkt,addr=self.ack_soc.recvfrom(102400)
            seq_num,checksum_field,ack_field =  pickle.loads(ack_pkt)
            if ack_field =='0b1010101010101010':
                lock.acquire()
                lastack=int(seq_num)-1
                #print 'received ack for '+str(lastack)
                lock.release()
            if lastack == pkts-1:
                break
            if not client_soc : break
        exit()

if __name__=="__main__":
    if len(sys.argv) != 6 :
        print "Please enter all the arguments required for starting the client"
        exit()
    global client_soc
    client_soc = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    main()

