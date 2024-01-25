find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_SATELLITESPLUS gnuradio-satellitesPlus)

FIND_PATH(
    GR_SATELLITESPLUS_INCLUDE_DIRS
    NAMES gnuradio/satellitesPlus/api.h
    HINTS $ENV{SATELLITESPLUS_DIR}/include
        ${PC_SATELLITESPLUS_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_SATELLITESPLUS_LIBRARIES
    NAMES gnuradio-satellitesPlus
    HINTS $ENV{SATELLITESPLUS_DIR}/lib
        ${PC_SATELLITESPLUS_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-satellitesPlusTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_SATELLITESPLUS DEFAULT_MSG GR_SATELLITESPLUS_LIBRARIES GR_SATELLITESPLUS_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_SATELLITESPLUS_LIBRARIES GR_SATELLITESPLUS_INCLUDE_DIRS)
