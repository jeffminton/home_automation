// rf22_mesh_client.pde
// -*- mode: C++ -*-
// Example sketch showing how to create a simple addressed, routed reliable messaging client
// with the RF22Mesh class.
// It is designed to work with the other examples rf22_mesh_server*
// Hint: you can simulate other network topologies by setting the 
// RF22_TEST_NETWORK define in RF22Router.h

// Mesh has much greater memory requirements, and you may need to limit the
// max message length to prevent wierd crashes

#define DELAY_TIME 0
#define CLIENT

#include <RF22AES.h>
#include <RF22Mesh.h>
#include <SPI.h>
#include <aJSON.h>
#include "client.h"
#include <MemoryFree.h>

//const node_type_t me = GARAGE_DOOR;

RF22AES rf22_aes( (uint8_t) 0 );



//#define LCD
#define PRINT

#ifdef LCD
LiquidCrystal lcd( 8, 9, 4, 5, 6, 7 );

void freeMem(char* message, int delay_time = 0) {
#ifdef PRINT
    lcd.clear();
    lcd.print( message );
    lcd.print( " :" );
    lcd.setCursor( 0, 1 );
    lcd.print( freeMemory( ) );
    delay( delay_time );
#endif
}

void freeMem(char letter, int delay_time = DELAY_TIME) {
    lcd.clear();
    lcd.print( letter );
    lcd.print( " :" );
    lcd.setCursor( 0, 1 );
    lcd.print( freeMemory( ) );
    delay( delay_time );
}

void freeMem( int value, int delay_time = 0) {
#ifdef PRINT
    lcd.clear();
    lcd.print( value );
    lcd.print( " :" );
    lcd.setCursor( 0, 1 );
    lcd.print( freeMemory( ) );
    delay( delay_time );
#endif
}


void freeMem( const __FlashStringHelper *message, int delay_time = 0 ) {
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


void print( char *message, int delay_time = 0 ) {
#ifdef PRINT
    lcd.clear();
    lcd.print( message );
    delay( delay_time );
#endif
}


void print( const __FlashStringHelper *message, int delay_time = 0 ) {
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

void freeMem(char* message, int delay_time = 0) {
#ifdef PRINT
    Serial.print( message );
    Serial.print( F( " :" ) );
    Serial.println( freeMemory() );
#endif
}

void freeMem(char letter, int delay_time = DELAY_TIME) {
    Serial.print( letter );
    Serial.print( " :" );
    Serial.println( freeMemory( ) );
}

void freeMem( int value, int delay_time = 0 ) {
#ifdef PRINT
    Serial.print( value );
    Serial.print( F( " :" ) );
    Serial.println( freeMemory() );
#endif
}



void print( char* message, int delay_time = 0 ) {
#ifdef PRINT
    Serial.println( message );
#endif
}


void freeMem( const __FlashStringHelper *message, int delay_time = 0 ) {
#ifdef PRINT
    Serial.print( message );
    Serial.print( F( " :" ) );
    Serial.println( freeMemory() );
#endif
}


void print( const __FlashStringHelper *message, int delay_time = 0 ) {
#ifdef PRINT
    Serial.println( message );
#endif
}

void freeMemStr(char* message) {
#ifdef PRINT
    Serial.print( message );
    Serial.print( F( " :" ) );
    Serial.println( freeMemory() );
#endif
}

void freeMemChr(char letter) {
    Serial.print( letter );
    Serial.print( " :" );
    Serial.println( freeMemory( ) );
}

void freeMemInt( int value ) {
#ifdef PRINT
    Serial.print( value );
    Serial.print( F( " :" ) );
    Serial.println( freeMemory() );
#endif
}



void print( char* message ) {
#ifdef PRINT
    Serial.println( message );
#endif
}


void freeMemFStr( const __FlashStringHelper *message ) {
#ifdef PRINT
    Serial.print( message );
    Serial.print( F( " :" ) );
    Serial.println( freeMemory() );
#endif
}


void print( const __FlashStringHelper *message ) {
#ifdef PRINT
    Serial.println( message );
#endif
}


#endif


unsigned long analog_sample( int pin ) {
    unsigned long a_val = 0;

    for( int i = 0; i < 4096; i++ ) {
        a_val += analogRead( pin );
    }

    return a_val >> 6;
}


// In this small artifical network of 4 nodes,
void setup() 
{
    //analogReference( INTERNAL );
    Serial.begin( 115200 );
    Serial.setTimeout( 3600000 );
    Serial.println( F( "online" ) );
    randomSeed( analogRead( 5 ) );
    Serial.print( F( "RF22AES size: " ) );
    Serial.println( sizeof( RF22AES ) );
    Serial.print( F( "RF22Mesh size: " ) );
    Serial.println( sizeof( RF22Mesh ) );
    Serial.print( F( "RF22Router size: " ) );
    Serial.println( sizeof( RF22Router ) );
    Serial.print( F( "RF22ReliableDatagram size: " ) );
    Serial.println( sizeof( RF22ReliableDatagram ) );
    Serial.print( F( "RF22Datagram size: " ) );
    Serial.println( sizeof( RF22Datagram ) );
    Serial.print( F( "RF22 size: " ) );
    Serial.println( sizeof( RF22 ) );
    Serial.print( F( "GenericSPIClass size: " ) );
    Serial.println( sizeof( GenericSPIClass ) );


    if( !rf22_aes.init() ) {
        Serial.println( "rf22 init failed" );
    } else {
        Serial.println( "rf22 init succeded" );       
    }
}


void loop()
{
    Serial.print( "node adress: " );
    Serial.println( rf22_aes.getThisAddress() );

    delay( 1000000 );
}

