import os

files = ["10M_packets_head_96_11.pcap",
         "10M_packets_head_96_111.pcap",
         "10M_packets_head_96_211.pcap",
         "10M_packets_head_96_311.pcap",
         "10M_packets_head_96_411.pcap",
         "10M_packets_head_96_511.pcap",
         "10M_packets_head_96_611.pcap",
         "10M_packets_head_96_711.pcap",
         "10M_packets_head_96_811.pcap",
         "10M_packets_head_96_911.pcap",
         "10M_packets_head_96_1008.pcap",
         "10M_packets_head_96_888.pcap",
         "10M_packets_head_96_88.pcap",
         "10M_packets_head_96_291.pcap",
         "10M_packets_head_96_734.pcap"]

for file in files:
    os.system("python3 pcap_ip_dst_frequency.py -f /media/data_orig/felvett/" + file)
