**Context:** Finiteelement > Kernelinterface > kernelInterface > The KernelBase::kernelLaunch Interface

## The KernelBase::kernelLaunch Interface
The `kernelLaunch` function is a member of the kernel class itself.
As mentioned above, a physics implementation may use the existing `KernelBase`
interface, or define its own.
The `KernelBase::kernelLaunch` function defines a launching policy, and an
internal looping pattern over the quadrautre points, and calls the functions
defined by the `KernelBase` as shown here:


   :language: c++
   :start-after: //START_kernelLauncher
   :end-before: //END_kernelLauncher

Each of the `KernelBase` functions called in the `KernelBase::kernelLaunch`
function are intended to provide a certain amount of modularity and flexibility
for the physics implementations.
The general purpose of each function is described by the function name, but may
be further descibed by the function documentation found
`here ](../../../doxygen_output/html/classgeos_1_1finite_element_1_1_kernel_base.html).
