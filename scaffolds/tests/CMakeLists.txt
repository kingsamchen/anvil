CPMAddPackage("gh:onqtam/doctest#v2.4.8")

add_executable({projname}_test)

target_sources({projname}_test
  PRIVATE
    test_main.cpp
)

target_link_libraries({projname}_test
  PRIVATE
    doctest
)

# {projname}_apply_common_compile_options({projname}_test)

# if(MSVC)
#   get_target_property(test_FILES {projname}_test SOURCES)
#   source_group("{projname}_test" FILES ${test_FILES})
#
#   if({PROJNAME}_USE_MSVC_PARALLEL_BUILD)
#     {projname}_apply_msvc_parallel_build({projname}_test)
#   endif()
#   if({PROJNAME}_USE_MSVC_STATIC_ANALYSIS)
#     {projname}_apply_msvc_static_analysis({projname}_test)
#   endif()
# else()
#   if({PROJNAME}_USE_SANITIZER)
#     {projname}_apply_sanitizer({projname}_test)
#   endif()
# endif()

add_test(NAME tests COMMAND {projname}_test)
