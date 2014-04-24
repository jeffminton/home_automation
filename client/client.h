
#ifndef CLIENT
#define CLIENT
#endif

typedef enum node_type {
    GARAGE_DOOR,
    THERMOSTAT_UPSTAIRS
} node_type_t;

typedef enum message_type {
    ADDRESS_REQUEST,
    SEND_COMMAND_REQ,
    COMMAND,
    SEND_COMMAND_RESP,
    COMMAND_ACK,
    SYNC_KEY,
    SYNC_IV,
    ADDRESS_GRANT
} message_type_t;


typedef struct {
    uint8_t key[16];
    uint8_t iv[16];
} key_set_t;


