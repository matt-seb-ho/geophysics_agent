**Context:** Datarepository > Wrapper > Default Values

## Default Values
`Wrapper` supports setting a default value for its wrapped object.
The default value is used if a wrapper with `InputFlags::OPTIONAL` attribute does not match an attribute in the input file.
For :ref:`LvArray` containers it is also used as a default value for new elements upon resizing the container.

Default value can be set via one of the following two methods:

* `setDefaultValue` sets the default value but does not affect the actual value stored in the wrapper.
* `setApplyDefaultValue` sets the default value *and* applies it to the stored value.



The type `DefaultValue<T>[ is used to store the default value for the wrapper.


   As such, it cannot currently be specialized for a user's custom type.
