
#ifdef __cplusplus
extern "C" {
#endif

#include "lwip/opt.h"

#include "lwip/debug.h"

static ping_callback ping_cbk = NULL;

void set_ping_callback(ping_callback callback) 
{
    LWIP_DEBUGF(PING_DEBUG, ("ping: setting the result callback\n"));
    ping_cbk = callback;
}

void ping_result(u8_t result)
{
    LWIP_DEBUGF(PING_DEBUG, ("ping: result received = %d\n", (int)result));

    if (ping_cbk) {
        ping_cbk(result);
    }
}

#ifdef __cplusplus
}
#endif
