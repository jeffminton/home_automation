#!/usr/bin/python

from Crypto.Cipher import AES
from random import randint
#from util import *
import serial
from array import array
import RF22
import argparse
import time


key = buffer( array( 'B', [63, 5, 221, 227, 216, 136, 34, 84, 133, 20, 241, 251, 65, 101, 242, 148] ) )
iv_map = {}
addr_map = []
start_address = 2


class message_type:
    ADDRESS_REQUEST = 0 
    SEND_COMMAND_REQ = 1 
    COMMAND = 2
    SEND_COMMAND_RESP = 3
    COMMAND_ACK = 4
    SYNC_KEY = 5
    SYNC_IV = 6
    ADDRESS_GRANT = 7
                            

class node_type:
    GARAGE_DOOR = 0
    THERMOSTAT_UPSTAIRS = 1

'''
def give_address( node, source ):
    buf = []
    addr_map[node] = start_address
    start_address += 1

    buf[0] = message_type.ADDRESS_GRANT
    buf[1] = node
    buf[2] = addr_map[node]

    buf = rf22AES.pad( buf )

    return rf22Mesh.sendtoWait( buf, len( buf ), source )
''' 

def main():
    parser = argparse.ArgumentParser(description='Generate RPC stub code')
    parser.add_argument( '-d', '--device', help='The serial device' )
    parser.add_argument( '-b', '--baudrate', help='The baud rate' )
    args = parser.parse_args()

    iv_zero = [0] * 16
    iv_zero_buf = buffer( array( 'B', iv_zero ) )

    arduino = None

    try:
        arduino = serial.Serial( args.device, int( args.baudrate ) )
        arduino.timeout = 3600
        arduino.setDTR(False)
        time.sleep(1)
        # toss any data already received, see
        # http://pyserial.sourceforge.net/pyserial_api.html#serial.Serial.flushInput
        arduino.flushInput()
        arduino.setDTR(True)

        #sleep for 3 seconds to allow the arduino to reboot
        time.sleep( 3 )

        arduino.write( "234123456" )

        while( arduino.inWaiting() < 1 ):
            0

        msg = arduino.read( 7 )

        if 'online' in msg:
            print "Arduino online"
        else:
            print "Arduino not connected"
            exit( 1 )

        rf22Mesh = RF22.RF22Mesh( arduino )
        rf22AES = RF22.RF22AES( arduino )

        while 1:
            print "waiting for address request"
            ret = rf22AES.address_server()
            '''
            print "address_server(): " + str( ret )
            while not ( ret == rf22Mesh.RF22_ROUTER_ERROR_NONE ):
                print "address_server(): " + str( ret )
                ret = rf22AES.address_server()
                print "waiting for address request"
            '''
            if( ret == rf22Mesh.RF22_ROUTER_ERROR_NONE ):
                print "gave_address"
                time.sleep(1600)


    except KeyboardInterrupt:
        print 'KeyboardInterrupt'
        if arduino:
            print 'Closing port'
            arduino.close()
        exit()
    except:
        print 'unknown exception'
        if arduino:
            print 'Closing port'
            arduino.close()
        raise

'''
    ( ret, buf, length, source, dest ) = rf22Mesh.recvfromAck()

    buf = pad( arduino.read( 16 ) )

    aes = AES.new( key, AES.MODE_CBC, iv_zero_buf )
    iv = aes.decrypt( buf )

    buf = arduino.read( 16 )
    aes = AES.new( key, AES.MODE_CBC, iv )
    node = aes.decrypt( buf )
    node = ord( node[0] )

    iv_map[ node ] = iv

    aes = AES.new( key, AES.MODE_CBC, iv_map[ node_type.GARAGE_DOOR ] )
    msg = aes.encrypt( pad( "online" ) );
    arduino.write( msg )
'''

if __name__ == "__main__":
    main()
