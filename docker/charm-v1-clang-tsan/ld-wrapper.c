#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv) {
    (void)argc;
    unsetenv("LD_LIBRARY_PATH");
    argv[0] = "/usr/bin/ld";
    execv(argv[0], argv);
    return 127;
}
