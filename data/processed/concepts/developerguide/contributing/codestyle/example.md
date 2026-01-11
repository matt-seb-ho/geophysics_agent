**Context:** Developerguide > Contributing > CodeStyle > Example

## Example
One example of would be a for a class named "Foo", the declaration would be in a header file named "Foo.hpp"

[`c
  /*
   * Foo.hpp
   */

  namespace bar
  {

  class Foo
  {
  public:
    Foo();
  private:
    double m_myDouble;
  }
  }

and a source file named "Foo.cpp"

``c
  /*
   * Foo.cpp
   */
  namespace bar
  {
    Foo::Foo():
      m_myDouble(0.0)
    {
      // some constructor stuff
    }
  }

# Const Keyword
#. All functions and accessors should be declared as "const" functions unless modification to the class is required.
#. In the case of accessors, both a "const" and "non-const" version should be provided.
#. The const keyword should be placed in the location read by the compiler, which is right to left.

The following examples are provided:

   ```c
      int a=0; // regular int
      int const b = 0; // const int
      int * const c = &a; // const pointer to non const int
      int const * const d = &b; // const pointer to const int
      int & e = a; // reference to int
      int const & f = b; // reference to const int


# Code Format
GEOS applies a variant of the
`BSD/Allman Style ](https://en.wikipedia.org/wiki/Indentation_style#Allman_style)_.
Key points to the GEOS style are:

#. Opening braces (i.e. "{") go on the next line of any control statement, and are not indented from the control statement.
#. NO TABS. Only spaces. In case it isn't clear ... NO TABS!
#. 2-space indentation

   ``c
      for( int i=0 ; i<10 ; ++i )
      {
        std::cout << "blah" << std::endl;
      }

#. Try to stay under 100 character line lengths. To achieve this apply these rules in order
#. Align function declaration/definitions/calls on argument list
#. Break up return type and function definition on new line
#. Break up scope resolution operators

   ``c
    void
    SolidMechanicsLagrangianFEM::
    TimeStepExplicit( real64 const& time_n,
                      real64 const& dt,
                      const int cycleNumber,
                      DomainPartition * const domain )
    {
      code here
    }

As part of the continuous integration testing, this GEOS code style is enforced via the uncrustify tool.
While quite extensive, uncrustify does not enforce every example of the preferred code style.
In cases where uncrusitfy is unable to enforce code style, it will ignore formatting rules.
In these cases it is acceptable to proceed with pull requests, as there is no logical recourse.

# Header Guards
Header guard names should consist of the name `GEOS`, followed by the component name (e.g. dataRepository),
and finally the name of the header file.
All characters in the macro should be capitalized.
