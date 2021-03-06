#!/usr/bin/make -f
# Makefile for rtmempool #
# ---------------------- #
# Created by falkTX
#

include ../../Makefile.mk

# --------------------------------------------------------------

BUILD_C_FLAGS += -pthread
BUILD_C_FLAGS += -I. -I../../includes

ifeq ($(CARLA_PLUGIN_SUPPORT),true)
BUILD_C_FLAGS += -DWANT_LV2
endif

LINK_FLAGS    += -lpthread

OBJS         = rtmempool.c.o
OBJS_posix32 = rtmempool.c.posix32.o
OBJS_posix64 = rtmempool.c.posix64.o
OBJS_win32   = rtmempool.c.win32.o
OBJS_win64   = rtmempool.c.win64.o

# --------------------------------------------------------------

all: ../rtmempool.a

posix32: ../rtmempool.posix32.a
posix64: ../rtmempool.posix64.a
win32:   ../rtmempool.win32.a
win64:   ../rtmempool.win64.a

# --------------------------------------------------------------

../rtmempool.a: $(OBJS)
	$(AR) rs $@ $^

../rtmempool.posix32.a: $(OBJS_posix32)
	$(AR) rs $@ $^

../rtmempool.posix64.a: $(OBJS_posix64)
	$(AR) rs $@ $^

../rtmempool.win32.a: $(OBJS_win32)
	$(AR) rs $@ $^

../rtmempool.win64.a: $(OBJS_win64)
	$(AR) rs $@ $^

../rtmempool.dll: $(OBJS)
	$(CXX) $^ -shared $(LINK_FLAGS) -o $@ $(CMD_STRIP) $@

../rtmempool.dylib: $(OBJS)
	$(CXX) $^ -dynamiclib $(LINK_FLAGS) -o $@ $(CMD_STRIP) $@

../rtmempool.so: $(OBJS)
	$(CXX) $^ -shared $(LINK_FLAGS) -o $@ $(CMD_STRIP) $@

# --------------------------------------------------------------

rtmempool.c.o: rtmempool.c
	$(CC) $< $(BUILD_C_FLAGS) -c -o $@

rtmempool.c.posix32.o: rtmempool.c
	$(CC) $< $(BUILD_C_FLAGS) $(32BIT_FLAGS) -c -o $@

rtmempool.c.posix64.o: rtmempool.c
	$(CC) $< $(BUILD_C_FLAGS) $(64BIT_FLAGS) -c -o $@

rtmempool.c.win32.o: rtmempool.c
	$(CC) $< $(BUILD_C_FLAGS) -DPTW32_STATIC_LIB $(32BIT_FLAGS) -c -o $@

rtmempool.c.win64.o: rtmempool.c
	$(CC) $< $(BUILD_C_FLAGS) -DPTW32_STATIC_LIB $(64BIT_FLAGS) -c -o $@

# --------------------------------------------------------------

clean:
	rm -f *.o ../rtmempool.*

debug:
	$(MAKE) DEBUG=true
