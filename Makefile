CFLAGS=-std=c11 -g -fno-common -Wall -Wno-switch -I src/cy16cc
SRCS=$(wildcard src/cy16cc/*.c)
OBJS=$(SRCS:.c=.o)

chibicc: $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

clean:
	rm -f chibicc $(OBJS)
