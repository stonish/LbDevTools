macro(assert_strequal var value)
  if(NOT "${${var}}" STREQUAL "${value}")
    message(FATAL_ERROR "wrong value for ${var}: found '${${var}}', expected '${value}'")
  endif()
endmacro()

macro(assert)
  if(NOT (${ARGV}))
    message(FATAL_ERROR "(${ARGV}) is false")
  endif()
endmacro()
