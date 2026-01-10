**Context:** Fileio > Doc > LogCsvOutputs > InternalWellGenerator and VTKWellGenerator

## InternalWellGenerator and VTKWellGenerator
### Information on well components
This component generates a table describing the internal structure of a well. Each table corresponds to a well and is titled with the well name. The table contains one line for each element making up the well, with the following information:

- **Element no.:**

  The index of the element in the well, starting from 0.

- **CoordX:**

  The X coordinate of the element center.

- **CoordY:**

  The Y coordinate of the element center.

- **CoordZ:**

  The Z coordinate of the element center.

- **Prev Element:**

  The identifier of the previous element. If this element does not exist, the field is empty.

- **Next Element:**

  The identifier of the next element. If it does not exist, the field is empty.

The output can be saved in the log file if this option is specified (as mentioned [here ](#how-to-generate-these-outputs)_) when the program is run.

