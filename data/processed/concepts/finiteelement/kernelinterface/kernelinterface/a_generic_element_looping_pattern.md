**Context:** Finiteelement > Kernelinterface > kernelInterface > A Generic Element Looping Pattern

## A Generic Element Looping Pattern
One example of a looping pattern is the
`regionBasedKernelApplication ](../../../doxygen_output/html/_kernel_base_8hpp.html#file_a22560f1fcca889307fdabb5fa7422c0d)
function.

The contents of the looping function are displayed here:


   :language: c++
   :start-after: //START_regionBasedKernelApplication
   :end-before: //END_regionBasedKernelApplication

This pattern may be used with any kernel class that either:

#. Conforms to the [KernelBase` interface by defining each of the kernel
   functions in `KernelBase`.

#. Defines its own `kernelLaunch` function that conforms the the signature
   of `KernelBase::kernelLaunch`.
   This option essentially allows for a custom kernel that does not conform to
   the interface defined by `KernelBase` and `KernelBase::kernelLaunch`.
