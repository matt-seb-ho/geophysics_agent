**Context:** Developerguide > Keycomponents > AddingNewSolver > Implementation File

## Implementation File
As we have seen in :ref:`Implementation`, the first place where to implement a new register from XML input is
in the constructor. The `diffusionCoeff` entry we have defined in the `laplaceDiffFEMViewKeys`
will then be asked as a required input. If not provided, the error thrown will ask for it described asked
an "input uniform diffusion coefficient for the Laplace equation".

.. code-block:: c++

  LaplaceDiffFEM::LaplaceDiffFEM( const string& name,
                                  Group * const parent ):
  LaplaceFEM( name, parent ), m_diffusion(0.0)
  {
    registerWrapper<string>(laplaceDiffFEMViewKeys.diffusionCoeff.Key()).
      setInputFlag(InputFlags::REQUIRED).
      setDescription("input uniform diffusion coeff for the laplace equation");
  }

Another important spot for binding the value of the XML read parameter to our `m_diffusion` is in `postInputInitialization()`.

.. code-block:: c++

  void LaplaceDiffFEM::postInputInitialization()
  {
    LaplaceFEM::postInputInitialization();

    string sDiffCoeff = this->getReference<string>(laplaceDiffFEMViewKeys.diffusionCoeff);
    this->m_diffusion = std::stof(sDiffCoeff);
  }

Now that we have required, read and bind the user-defined diffusion value to a variable, we can use it in the construction of our
matrix into the overridden `assembleSystem()`.

.. code-block:: c++
  :emphasize-lines: 16-18

  // begin element loop, skipping ghost elements
  for( localIndex k=0 ; k<elementSubRegion->size() ; ++k )
  {
    if(elemGhostRank[k] < 0)
    {
      element_rhs = 0.0;
      element_matrix = 0.0;
      for( localIndex q=0 ; q<n_q_points ; ++q)
      {
        for( localIndex a=0 ; a<numNodesPerElement ; ++a)
        {
          elemDofIndex[a] = dofIndex[ elemNodes( k, a ) ];

          for( localIndex b=0 ; b<numNodesPerElement ; ++b)
          {
            element_matrix(a,b) += detJ[k][q] *
                                   m_diffusion *
                                 + Dot( dNdX[k][q][a], dNdX[k][q][b] );
          }

        }
      }
      matrix.add( elemDofIndex, elemDofIndex, element_matrix );
      rhs.add( elemDofIndex, element_rhs );
    }
  }

This completes the implementation of our new solver *LaplaceDiffFEM*.

Nonetheless, the compiler should complain that `m_fieldName` is privately as inherited from *LaplaceFEM*. One should then either promote `m_fieldName` to protected
or add a getter in *LaplaceFEM* class to correct the error. The getter option has been chosen and the fix in our solver is then:

.. code-block:: c++

  array1d<globalIndex> const & dofIndex =
    nodeManager->getReference< array1d<globalIndex> >( dofManager.getKey( getFieldName() ) );


Note: For consistency do not forget to change LaplaceFEM to LaplaceDiffFEM in the guards comments

# Last steps
After assembling both declarations and implementations for our new solver, the final steps go as:

 - add declarations to parent CMakeLists.txt (here add to `physicsSolvers_headers` );
 - add implementations to parent CMakeLists.txt (here add to `physicsSolvers_sources`);
 - check that Doxygen comments are properly set in our solver class;
 - uncrustify it to match the code style by going to the build folder and running the command: make uncrustify_style;
 - write unit tests for each new features in the solver class;
 - write an integratedTests for the solver class.
