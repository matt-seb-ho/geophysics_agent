**Context:** Developerguide > Contributing > CodeStyle > File Names

## File Names
- File names should be [PascalCase ](https://en.wikipedia.org/wiki/Camel_case)_.
- C++ header files are always named with a file extension of  \*.hpp.
- C++ header implementation files, which contain templated or inline function definitions, are always named \*Helpers.hpp.
- C++ source files are always named with a file extension of  \*.cpp.
- C++ class declarations and definitions are contained files with identical names, except for the extensions.
- C++ free function headers and source files are declared/defined in files with identical names, except for the extension.

For example, a class named "Foo" may be declared in a file named "Foo.hpp", with inline/templated functions
defined in "FooHelpers.hpp", with the source implementation contained in Foo.cpp.

.. warning[``
  There should not be identical filenames that only differ by case. Some filesystems are not case-sensitive,
  and worse, some filesystems such as MacOSX are case-preserving but not case sensitive.
