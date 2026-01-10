**Context:** Developerguide > Keycomponents > XML > Implement the data registration process (`registerWrapper`):

## Implement the data registration process (`registerWrapper`):
The registration process done in the class constructor puts everything together.
It connects the attributes values in the XML file to class member data.
For instance, in the listing below, the first `registerWrapper` call means that we want to read in the XML file the attribute value corresponding to the attribute tag ''phaseMinVolumeFraction'' defined in the .hpp file, and that we want to store the read values into the `m_phaseMinVolumeFraction` data members.
We see that this input is not required.
If it is absent from the XML file, the default value is used instead.
The short description that completes the registration will be added to the auto-generated documentation.


   :language: c++
   :start-after: //START_SPHINX_INCLUDE_00
   :end-before: }

*[source: src/coreComponents/constitutive/relativePermeability/BrooksCoreyRelativePermeability.cpp]*
