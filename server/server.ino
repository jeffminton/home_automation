// rf22_mesh_server1.pde
// -*- mode: C++ -*-
// Example sketch showing how to create a simple addressed, routed reliable messaging server
// with the RF22Mesh class.
// It is designed to work with the other examples rf22_mesh_*
// Hint: you can simulate other network topologies by setting the 
// RF22_TEST_NETWORK define in RF22Router.h

// Mesh has much greater memory requirements, and you may need to limit the
// max message length to prevent wierd crashes
#define RF22_MAX_MESSAGE_LEN 50
#define DELAY_TIME 0
//#define OVERRIDE_DELAY_TIME 0


#include <RF22Mesh.h>
#include <SPI.h>
// include the aJSON library
#include <aJSON.h>
// include the JsonRPC library
#include <JsonRPC.h>
#include "server.h"
#include <MemoryFree.h>
#include <memdebug.h>
#include <LiquidCrystal.h>

// In this small artifical network of 4 nodes,
#define SERVER_ADDRESS 1

// Singleton instance of the radio
RF22Mesh rf22( SERVER_ADDRESS );
// initialize a serial json stream for receiving json objects
// through a serial/USB connection
aJsonStream stream(&Serial);

//#define PRINT
#define LCD
#ifdef LCD
LiquidCrystal lcd( 8, 9, 4, 5, 6, 7 );

void freeMem(char* message, int delay_time = DELAY_TIME) {
#ifdef PRINT
    lcd.clear();
    lcd.print( message );
    lcd.print( " :" );
    //lcd.setCursor( 0, 1 );
    lcd.print( freeMemory( ) );
#ifdef OVERRIDE_DELAY_TIME
    delay( OVERRIDE_DELAY_TIME );
#else
    delay( delay_time );
#endif
#endif
}

void freeMem(char letter, int delay_time = DELAY_TIME) {
#ifdef PRINT
    lcd.clear();
    lcd.print( letter );
    lcd.print( " :" );
    //lcd.setCursor( 0, 1 );
    lcd.print( freeMemory( ) );
#ifdef OVERRIDE_DELAY_TIME
    delay( OVERRIDE_DELAY_TIME );
#else
    delay( delay_time );
#endif
#endif
}


void freeMem( int value, int delay_time = DELAY_TIME) {
#ifdef PRINT
    lcd.clear();
    lcd.print( value );
    lcd.print( " :" );
    //lcd.setCursor( 0, 1 );
    lcd.print( freeMemory( ) );
#ifdef OVERRIDE_DELAY_TIME
    delay( OVERRIDE_DELAY_TIME );
#else
    delay( delay_time );
#endif
#endif
}


void freeMem( const __FlashStringHelper *message, int delay_time = DELAY_TIME ) {
#ifdef PRINT
    char buf[BUF_SIZE]; 
    const char PROGMEM *p = (const char PROGMEM *)message;
    uint8_t count = 0;
    unsigned char c;
    while( count < BUF_SIZE ) {
    c = pgm_read_byte(p++);
    buf[count] = c;
    if (c == 0) break;
    count++;
    }
    return freeMem( (char *) buf, delay_time);
#endif
}


void print( char *message, int delay_time = DELAY_TIME ) {
#ifdef PRINT
    lcd.clear();
    lcd.print( message );
#ifdef OVERRIDE_DELAY_TIME
    delay( OVERRIDE_DELAY_TIME );
#else
    delay( delay_time );
#endif
#endif
}


void print( const __FlashStringHelper *message, int delay_time = DELAY_TIME ) {
#ifdef PRINT
    char buf[BUF_SIZE]; 
    const char PROGMEM *p = (const char PROGMEM *)message;
    uint8_t count = 0;
    unsigned char c;
    while( count < BUF_SIZE ) {
    c = pgm_read_byte(p++);
    buf[count] = c;
    if (c == 0) break;
    count++;
    }
    return print( (char *) buf, delay_time);
#endif
}

#else

void freeMem(char* message, int delay_time = DELAY_TIME) {
#ifdef PRINT
    Serial.print( message );
    Serial.print( F( " :" ) );
    Serial.println( freeMemory() );
#endif
}

void freeMem( int value, int delay_time = DELAY_TIME ) {
#ifdef PRINT
    Serial.print( value );
    Serial.print( F( " :" ) );
    Serial.println( freeMemory() );
#endif
}



void print( char* message, int delay_time = DELAY_TIME ) {
#ifdef PRINT
    Serial.println( message );
#endif
}


void freeMem( const __FlashStringHelper *message, int delay_time = DELAY_TIME ) {
#ifdef PRINT
    Serial.print( message );
    Serial.print( F( " :" ) );
    Serial.println( freeMemory() );
#endif
}


void print( const __FlashStringHelper *message, int delay_time = DELAY_TIME ) {
#ifdef PRINT
    Serial.println( message );
#endif
}

#endif


/*
 * Function:        sendtoWait
 * Input:           none
 * Serial Input:    3 parameters
 *                  msg - the message to send
 *                  len - the length of the message
 *                  dest - destination address
 * Serial Output:   ret - The return code of rf22 sendtoWait
 * Output:          none
 * Dec:             Get parameters for rf22 sendtoWait function
 *                  Serial data in pattern: msg, len, dest
 */
void sendtoWait( aJsonObject *params ) {
    char *buf;
    char byte_str[] = {'\0', '\0', '\0'};
    uint8_t len, dest, ret, str_len;
    aJsonObject *bufParam, *root, *retParams;

    len = aJson.getObjectItem( params, F( "l" ) )->valueint;
    dest = aJson.getObjectItem( params, F( "d" ) )->valueint;

    bufParam = aJson.getObjectItem( params, F( "b" ) );

    memset( (void *) RF22Router::global_msg_buffer, 0, GLOBAL_BUFFER_SIZE );

    if( bufParam->type == (char) 5 ) {
        buf = bufParam->valuestring;
        str_len = strlen( buf );
        for( int i = 0, j = 0; i < str_len; i+=2, j++ ) {
            byte_str[0] = buf[i];
            byte_str[1] = buf[i + 1];
            RF22Router::global_msg_buffer[j] = (uint8_t) strtol( byte_str, NULL, 16 );
        }
        len = strlen( (char *) RF22Router::global_msg_buffer );

        ret = rf22.sendtoWait( RF22Router::global_msg_buffer, len, dest );
/*
    } else if( bufParam->type == (char) 6 ) {
        arr_len = aJson.getArraySize( bufParam );

        for( uint8_t i = 0; i < arr_len; i++ ) {

            RF22Router::global_msg_buffer[i] = (uint8_t) aJson.getArrayItem( bufParam, i )->valueint;
        }
        ret = rf22.sendtoWait( RF22Router::global_msg_buffer, len, dest );
*/
    }

    root = aJson.createObject();

    aJson.addNumberToObject( root, F( "m" ), SENDTOWAIT );

    retParams = aJson.createObject();

    aJson.addItemToObject( root, F( "p" ), retParams );

    aJson.addNumberToObject( retParams, F( "ret" ), ret );


    Serial.print( F("234" ) );
    aJson.print( root, &stream );

    aJson.deleteItem( root );

}

/*
 * Function:        recvfromAck
 * Input:           none
 * Serial Input:    none
 * Serial Output:   
 *                  *msg - the received message
 *                  *len - the recieved message lenght
 *                  *source - the source of the message
 *                  *dest - the messages desired dstination
 * output:          none
 * desc:            get parameters for and call recvfromAck
 */
void recvfromAck( aJsonObject *params ) {



    uint8_t bytes, len = GLOBAL_BUFFER_SIZE, source, dest;
    boolean ret;
    aJsonObject *root, *retParams;

    ret = rf22.recvfromAck( RF22Router::global_msg_buffer, &len, &source, &dest );

    root = aJson.createObject();
    aJson.addNumberToObject( root, F( "m" ), RECVFROMACK );
    retParams = aJson.createObject();
    aJson.addItemToObject( root, F( "p" ), retParams );
    aJson.addItemToObject( retParams, F( "buf" ), aJson.createIntArray( RF22Router::global_msg_buffer, len ) ); 
    aJson.addNumberToObject( retParams, F( "len" ), len );
    aJson.addNumberToObject( retParams, F( "source" ), source );
    aJson.addNumberToObject( retParams, F( "dest" ), dest );
    if( ret == true ) {
        aJson.addTrueToObject( retParams, F( "ret" ) );
    } else {
        aJson.addFalseToObject( retParams, F( "ret" ) );
    }

    Serial.write( aJson.print( root ) );

    aJson.deleteItem( root );
}


/*
 * Function:        recvfromAckTimeout
 * Input:           none
 * Serial Input:    1 param
 *                  timeout - the time to wait for an ack
 * Serial Output:   4 params
 *                  msg - the received message
 *                  len - the recieved message lenght
 *                  source - the source of the message
 *                  dest - the messages desired dstination
 * output:          none
 * desc:            get parameters for and call recvfromAckTimeout
 */
void recvfromAckTimeout( aJsonObject* params ) {


    char *temp_buf;
    char hex_buf[3];
    int ret_json;
    uint8_t bytes, len = GLOBAL_BUFFER_SIZE, source, dest, new_len = 0;
    uint16_t timeout;
    boolean ret = false;
    aJsonObject *timeoutParam, *root, *retParams;

    memset( (void *) RF22Router::global_msg_buffer, 0, GLOBAL_BUFFER_SIZE );

    timeoutParam = aJson.getObjectItem( params, F( "timeout" ) );
    timeout = (uint16_t) timeoutParam->valueint;

    ret = rf22.recvfromAckTimeout( RF22Router::global_msg_buffer, &len, timeout, &source, &dest );

    root = aJson.createObject();
    aJson.addNumberToObject( root, F( "m" ), RECVFROMACKTIMEOUT );
    retParams = aJson.createObject();
    aJson.addItemToObject( root, F( "p" ), retParams );
    if( ret == true ) {
        aJson.addTrueToObject( retParams, F( "ret" ) );
        aJson.addNumberToObject( retParams, F( "s" ), (int) source );
        aJson.addNumberToObject( retParams, F( "d" ), (int) dest );
        //str_len = (uint8_t) strlen( (const char *) RF22Router::global_msg_buffer );
        //len = len > str_len ? len : str_len;
        temp_buf = (char *) calloc( ( len * 2 ) + 1, sizeof( char ) );
        for( int i = 0, j = 0; i < len; i++, j+=2 ) {
            sprintf( hex_buf, "%02x", RF22Router::global_msg_buffer[i] );
            //itoa( RF22Router::global_msg_buffer[i], hex_buf, 16 );
            temp_buf[j] = hex_buf[0];
            new_len++;
            temp_buf[j + 1] = hex_buf[1];
            new_len++;
        }
        strncpy( (char *) RF22Router::global_msg_buffer, temp_buf, GLOBAL_BUFFER_SIZE );
        free( temp_buf );
        //str_len = (uint8_t) strlen( (const char *) RF22Router::global_msg_buffer );
        //len = ( len * 2 ) > str_len ? ( len * 2 ) : str_len;
        aJson.addStringToObject( retParams, F( "b" ), (const char *) RF22Router::global_msg_buffer );
        aJson.addNumberToObject( retParams, F( "l" ), (int) new_len );
    } else {
        aJson.addFalseToObject( retParams, F( "ret" ) );
    }
    Serial.print( F( "234" ) );
    ret_json = aJson.print( root, &stream );

    aJson.deleteItem( root );
}

boolean serial_prefix_check( const __FlashStringHelper *message ) {
    const char PROGMEM *p = (const char PROGMEM *)message;
    uint8_t count = 0;
    unsigned char c;
    while( count < BUF_SIZE ) {
        c = pgm_read_byte(p++);
        RF22Router::global_msg_buffer[count] = c;
        if (c == 0) break;
            count++;
    }
    return serial_prefix_check( (char *) RF22Router::global_msg_buffer );
}


boolean serial_prefix_check( char *prefix ) {
    
    int prefix_len = strlen( prefix );
    char buf;

    while( Serial.available() < 1 );

    for( int i = 0; i < prefix_len; i++ ) {
        buf = Serial.read();
        delay( 1 );
        if( (int) buf != (int) prefix[i] ) {
            return false;
        }
    }

    return true;
}


void setup() 
{
#ifdef LCD
    lcd.begin( 20, 4 );
#endif
    pinMode( 14, OUTPUT );
    Serial.begin(19200);
}

void loop()
{
    int count = 0;
    // initialize an instance of the JsonRPC library for registering
    // exactly 1 local method
    JsonRPC rpc(16);

    char *buf;
    buf = (char *) calloc( 16, sizeof( char ) );

    rpc.registerMethod( SENDTOWAIT, &sendtoWait);
    count++;
    rpc.registerMethod( RECVFROMACK, &recvfromAck);
    count++;
    rpc.registerMethod( RECVFROMACKTIMEOUT, &recvfromAckTimeout);
    count++;

    while( serial_prefix_check( F( "234" ) ) == false );

    while( serial_prefix_check( F( "123456" ) ) == false );

    free( buf );
    Serial.println( F( "online" ) );

    if( !rf22.init() ) {

    }
    // Defaults after init are 434.0MHz, 0.05MHz AFC pull-in, modulation FSK_Rb2_4Fd36



    for( ; ; ) {

        while( serial_prefix_check( F( "234" ) ) == false );

        if (stream.available()) {
            // skip any accidental whitespace like newlines
            stream.skip();
        }

        if (stream.available()) {

            aJsonObject *msg = aJson.parse(&stream);

            rpc.processMessage(msg);

            aJson.deleteItem(msg);

        }

    }
}

