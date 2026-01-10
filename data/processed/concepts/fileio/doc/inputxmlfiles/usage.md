**Context:** Fileio > Doc > InputXMLFiles > Usage

## Usage
An input file that uses advanced xml features requires preprocessing before it can be used with GEOS.
The preprocessor writes a compiled xml file to the disk, which can be read directly by GEOS and serves as a permanent record for the simulation.
There are three ways to apply the preprocessor:

1) Automatic Preprocessing:  Substituting `geosx` for `geosx_preprocessed` when calling the code will automatically apply the preprocessor to the input xml file, and then pass the remaining arguments to GEOS.  With this method, the compiled xml files will have the suffix '.preprocessed'.  Before running the code, the compiled xml file will also be validated against the xml schema.

```bash
    # Serial example
    geosx_preprocessed -i input.xml

    # Parallel example
    srun -n 2 geosx_preprocessed -i input.xml -x 2


2) Manual Preprocessing:  For this approach, xml files are preprocessed manually by the user with the `preprocess_xml` script.  These files can then be submitted to GEOS separately:

```bash
    # The -c argument is used to manually specify the compiled name
    preprocess_xml -i input.xml -c input.xml.processed
    geosx -i input.xml.processed

    # Otherwise, a random name will be chosen by the tool
    compiled_input=$(preprocess_xml input.xml)
    geosx -i $compiled_input


3) Python / pygeosx: The preprocessor can also be applied directly in python or in pygeosx simulations.  An example of this is method is provided here: `GEOS/examples/pygeosxExamples/hydraulicFractureWithMonitor/`.


Each of these options support specifying multiple input files via the command line (e.g. `geosx_preprocessed -i input_a.xml -i input_b.xml`).
They also support any number of command-line parameter overrides (e.g. `geosx_preprocessed -i input_a.xml -p parameter_a alpha -p parameter_b beta`).

