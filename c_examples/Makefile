CC ?= gcc
CFLAGS ?= -O3 -Wall -Wextra

TARGETS = blink_axi_gpio blink_d3_mio load_bit

all: $(TARGETS)

blink_axi_gpio: blink_axi_gpio.c
	$(CC) $(CFLAGS) -o $@ $<

blink_d3_mio: blink_d3_mio.c
	$(CC) $(CFLAGS) -o $@ $<

load_bit: load_bit.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	rm -f $(TARGETS)

.PHONY: all clean
