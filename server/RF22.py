
from Crypto.Cipher import AES
from random import randint
#from util import *
import serial
from array import array
import json
import time


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



class RF22Mesh:
    thisAddress = 0
    slaveSelectPin = 0
    interupt = 0
    arduino = 0
    RF22_ROUTER_ERROR_NONE              = 0
    RF22_ROUTER_ERROR_INVALID_LENGTH    = 1
    RF22_ROUTER_ERROR_NO_ROUTE          = 2
    RF22_ROUTER_ERROR_TIMEOUT           = 3
    RF22_ROUTER_ERROR_NO_REPLY          = 4
    RF22_ROUTER_ERROR_UNABLE_TO_DELIVER = 5
    RF22_RPC_ERROR                      = 6
    RF22_BROADCAST_ADDRESS              = 0xff
    SENDTOWAIT = 1
    RECVFROMACK = 2
    RECVFROMACKTIMEOUT = 3

    addr_map = {}
    start_address = 2


    
    def __init__( self, arduino ):
        self.arduino = arduino


    def clean_json( self, json_str ):
        open_braces = 0
        json_started = 0
        out_str = ""
        for i in range( len( json_str ) ):
            if json_str[i] == '{':
                if json_started == 0:
                    json_started = 1
                open_braces += 1
            elif json_str[i] == '}':
                open_braces -= 1
            elif open_braces == 0 and json_started == 1:
                return out_str

            if json_started == 1:
                out_str += json_str[i]
                #print json_str[i]

        return json_str

    def serial_prefix_check( self, prefix ):
        while self.arduino.inWaiting() < 1:
            pass

        for i in range( len( prefix ) ):
            byte = self.arduino.read()
            if not (prefix[i] == byte ):
                return False

        return True

    def sendtoWait( self, buf, length, dest ):
        try:
            print 'sendtoWait'
            rpc_obj = {}
            rpc_obj["m"] = self.SENDTOWAIT
            rpc_obj["p"] = {}
    
            ord_str = ""
            print "send buf"
            for i in range( length ):
                ord_str += str( ord( buf[i] ) ) + ", "
            print ord_str

            hex_buf = ""
            hex_str = ""
            for i in range( length ):
                hex_str += "%02x" % ord( buf[i] ) 
                hex_str += ", "
                hex_buf += "%02x" % ord( buf[i] )
            print hex_str

            rpc_obj["p"]["b"] = hex_buf
            rpc_obj["p"]["l"] = len( hex_buf )
            rpc_obj["p"]["d"] = dest

            json_str = json.JSONEncoder( separators=(',', ':') ).encode( rpc_obj ) 

            self.arduino.write( "234" )
            self.arduino.write( json_str )

            while( self.serial_prefix_check( "234" ) == False ):
                pass

            json_str = ''

            tries = 0
            while self.arduino.inWaiting() < 1 and tries < 100:
                time.sleep( .001 )
                tries += 1

            while self.arduino.inWaiting() > 0:
                tries = 0
                json_str += self.arduino.read();
                while self.arduino.inWaiting() < 1 and tries < 100:
                    time.sleep( .001 )
                    tries += 1

            ret_rpc_obj = json.loads( json_str )

            if( ret_rpc_obj["m"] != self.SENDTOWAIT ):
                print "sendtoWait received return message"
                print "from the wrong remote function: " + str( ret_rpc_obj["m"] )
                return RF22_RPC_ERROR

            return ret_rpc_obj["p"]["ret"]

        except ValueError as ex:
            print "sendtoWait: Value Error: Resending"
        except TypeError as ex:
            print ex
            print "sendtoWait: Type Error: Resending"
        except:
            print "sendtoWait: Uknown error: Resending"
            raise

        
    def recvfromAck( self ):
        rpc_obj = {}
        rpc_obj["m"] = self.RECVFROMACK
        rpc_obj["p"] = {}
        
        self.arduino.write( "234" )
        self.arduino.write( json.JSONEncoder( separators=(',', ':') ).encode( rpc_obj ) )

        while( self.serial_prefix_check( "234" ) == False ):
            pass

        ret_rpc_obj = json.load( self.arduino )

        if( ret_rpc_obj["m"] != "recvfromAck" ):
            print "recvfromAck received return message"
            print "from the wrong remote function: " + str( ret_rpc_obj["m"] )
            return 0

        length = ret_rpc_obj["p"]["len"]
        buf = ret_rpc_obj["p"]["buf"]
        source = ret_rpc_obj["p"]["source"]
        dest = ret_rpc_obj["p"]["dest"]
        ret = ret_rpc_obj["p"]["ret"]

        return ( ret, buf, length, source, dest )
        
    def recvfromAckTimeout( self, timeout ):
        rpc_obj = {}
        rpc_obj["m"] = self.RECVFROMACKTIMEOUT
        rpc_obj["p"] = {}
        rpc_obj["p"]["timeout"] = timeout
       
        json_item = json.JSONEncoder( separators=(',', ':') ).encode( rpc_obj )

        while True:
            self.arduino.write( "234" )
            self.arduino.write( json.JSONEncoder( separators=(',', ':') ).encode( rpc_obj ) )

            while( self.serial_prefix_check( "234" ) == False ):
                pass

            json_str = ''
   
            tries = 0
            while self.arduino.inWaiting() < 1 and tries < 100:
                time.sleep( .001 )
                tries += 1

            while self.arduino.inWaiting() > 0:
                tries = 0
                json_str += self.arduino.read();
                while self.arduino.inWaiting() < 1 and tries < 100:
                    time.sleep( .001 )
                    tries += 1

            try:
                
                ret_rpc_obj = json.loads( json_str )

                if not ( ret_rpc_obj["m"] == self.RECVFROMACKTIMEOUT ):
                    print "recvfromAckTimeout 6 received return message"
                    print "from the wrong remote function: " + str( ret_rpc_obj["m"] )
                    return ( 0, 0, 0, 0, 0 )

                ret = ret_rpc_obj["p"]["ret"]
                if ret != False : 
                    length = ret_rpc_obj["p"]["l"]
                    buf = ""
                    print "buf len: " + str( length )
                    buf_hex = ""
                    for i in range( 0, length, 2 ):
                        byte = ret_rpc_obj["p"]["b"][i:i+2]
                        buf_hex += byte + ", "
                        if( not byte == '' ):
                            val = int( byte, 16 )
                            buf += chr( val )
                    print buf_hex
                    buf = self.clean_json( buf )
                    source = ret_rpc_obj["p"]["s"]
                    dest = ret_rpc_obj["p"]["d"]
                else:
                    length = None
                    buf = None
                    source = None
                    dest = None

                return ( ret, buf, length, source, dest )
            except ValueError as ex:
                print "recvfromAckTimeout 7: Value Error: Resending"
            except TypeError as ex:
                print ex
                print "recvfromAckTimeout 8: Type Error: Resending"
            except:
                print "recvfromAckTimeout 9: Uknown error: Resending"
                raise


    def address_server( self ):
        print "address_server start"
        ( ret, buf, length, source, dest ) = self.recvfromAckTimeout( 100 )

        try:
            print buf
            msg = json.loads( buf )

            if( ret == True and msg['t'] == message_type.ADDRESS_REQUEST ):
                print 'address_server msg type received: ' + str( msg['t'] )
                node = msg['m']
                print 'address_server msg me received: ' + str( node )
                self.addr_map[str( node )] = self.start_address
                self.start_address += 1
                print 'address_server addr_map: ' + str( self.addr_map )
                print 'address_server start address: ' + str( self.start_address )

                addr_obj = {}
                addr_obj['t'] = message_type.ADDRESS_GRANT
                addr_obj['m'] = node
                addr_obj['a'] = self.addr_map[str( node )]

                print 'address_server addr_obj: ' + str( addr_obj )

                buf = json.JSONEncoder( separators=(',', ':') ).encode( addr_obj )

                print 'address_server encoded addr_obj buf: ' + buf

                ret = self.sendtoWait( buf, len( buf ), source )

                print 'address_server send ret: ' + str( ret )

                return ret

        except ValueError as ex:
            print "address_server: Value Error: Resending"
        except TypeError as ex:
            print ex
            print "address_server: Type Error: Resending"
        except:
            print "address_server: Uknown error: Resending"
            raise



class RF22AES( RF22Mesh ):
    thisAddress = 0
    slaveSelectPin = 0
    interupt = 0
    arduino = 0
    RF22_ROUTER_ERROR_NONE              = 0
    RF22_ROUTER_ERROR_INVALID_LENGTH    = 1
    RF22_ROUTER_ERROR_NO_ROUTE          = 2
    RF22_ROUTER_ERROR_TIMEOUT           = 3
    RF22_ROUTER_ERROR_NO_REPLY          = 4
    RF22_ROUTER_ERROR_UNABLE_TO_DELIVER = 5
    RF22_BROADCAST_ADDRESS              = 0xff
    
    default_key = buffer( array( 'B', [63, 5, 221, 227, 216, 136, 34, 84, 133, 20, 241, 251, 65, 101, 242, 148] ) )
    default_iv  = buffer( array( 'B', [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] ) )

    key_map = {}
    iv_map = {}

    def __init__( self, arduino ):
        self.arduino = arduino
        RF22Mesh.__init__( self, arduino )

    def pad( self, buf ):
        if( buf == None ):
            return ( None, 0 )
        length = len( buf )
        missing = 16 - ( length % 16 )
        if missing == 16:
            return ( buf, length )
        for i in range( missing ):
            length += 1
            buf += '\0'
        return ( buf, length )


    def sendtoWait( self, buf, length, dest, key = None, iv = None ):
        print "RF22AES:sendtoWait"
        if( key == None or iv == None ):
            print "RF22AES:sendtoWait no keys"
            ret = RF22Mesh.sendtoWait( self, buf, length, dest )
        else:
            aes = AES.new( key, AES.MODE_CBC, iv )
            ( buf, length ) = self.pad( buf )

            ord_str = ""
            print "before enc"
            for i in range( length ):
                ord_str += str( ord( buf[i] ) ) + ", "
            print ord_str

            buf = aes.encrypt( buf );
            
            ord_str = ""
            print "after enc"
            for i in range( length ):
                ord_str += str( ord( buf[i] ) ) + ", "
            print ord_str

            ret = RF22Mesh.sendtoWait( self, buf, length, dest )

        return ret
        
    def recvfromAck( self, key = None, iv = None ):
        if( key == None or iv == None ):
            ( ret, buf, length, source, dest ) = RF22Mesh.recvfromAck( self )
        else:
            aes = AES.new( key, AES.MODE_CBC, iv )
            
            ( ret, buf, length, source, dest ) = RF22Mesh.recvfromAck( self )
            
            if( ret == False ):
                buf = self.pad( buf )

                buf = aes.decrypt( buf )

        return ( ret, buf, length, source, dest )
        
    def recvfromAckTimeout( self, timeout, key = None, iv = None ):
        if( key == None or iv == None ):
            ( ret, buf, length, source, dest ) = RF22Mesh.recvfromAckTimeout( self, timeout )
        else:
            aes = AES.new( key, AES.MODE_CBC, iv )
            ( ret, buf, length, source, dest ) = RF22Mesh.recvfromAckTimeout( self, timeout )
            if( ret == True ):
                print "RF22AES::recvfromAckTimeout: ret true"
                ( buf, length ) = self.pad( buf )
                
                ord_str = ""
                print "before dec"
                for i in range( length ):
                    ord_str += str( ord( buf[i] ) ) + ", "
                print ord_str

                buf = aes.decrypt( buf )

                ord_str = ""
                print "after dec"
                for i in range( length ):
                    ord_str += str( ord( buf[i] ) ) + ", "
                print ord_str
                
                buf = RF22Mesh.clean_json( self, buf )
                length = len( buf )

        return ( ret, buf, length, source, dest )

    def address_server( self ):
        try:
            ret = RF22Mesh.address_server( self )

            if( ret == RF22Mesh.RF22_ROUTER_ERROR_NONE ):
                ret = False
                print "RF22AES.address_server wait for iv sync request"
                while( ret == False ):
                    ( ret, buf, length, source, dest ) = self.recvfromAckTimeout( 2000, self.default_key, self.default_iv )
                    print ret

                '''
                buf_str = ""
                for i in range( length ):
                    buf_str += chr( buf[i] )
               
                print buf_str
                '''
                rpc_obj = json.loads( buf )

                if( rpc_obj['t'] == message_type.SYNC_IV and \
                    RF22Mesh.addr_map[str( rpc_obj['m'] )] == source ):
                    self.iv_map[str( source )] = rpc_obj['i']
                    print "got IV for " + str( source )
                    print self.iv_map[str( source )]
                else:
                    print "return 1 RF22Mesh.RF22_ROUTER_ERROR_NO_ROUTE"
                    return RF22Mesh.RF22_ROUTER_ERROR_NO_ROUTE

                ack_obj = {}
                ack_obj['m'] = rpc_obj['m']
                ack_obj['t'] = message_type.SYNC_IV

                json_str = json.JSONEncoder( separators=(',', ':') ).encode( ack_obj ) 

                print "RF22AES.address_server send iv sync ack"
                ret = self.sendtoWait( json_str, len( json_str ), RF22Mesh.addr_map[str( rpc_obj['m'] )], self.default_key, self.default_iv )
                if( not ( ret == RF22Mesh.RF22_ROUTER_ERROR_NONE ) ):
                    print "return 2 " + str( ret )
                    return ret

                print "RF22AES.address_server wait for key sync request"
                while( ret == False ):
                    ( ret, buf, length, source, dest ) = self.recvfromAckTimeout( 2000, self.default_key, self.default_iv )
                    print ret
                
                '''
                buf_str = ""
                for i in range( length ):
                    buf_str += chr( buf[i] )
                '''
                rpc_obj = json.loads( buf )
                print "RF22AES.address_server 6 Json loaded"
                print 'RF22AES.address_server 7 decoded json: ' + str( rpc_obj )

                print rpc_obj['t']
                print rpc_obj['m']
                print rpc_obj['i']
                if( rpc_obj['t'] == message_type.SYNC_KEY and \
                    RF22Mesh.addr_map[str( rpc_obj['m'] )] == source ):
                    self.key_map[str( source )] = rpc_obj['i']
                    print "got Key for " + str( source )
                    print self.key_map[str( source )]
                else:
                    print "return 3 RF22Mesh.RF22_ROUTER_ERROR_NO_ROUTE"
                    return RF22Mesh.RF22_ROUTER_ERROR_NO_ROUTE

                ack_obj = {}
                ack_obj['m'] = rpc_obj['m']
                ack_obj['t'] = message_type.SYNC_KEY

                json_str = json.JSONEncoder( separators=(',', ':') ).encode( ack_obj ) 

                print "RF22AES.address_server send key sync ack"
                ret = self.sendtoWait( json_str, len( json_str ), RF22Mesh.addr_map[str( rpc_obj['m'] )], self.default_key, self.default_iv )
                if( not ( ret == RF22Mesh.RF22_ROUTER_ERROR_NONE ) ):
                    print "return 4 " + str( ret )
                    return ret
               
                print "return 5 " + str( ret )
                return ret

            else:
                print "return 6 RF22Mesh.RF22_ROUTER_ERROR_NO_ROUTE"
                return RF22Mesh.RF22_ROUTER_ERROR_NO_ROUTE
        except ValueError as ex:
            print "RF22AES::address_server: Value Error: Resending"
            print "return 6 RF22Mesh.RF22_ROUTER_ERROR_NO_ROUTE"
            return RF22Mesh.RF22_ROUTER_ERROR_NO_ROUTE
        except TypeError as ex:
            print ex
            print "RF22AES::address_server: Type Error: Resending"
            print "return 6 RF22Mesh.RF22_ROUTER_ERROR_NO_ROUTE"
            return RF22Mesh.RF22_ROUTER_ERROR_NO_ROUTE
        except:
            print "RF22AES::address_server: Uknown error: Resending"
            raise

