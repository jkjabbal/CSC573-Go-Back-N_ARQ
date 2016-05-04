I.GO-BACK-N
  Client:
    python gbnclient.py <server_fqdn> 7735 <filename_with_extension> N MSS
  Server:
    python gbnserver.py 7735 <outfile_with_extension> p
II.SELECTIVE REPEAT
  Client:
    python srpclient.py <server_fqdn> 7735 <filename_with_extension> N MSS
  Server:
    python srpserver.py 7735 <outfile_with_extension> p
