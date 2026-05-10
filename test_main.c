#include "chibicc.h"

// Define basic globals since we're stubbing
StringArray include_paths;
bool opt_fpic = false;
bool opt_fcommon = true;
char *base_file = "test.c";
char *output_file = "a.s";

int main() {
    return 0;
}
