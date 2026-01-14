**Context:** Datarepository > Wrapper > Attributes

## Attributes
Each instance of `Wrapper` has a set of attributes that control its function in the data repository.
These attributes are:

* **InputFlags**

  A strongly typed enum that defines the relationship between the Wrapper and the XML input.
  Possible values are:

  +--------------+-----------------------------------------------------------------------------+
  | Value        | Explanation                                                                 |
  +==============+=============================================================================+
  | `FALSE`    | Data is not read from XML input (default).                                  |
  +--------------+-----------------------------------------------------------------------------+
  | `OPTIONAL` | Data is read from XML if an attribute matching Wrapper's name is found.     |
  +--------------+-----------------------------------------------------------------------------+
  | `REQUIRED` | Data is read from XML and an error is raised if the attribute is not found. |
  +--------------+-----------------------------------------------------------------------------+

  Other values of `InputFlags` enumeration are reserved for `Group` objects.



* **RestartFlags**

  Enumeration that describes how the Wrapper interacts with restart files.

  +--------------------+---------------------------------------------------------------+
  | Value              | Explanation                                                   |
  +====================+===============================================================+
  | `NO_WRITE`       | Data is not written into restart files.                       |
  +--------------------+---------------------------------------------------------------+
  | `WRITE`          | Data is written into restart files but not read upon restart. |
  +--------------------+---------------------------------------------------------------+
  | `WRITE_AND_READ` | Data is both written and read upon restart (default).         |
  +--------------------+---------------------------------------------------------------+


   Therefore, when registering custom types (i.e. not a basic C++ type or an :ref:`LvArray` container) we recommend setting the flag to `NO_WRITE`.
   A future documentation topic will explain how to extend buffer packing capabilities to custom user-defined types.

* **PlotLevel**

  Enumeration that describes how the Wrapper interacts with plot (visualization) files.

  +-------------+-------------------------------------------------------------------+
  | Value       | Explanation                                                       |
  +=============+===================================================================+
  | `LEVEL_0` | Data always written to plot files.                                |
  +-------------+-------------------------------------------------------------------+
  | `LEVEL_1` | Data written to plot when `plotLevel`>=1 is specified in input. |
  +-------------+-------------------------------------------------------------------+
  | `LEVEL_2` | Data written to plot when `plotLevel`>=2 is specified in input. |
  +-------------+-------------------------------------------------------------------+
  | `LEVEL_3` | Data written to plot when `plotLevel`>=3 is specified in input. |
  +-------------+-------------------------------------------------------------------+
  | `NOPLOT`  | Data never written to plot files.                                 |
  +-------------+-------------------------------------------------------------------+


