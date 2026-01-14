**Context:** Developerguide > Contributing > Doxygen > How to document

## How to document
The following rules and conventions are used. Some are stricter than others.

#. We use `@`-syntax for all Doxygen commands (e.g. `@brief` instead of `\\brief`).

#. Entities such as type aliases and member variables that typically only require a brief description,
   can have a single-line documentation starting with `///`.

   * `@brief` is not required for single-line comments.

#. Entities such as classes and functions that typically require either detailed explanation or parameter documentation,
   are documented with multiline comment blocks.

   * `@brief` is required for comment blocks.

#. Brief and detailed descriptions should be complete sentences (i.e. start with a capital letter and end with a dot).

#. Prefer concise wording in `@brief`, e.g. "Does X." instead of "This is a function that does X."

#. All functions parameters and return values must be explicitly documented via `@param` and `@return`.

   * An exception to this rule seem to be copy/move constructor/assignment, where parameter documentation can be omitted.

#. Add `[in]` and `[out]` tags to function parameters, as appropriate.

#. Function and template parameter descriptions are not full sentences (i.e. not capitalized nor end with a dot).

#. For hierarchies with virtual inheritance, document base virtual interfaces rather than overriding implementations.

#. Documented functions cannot use `GEOS_UNUSED_ARG()` in their declarations.

#. For empty virtual base implementations that use `GEOS_UNUSED_ARG(x)` to remove compiler warnings, use one of two options:

   * move empty definition away (e.g. out of class body) and keep `GEOS_UNUSED_ARG(x)` in definition only;
   * put `GEOS_UNUSED_VAR(x)` into the inline empty body.

#. For large classes, logically group functions using member groups via `///@{` and `///@}` and give them group names
   and descriptions (if needed) via a `@name` comment block. Typical groups may include:

   * constructors/destructor/assignment operators;
   * getter/setter type functions;
   * overridable virtual functions;
   * any other logically coherent groups (functions related to the same aspect of class behavior).

#. In-header implementation details (e.g. template helpers) often shouldn't appear in user documentation.
   Wrap these into `internal` namespace.

#. Use `/// @cond DO_NOT_DOCUMENT` and `/// @endcond` tags to denote a section of public API that should not be
   documented for some reason. This should be used rarely and selectively. An example is in-class helper structs
   that must be public but that user should not refer to explicitly.

# Example
   .. code-block:: c++

      /// This is a documented macro
      #define USEFUL_MACRO

      /**
       * @brief Short description.
       * @tparam    T type of input value
       * @param[in] x input value explanation
       * @return      return value explanation
       *
       * Detailed description goes here.
       *
       * @note A note warning users of something unexpected.
       */
      template<typename T>
      int Foo( T const & x );

      /**
      * @brief Class for showing Doxygen.
      * @tparam T type of value the class operates on
      *
      * This class does nothing useful except show how to use Doxygen.
      */
      template<typename T>
      class Bar
      {
      public:

        /// A documented member type alias.
        using size_type = typename std::vector<T>::size_type;

        /**
         * @name Constructors/destructors.
         */
        ///@{

        /**
         * @brief A documented constructor.
         * @param value to initialize the object
         */
        explicit Bar( T t );

        /**
         * @brief A deleted, but still documented copy constructor.
         * @param an optionally documented parameter
         */
        Bar( Bar const & source ) = delete;

        /**
         * @brief A defaulted, but still documented move constructor.
         * @param an optionally documented parameter
         */
        Bar( Bar const & source ) = default;

        /**
         * @brief A documented desctructor.
         * virtual ~Bar() = default;
         */

        ///@}

        /**
         * @name Getters for stored value.
         */
        ///@{

        /**
         * @brief A documented public member function.
         * @return a reference to contained value
         */
        T & getValue();

        /**
         * @copydoc getValue()
         */
        T const & getValue() const;

        ///@}

      protected:

        /**
         * @brief A documented protected pure virtual function.
         * @param[in]  x the input value
         * @param[out] y the output value
         *
         * Some detailed explanation for users and implementers.
         */
        virtual void doSomethingOverridable( int const x, T & y ) = 0;

        /// @cond DO_NOT_DOCUMENT
        // Some stuff we don't want showing up in Doxygen
        struct BarHelper
        {};
        /// @endcond

      private:

        /// An optionally documented (not enforced) private member.
        T m_value;

      };

# Current Doxygen
[Link to Doxygen Class directory ](../../../../doxygen_output/html/classes.html)_

Direct links to some useful class documentation:

[Group API ](../../../../doxygen_output/html/classgeos_1_1data_repository_1_1_group.html)

[Wrapper API ](../../../../doxygen_output/html/classgeos_1_1data_repository_1_1_wrapper.html)

[ObjectManagerBase API ](../../../../doxygen_output/html/classgeos_1_1_object_manager_base.html)

[MeshLevel API ](../../../../doxygen_output/html/classgeos_1_1_mesh_level.html)

[NodeManager API ](../../../../doxygen_output/html/classgeos_1_1_node_manager.html)

[FaceManager API ](../../../../doxygen_output/html/classgeos_1_1_face_manager.html)