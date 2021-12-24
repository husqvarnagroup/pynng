# build the pynng interface.
#
# This script assumes the nng library has already been built; the setup.py
# script should ensure that it is built before running.  It looks in this file
# to see what the expected object file is based on the platform.
from cffi import FFI
import os
from subprocess import check_call
import sys

ffibuilder = FFI()

if sys.platform == 'win32':
    objects = ['./nng/build/Release/nng.lib']

    mbedtls_dir = './mbedtls/build/library/Release'
    objects += [
        mbedtls_dir + "/mbedtls.lib",
        mbedtls_dir + "/mbedx509.lib",
        mbedtls_dir + "/mbedcrypto.lib",
    ]

    # system libraries determined to be necessary through trial and error
    libraries = ['Ws2_32', 'Advapi32']
else:
    check_call('prefix=/usr ./generate_api.sh', shell=True)
    objects = []
    libraries = ['pthread', 'nng']
    machine = os.uname().machine
    # this is a pretty heuristic... but let's go with it anyway.
    # it would be better to get linker information from cmake somehow.
    if not ('x86' in machine or 'i386' in machine or 'i686' in machine):
        libraries.append('atomic')


ffibuilder.set_source(
    "pynng._nng",
    r""" // passed to the real C compiler,
         // contains implementation of things declared in cdef()
         #define NNG_DECL
         #define NNG_SHARED_LIB
         #include <nng/nng.h>
         #include <nng/protocol/bus0/bus.h>
         #include <nng/protocol/pair0/pair.h>
         #include <nng/protocol/pair1/pair.h>
         #include <nng/protocol/pipeline0/pull.h>
         #include <nng/protocol/pipeline0/push.h>
         #include <nng/protocol/pubsub0/pub.h>
         #include <nng/protocol/pubsub0/sub.h>
         #include <nng/protocol/reqrep0/req.h>
         #include <nng/protocol/reqrep0/rep.h>
         #include <nng/protocol/survey0/respond.h>
         #include <nng/protocol/survey0/survey.h>
         #include <nng/supplemental/tls/tls.h>
         #include <nng/transport/tls/tls.h>

    """,
    libraries=libraries,
    # library_dirs=['nng/build/Debug',],
    # (more arguments like setup.py's Extension class:
    extra_objects=objects,
)


with open('nng_api.h') as f:
    api = f.read()

callbacks = """
    // aio callback: https://nanomsg.github.io/nng/man/tip/nng_aio_alloc.3
    extern "Python" void _async_complete(void *);

    // nng_pipe_notify callback:
    // https://nanomsg.github.io/nng/man/tip/nng_pipe_notify.3
    extern "Python" void _nng_pipe_cb(nng_pipe, nng_pipe_ev, void *);
"""
ffibuilder.cdef(api + callbacks)

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
