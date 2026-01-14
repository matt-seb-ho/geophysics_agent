**Context:** Linearalgebra > DofManager > Methods

# Methods
The main methods of `DoF Manager` are:

* `setDomain`: sets the domain containing mesh bodies to operate on
  `domain` identifies the global domain

 ``c
  void setDomain( DomainPartition * const domain );

* `addField`: creates a new set of DoF, labeled `field`, with specific
  `location`.
  Default number of `components` is `1`, like for pressure in flux.
  Default `regions` is the empty string, meaning all domain.

 ``c
  void addField( string const & fieldName,
                 Location const location,
                 localIndex const components,
                 string_array const & regions );

* `addCoupling`: creates a coupling between two fields (`rowField` and
  `colField`) according to a given `connectivity` in the regions defined by `regions`.
  Both fields (row and column) must have already been defined on the regions where is required the coupling among them.
  Default value for `regions` is the whole intersection between the regions where the first and the second fields are defined.
  This method also creates the coupling between `colField` and `rowField`, i.e. the transpose of the rectangular sparsity pattern.
  This default behaviour can be disabled by passing `symmetric = false`.

 ``c
  void addCoupling( string const & rowField,
                    string const & colField,
                    Connectivity const connectivity,
                    string_array const & regions,
                    bool const symmetric );

* `reorderByRank`: finish populating field and coupling information and apply DoF
  re-numbering

 ``c
  void reorderByRank();

* `getKey`: returns the "key" associated with the field, that can be used to access the index array on the mesh object manager corresponding to field's location.

 ``c
  string const & getKey( string const & fieldName );

* `clear`: removes all fields, releases memory and re-opens the DofManager

 ``c
  void clear();

* `setSparsityPattern`: populates the sparsity for the given
  `rowField` and `colField` into `matrix`.
  Closes the matrix if `closePattern` is `true`.

 ``c
  void setSparsityPattern( MATRIX & matrix,
                           string const & rowField,
                           string const & colField,
                           bool closePattern = true) const;

* `setSparsityPattern`: populates the sparsity for the full system matrix into `matrix`.
  Closes the matrix if `closePattern` is `true`.

 ``c
  void setSparsityPattern( MATRIX & matrix,
                           bool closePattern = true ) const;

* `numGlobalDofs`: returns the total number of DoFs across all processors for
  the specified name `field` (if given) or all fields (if empty).

 ``c
  globalIndex numGlobalDofs( string const & field = "" ) const;

* `numLocalDofs`: returns the number of DoFs on this process for the
  specified name `field` (if given) or all fields (if empty).

 ``c
  localIndex numLocalDofs( string const & field = "" ) const;

* `printFieldInfo`: prints a short summary of declared fields and coupling to the output stream `os`.

 ```c
  void printFieldInfo( std::ostream & os = std::cout ) const;
