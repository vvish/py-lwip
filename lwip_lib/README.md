# lwIP shared library

## Summary
The folder contains configuration file, architecture specific code and 
cmake definitions required to build lwIP as shared
library.

The content is based on example from `lwip/contrib/ports/unix/lib`


## Building the library

To build lwIP as library from this folder: 

```bash
mkdir build
cd build
cmake ..
make all
```

Or from the project root folder:

```bash
make lwip-lib
```

The output lib is named `liblwip.so`

## lwIP configuration

The configuration file is `lwipopts.h` containing the values that will
override the defaults during lwIP library build.

Curent settings in the lwipopts.h specify lwIP build without OS support.


