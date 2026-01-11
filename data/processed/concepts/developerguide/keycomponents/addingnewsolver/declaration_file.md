**Context:** Developerguide > Keycomponents > AddingNewSolver > Declaration File

## Declaration File
As there is only few places where we have to change, the whole declaration file is reported below and
commented afterwards.

.. code-block:: c++

  #include "physicsSolvers/simplePDE/LaplaceFEM.hpp"

  namespace geos
  {

  class LaplaceDiffFEM : public LaplaceFEM
  {
  public:

    LaplaceDiffFEM() = delete;

    LaplaceDiffFEM( const string& name,
                    Group * const parent );

    virtual ~LaplaceDiffFEM() override;

    static string catalogName() { return "LaplaceDiffFEM"; }

    virtual void
    assembleSystem( real64 const time,
                    real64 const dt,
                    DomainPartition * const domain,
                    DofManager const & dofManager,
                    ParallelMatrix & matrix,
                    ParallelVector & rhs ) override;


    struct viewKeyStruct : public LaplaceFEM::viewKeyStruct
    {
      dataRepository::ViewKey diffusionCoeff = { "diffusionCoeff" };
    } laplaceDiffFEMViewKeys;

    protected:
    virtual void postInputInitialization() override final;

  private:
    real64 m_diffusion;

  };


We intend to have a user-defined diffusion coefficient, we then need a `real64` class variable `m_diffusion`
to store it.

Consistently with *LaplaceFEM*, we will also delete the nullary constructor and declare a constructor with the same arguments for
forwarding to `Group` master class. Another mandatory step is to override the static `CatalogName()` method to properly
register any data from the new solver class.

Then as mentioned in :ref:`Implementation`, the diffusion coefficient is used when assembling the matrix coefficient. Hence
we will have to override the `assembleSystem()` function as detailed below.

Moreover, if we want to introduce a new binding between the input XML and the code we will have to work on the three
`struct viewKeyStruct` , `postInputInitialization()` and the constructor.

Our new solver `viewKeyStruct` will have its own structure inheriting from the *LaplaceFEM* one to have the `timeIntegrationOption`
and `fieldName` field. It will also create a `diffusionCoeff` field to be bound to the user defined homogeneous coefficient on one hand
and to our `m_diffusion` class variable on the other.

