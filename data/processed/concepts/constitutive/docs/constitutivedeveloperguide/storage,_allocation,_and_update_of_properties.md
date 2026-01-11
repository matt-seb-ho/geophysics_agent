**Context:** Constitutive > constitutiveDeveloperGuide > Storage, allocation, and update of properties

## Storage, allocation, and update of properties
Each constitutive model owns, as member variables, `LvArray::Array` containers
that hold the properties (or fields) and their derivatives with respect to the
other fields needed to update each property. Each property is stored as an array with the
first dimension representing the elementIndex and the second dimension storing the index of the
integration point. These dimensions are determined by the number of elements of the
subregion on which each constitutive model is registered, and by the chosen discretization
method. Vector and tensor fields have an additional dimension to identify
their components. Similarly, an additional dimension is
necessary for multiphase fluid models with properties defined for each component in each phase.
For example, a single-phase fluid model where density and viscosity are
functions of the fluid pressure has the following members:


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_00
   :end-before: //END_SPHINX_INCLUDE_00

Resizing all fields of the constitutive models happens during the initialization phase by
the `ConstitutiveManger` through a call to `ConstitutiveManger::hangConstitutiveRelation`,
which sets the appropriate subRegion as the parent Group of each constitutive model object.
This function also resizes all fields based on the size of the subregion and the number of quadrature
points on it, by calling `CONSTITUTIVE_MODEL::allocateConstitutiveData`. For the
single phase fluid example used before, this call is:


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_00
   :end-before: //END_SPHINX_INCLUDE_00

Any property or field stored on a constitutive model must be updated within a computational
kernel to ensure that `host` and `device` memory in GPUs are properly synced, and that any
updates are performed on `device`. Some properties are updated
within finite element kernels of specific physics (such as stress in a mechanics kernel). Consequently,
for each constitutive model class, a corresponding `nameOfTheModelUpdates`, which only contains
`LvArray::arrayView` containers to the data, can be captured by value inside computational kernels.
For example, for the single phase fluid model `Updates` are:


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_01
   :end-before: //END_SPHINX_INCLUDE_01

Because `Updates` classes are responsible for updating the fields owned by the constitutive models,
they also implement all functions needed to perform property updates, such as:


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_02
   :end-before: //END_SPHINX_INCLUDE_02

# Compound models
Compound constitutive models are employed to mimic the behavior of a material that
requires a combination of constitutive models linked together. These compound models
do not hold any data. They serve only as an interface with the individual models that
they couple.
