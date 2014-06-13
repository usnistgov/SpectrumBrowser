INCLUDE(FindPkgConfig)
PKG_CHECK_MODULES(PC_MYBLOCKS myblocks)

FIND_PATH(
    MYBLOCKS_INCLUDE_DIRS
    NAMES myblocks/api.h
    HINTS $ENV{MYBLOCKS_DIR}/include
        ${PC_MYBLOCKS_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREEFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    MYBLOCKS_LIBRARIES
    NAMES gnuradio-myblocks
    HINTS $ENV{MYBLOCKS_DIR}/lib
        ${PC_MYBLOCKS_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
)

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(MYBLOCKS DEFAULT_MSG MYBLOCKS_LIBRARIES MYBLOCKS_INCLUDE_DIRS)
MARK_AS_ADVANCED(MYBLOCKS_LIBRARIES MYBLOCKS_INCLUDE_DIRS)

