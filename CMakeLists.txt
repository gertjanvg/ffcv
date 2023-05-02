cmake_minimum_required( VERSION 3.13 )

project(libffcv)
set(CMAKE_CXX_STANDARD 11)

find_package( OpenCV REQUIRED )
include_directories( ${OpenCV_INCLUDE_DIRS} )

find_package( Python3 REQUIRED Development )
include_directories( ${Python_INCLUDE_DIRS} )

set(SOURCE_FILES libffcv/libffcv.cpp)
add_executable(libffcv ${SOURCE_FILES})

target_link_libraries( libffcv ${OpenCV_LIBS} )
target_link_libraries( libffcv ${Python_LIBRARIES} )
