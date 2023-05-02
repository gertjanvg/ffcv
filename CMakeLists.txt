cmake_minimum_required( VERSION 3.13 )

project(ffcv)
set(CMAKE_CXX_STANDARD 11)
set(Python3_FIND_VIRTUALENV ONLY)

find_package( OpenCV REQUIRED )
include_directories( ${OpenCV_INCLUDE_DIRS} )

find_package( Python3 REQUIRED Interpreter Development )
include_directories( ${Python3_INCLUDE_DIRS} )

find_package( libjpeg-turbo REQUIRED )

set(SOURCE_FILES libffcv/libffcv.cpp)
add_library(ffcv SHARED ${SOURCE_FILES})

target_link_libraries( ffcv PUBLIC ${OpenCV_LIBS} ${Python3_LIBRARIES} libjpeg-turbo::turbojpeg )
