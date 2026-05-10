#ifndef _STDDEF_H
#define _STDDEF_H

typedef unsigned short size_t;
typedef signed short ptrdiff_t;

#define NULL ((void *)0)

#define offsetof(type, member) ((size_t)&(((type *)0)->member))

#endif
