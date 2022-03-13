
option({PROJNAME}_ENABLE_CLANG_TIDY "Enable clang-tidy on build" OFF)

if({PROJNAME}_ENABLE_CLANG_TIDY)
  find_program(CLANG_TIDY_EXE
               NAMES clang-tidy
               DOC "Path to clang-tidy executable")
  if(NOT CLANG_TIDY_EXE)
      message(STATUS "WARNING: clang-tidy Not found.")
  else()
      message(STATUS "clang-tidy Enabled: ${CLANG_TIDY_EXE}")
      set(CMAKE_CXX_CLANG_TIDY
          "${CLANG_TIDY_EXE}"
          -header-filter={projname}/)
  endif()
else()
  message(STATUS "clang-tidy Disabled")
endif()
