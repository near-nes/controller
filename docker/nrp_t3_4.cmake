set(COVERAGE OFF CACHE BOOL "Evaluate coverage")
set(BUILD_RST OFF CACHE BOOL "Build rst files for the documentation")


set(ENABLE_GAZEBO OFF CACHE BOOL "Enable gazebo support")
set(BUILD_GAZEBO_ENGINE_SERVER OFF CACHE BOOL "Disable nest-simulator engines server side")
set(ENABLE_NEST OFF CACHE BOOL "Enable nest support")
set(BUILD_NEST_ENGINE_SERVER OFF CACHE BOOL  "Disable nest-simulator engines server side")
set(ENABLE_EDLUT OFF CACHE BOOL "Enable EDLUT support")
set(ENABLE_SPINNAKER OFF CACHE BOOL "Enable Spinnaker support")


set(ENABLE_ROS OFF CACHE BOOL "Enable ROS support")
set(ENABLE_MQTT OFF CACHE BOOL "Enable MQTT support")

set(ENABLE_TESTING OFF CACHE STRING "Enable tests")
set(ENABLE_EXAMPLES_TESTING FOO CACHE STRING "Enable running of examples in tests")
