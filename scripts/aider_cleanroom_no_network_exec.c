/* Execute a command under a fail-closed seccomp policy that denies sockets.
 *
 * Modal's gVisor runtime rejects the loopback setup performed by a nested
 * network namespace. Denying socket and socketpair at the syscall boundary
 * gives the generated compiler/test process no network primitive while keeping
 * Bubblewrap's mount, PID, IPC, UTS, and environment isolation usable.
 */

#include <errno.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <sys/prctl.h>
#include <sys/syscall.h>

#if !defined(__x86_64__)
#error "The clean-room Modal image is provenance-bound to x86_64"
#endif

#define DENY_SYSCALL(number)                                                   \
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, (number), 0, 1),                      \
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | (EPERM & SECCOMP_RET_DATA))

static int install_no_network_filter(void) {
    struct sock_filter filter[] = {
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, arch)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL_PROCESS),
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
        DENY_SYSCALL(__NR_socket),
        DENY_SYSCALL(__NR_socketpair),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog program = {
        .len = (unsigned short)(sizeof(filter) / sizeof(filter[0])),
        .filter = filter,
    };

    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) {
        return -1;
    }
    if (prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &program) != 0) {
        return -1;
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fputs("usage: cleanroom-no-network-exec COMMAND [ARG...]\n", stderr);
        return 125;
    }
    if (install_no_network_filter() != 0) {
        perror("failed to install clean-room seccomp network policy");
        return 125;
    }
    execvp(argv[1], &argv[1]);
    perror("failed to execute clean-room command");
    return 125;
}
