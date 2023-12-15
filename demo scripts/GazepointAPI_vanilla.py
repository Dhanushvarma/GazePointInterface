######################################################################################
# GazepointAPI_vanilla.py - Example Client
# Written in 2013 by Gazepoint www.gazept.com
#
# To the extent possible under law, the author(s) have dedicated all copyright 
# and related and neighboring rights to this software to the public domain worldwide. 
# This software is distributed without any warranty.
#
# You should have received a copy of the CC0 Public Domain Dedication along with this 
# software. If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.
######################################################################################

import socket

# Host machine IP
HOST = '127.0.0.1'
# Gazepoint Port
PORT = 4242
ADDRESS = (HOST, PORT)

# Connect to Gazepoint API
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(ADDRESS)

# Send commands to initialize data streaming
s.send(str.encode('<SET ID="ENABLE_SEND_CURSOR" STATE="1" />\r\n'))
s.send(str.encode('<SET ID="ENABLE_SEND_POG_FIX" STATE="1" />\r\n'))
s.send(str.encode('<SET ID="ENABLE_SEND_DATA" STATE="1" />\r\n'))

while 1:
    # Receive data
    rxdat = s.recv(1024)
    data = bytes.decode(rxdat)
    print(data)

    # Parse data string
    FPOGX = 0
    FPOGY = 0
    FPOGV = 0
    CX = 0
    CY = 0

    # Split data string into a list of name="value" substrings
    datalist = data.split(" ")

    # Iterate through list of substrings to extract data values
    for el in datalist:
        if (el.find("FPOGX") != -1):
            FPOGX = float(el.split("\"")[1])

        if (el.find("FPOGY") != -1):
            FPOGY = float(el.split("\"")[1])

        if (el.find("FPOGV") != -1):
            FPOGV = float(el.split("\"")[1])

        if (el.find("CX") != -1):
            CX = float(el.split("\"")[1])

        if (el.find("CY") != -1):
            CY = float(el.split("\"")[1])

    # Print results
    print("FPOGX:", FPOGX)
    print("FPOGY:", FPOGY)
    print("FPOGV:", FPOGV)
    print("CX:", CX)
    print("CY:", CY)
    print("\n")

s.close()