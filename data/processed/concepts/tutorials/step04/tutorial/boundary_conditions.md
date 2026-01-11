**Context:** Tutorials > Step04 > Tutorial > Boundary conditions

## Boundary conditions
As aforementioned, the beam is fixed on one end, and subjects to surface traction on
the other end. These boundary conditions are set up through the `FieldSpecifications` block.
Here, `nodeManager` and
`faceManager`
in the `objectPath` indicate that the boundary conditions are applied to the element nodes and faces, respectively.
Component `0`, `1`, and `2` refer to the x, y, and z direction, respectively. And the non-zero values given by
`Scale` indicate the magnitude of the loading. Some shorthands, such as
`xneg` and `xpos`, are used as the locations where the boundary conditions are applied in the computational domain.
For instance, `xneg` means the portion of the computational domain located at the left-most in the x-axis, while
`xpos` refers to the portion located at the right-most area in the x-axis. Similar shorthands include `ypos`, `yneg`,
`zpos`, and `zneg`. Particularly, the time-dependent loading applied at the beam tip is defined through a function with
the name `timeFunction`.


  :language: xml
  :start-after: <!-- SPHINX_BoundaryConditions -->
  :end-before:  <!-- SPHINX_BoundaryConditionsEnd -->

------------------------------------