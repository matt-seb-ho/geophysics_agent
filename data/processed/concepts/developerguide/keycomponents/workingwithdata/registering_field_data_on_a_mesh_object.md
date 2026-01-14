**Context:** Developerguide > Keycomponents > WorkingWithData > Registering Field data on a Mesh Object

## Registering Field data on a Mesh Object
To register `Field` data, there are many ways a developer may proceed.
We will use the example of registering a `totalDisplacement` on the `NodeManager`
from the `SolidMechanics` solver.
The most general approach is to define a string key and call one of the
`Group::registerWrapper() ](../../../doxygen_output/html/classgeos_1_1data_repository_1_1_group.html#a741c3b5728fc47b33fbaad6c4f124991)
functions from `PhysicsSolverBase::registerDataOnMesh()`.
Then when you want to use the data, you can call `Group::getReference()`.
For example this would look something like:

.. code-block:: c++

    void SolidMechanicsLagrangianFEM::registerDataOnMesh( Group * const MeshBodies )
    {
      for( auto & mesh : MeshBodies->GetSubGroups() )
      {
        NodeManager & nodes = mesh.second->groupCast< MeshBody * >()->getMeshLevel( 0 ).getNodeManager();

        nodes.registerWrapper< array2d< real64, nodes::TOTAL_DISPLACEMENT_PERM > >( keys::totalDisplacement ).
          setPlotLevel( PlotLevel::LEVEL_0 ).
          setRegisteringObjects( this->getName()).
          setDescription( "An array that holds the total displacements on the nodes." ).
          reference().resizeDimension< 1 >( 3 );
      }
    }

and

.. code-block:: c++

    arrayView2d< real64, nodes::TOTAL_DISPLACEMENT_USD > const & u = nodes.getReference< array2d< real64, nodes::TOTAL_DISPLACEMENT_PERM > >( keys::totalDisplacement );
    ... do something with u

This approach is flexible and extendible, but is potentially error prone due to
its verbosity and lack of information centralization.
Therefore we also provide a more controlled/uniform method by which to register
and extract commonly used data on the mesh.
The `trait approach` requires the definition of a `traits struct` for each
data object that will be supported.
To apply the `trait approach` to the example use case shown above, there
should be the following definition somewhere in a header file:

.. code-block:: c++

    namespace fields
    {
    struct totalDisplacement
    {
      static constexpr auto key = "totalDisplacement";
      using DataType = real64;
      using Type = array2d< DataType, nodes::TOTAL_DISPLACEMENT_PERM >;
      static constexpr DataType defaultValue = 0;
      static constexpr auto plotLevel = dataRepository::PlotLevel::LEVEL_0;

      /// Description of the data associated with this trait.
      static constexpr auto description = "An array that holds the total displacements on the nodes.";
    };
    }

Also note that you should use the `DECLARE_FIELD` C++ macro that will perform this tedious task for you.
Then the registration is simplified as follows:

.. code-block:: c++

    void SolidMechanicsLagrangianFEM::registerDataOnMesh( Group * const MeshBodies )
    {
      for( auto & mesh : MeshBodies->GetSubGroups() )
      {
        NodeManager & nodes = mesh.second->groupCast< MeshBody * >()->getMeshLevel( 0 ).getNodeManager();
        nodes.registerField< fields::totalDisplacement >( this->getName() ).resizeDimension< 1 >( 3 );
      }
    }

And to extract the data, the call would be:

.. code-block:: c++

    arrayView2d< real64, nodes::TOTAL_DISPLACEMENT_USD > const & u = nodes.getField< fields::totalDisplacement >();
    ... do something with u

The end result of the `trait approach` to this example is that the developer
has defined a standard specification for `totalDisplacement`, which may be
used uniformly across the code.
