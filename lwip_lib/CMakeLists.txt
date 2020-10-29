cmake_minimum_required(VERSION 3.8)

project(lwip C)

set (BUILD_SHARED_LIBS ON)

if (NOT CMAKE_SYSTEM_NAME STREQUAL "Linux" AND NOT CMAKE_SYSTEM_NAME STREQUAL "GNU")
    message(FATAL_ERROR "Lwip shared library is only working on Linux or the Hurd")
endif()

set(LWIP_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../lwip)
#include(${LWIP_DIR}/contrib/ports/CMakeCommon.cmake)

set (LWIP_DEFINITIONS -DLWIP_DEBUG)
set (LWIP_INCLUDE_DIRS
    "${LWIP_DIR}/src/include"
    "${LWIP_DIR}/contrib/apps/ping"
    "${CMAKE_CURRENT_SOURCE_DIR}/"
    "${CMAKE_CURRENT_SOURCE_DIR}/include"

)

set (INT_SOURCES 
    "${CMAKE_CURRENT_SOURCE_DIR}/src/perf.c" 
    "${CMAKE_CURRENT_SOURCE_DIR}/src/sys_arch.c"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/sio.c"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ping_result.c"
)

set (PING_SOURCES 
    "${LWIP_DIR}/contrib/apps/ping/ping.c"
    "${CMAKE_CURRENT_SOURCE_DIR}/src/ping_result.c"
)

#include(${LWIP_CONTRIB_DIR}/ports/unix/Filelists.cmake)
include(${LWIP_DIR}/src/Filelists.cmake)

add_library(lwip ${lwipnoapps_SRCS} ${lwipcontribportunix_SRCS} ${lwipcontribportunixnetifs_SRCS} ${INT_SOURCES} ${PING_SOURCES})
target_compile_options(lwip PRIVATE ${LWIP_COMPILER_FLAGS})
target_compile_definitions(lwip PRIVATE ${LWIP_DEFINITIONS} ${LWIP_MBEDTLS_DEFINITIONS})
target_include_directories(lwip PRIVATE ${LWIP_INCLUDE_DIRS} ${LWIP_MBEDTLS_INCLUDE_DIRS})
target_link_libraries(lwip ${LWIP_SANITIZER_LIBS})

#find_library(LIBPTHREAD pthread)
#target_link_libraries(lwip ${LIBPTHREAD})
