# syntax=docker/dockerfile:1.7
FROM w8-biayn-polyglot-cpp@sha256:4cff5e0d746a95fc3cf787ce7e1519485ca521ad1040ccbedb314d958e967991
LABEL charm.base_image_sha256="4cff5e0d746a95fc3cf787ce7e1519485ca521ad1040ccbedb314d958e967991"
LABEL charm.compiler="clang-18.1.3-private-interpreter"

COPY --from=llvm bin/clang /opt/llvm/bin/clang
COPY --from=llvm lib/libclang-cpp.so.18.1 /opt/llvm/lib/libclang-cpp.so.18.1
COPY --from=llvm lib/libLLVM.so.1 /opt/llvm/lib/libLLVM.so.1
COPY --from=llvm lib/libLLVM.so.1 /opt/llvm/lib/libLLVM.so.18.1
COPY --from=llvm lib/clang/18 /opt/llvm/lib/clang/18

COPY --from=hostlib ld-linux-x86-64.so.2 /opt/llvm/lib/ld-linux.so
COPY --from=hostlib libc.so.6 /opt/llvm/lib/libc.so.6
COPY --from=hostlib libm.so.6 /opt/llvm/lib/libm.so.6
COPY --from=hostlib libstdc++.so.6.0.33 /opt/llvm/lib/libstdc++.so.6
COPY --from=hostlib libgcc_s.so.1 /opt/llvm/lib/libgcc_s.so.1
COPY --from=hostlib libffi.so.8.1.4 /opt/llvm/lib/libffi.so.8
COPY --from=hostlib libedit.so.2.0.72 /opt/llvm/lib/libedit.so.2
COPY --from=hostlib libz.so.1.3 /opt/llvm/lib/libz.so.1
COPY --from=hostlib libzstd.so.1.5.5 /opt/llvm/lib/libzstd.so.1
COPY --from=hostlib libtinfo.so.6.4 /opt/llvm/lib/libtinfo.so.6
COPY --from=hostlib libxml2.so.2.9.14 /opt/llvm/lib/libxml2.so.2
COPY --from=hostlib libbsd.so.0.12.1 /opt/llvm/lib/libbsd.so.0
COPY --from=hostlib libicuuc.so.74.2 /opt/llvm/lib/libicuuc.so.74
COPY --from=hostlib libicudata.so.74.2 /opt/llvm/lib/libicudata.so.74
COPY --from=hostlib liblzma.so.5.4.5 /opt/llvm/lib/liblzma.so.5
COPY --from=hostlib libmd.so.0.1.0 /opt/llvm/lib/libmd.so.0
COPY --from=hostlib libresolv.so.2 /opt/llvm/lib/libresolv.so.2

RUN printf '/opt/llvm/lib/ld-linux.so\0' > /tmp/charm-clang-interp \
    && objcopy --update-section .interp=/tmp/charm-clang-interp /opt/llvm/bin/clang
COPY docker/charm-v1-clang-tsan/ld-wrapper.c /tmp/charm-ld-wrapper.c
RUN cc -static -O2 /tmp/charm-ld-wrapper.c -o /opt/llvm/bin/ld-wrapper
COPY docker/charm-v1-clang-tsan/c++ /usr/local/bin/c++
RUN chmod 0755 /usr/local/bin/c++
