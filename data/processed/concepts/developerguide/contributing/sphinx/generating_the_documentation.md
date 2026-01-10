**Context:** Developerguide > Contributing > Sphinx > Generating the documentation

# Generating the documentation
- To generate the documentation files, you will need to install Sphinx using:

  [`sh
    pip -m install sphinx
    pip -m install sphinx-design sphinx-argparse sphinxcontrib-plantuml sphinxcontrib.programoutput sphinx_rtd_theme
    pip -m install scipy

- Then you can generate the documentation files with the following commands:

  ``sh
    cd /path/to/GEOS/build-your-platform-release
    make geosx_docs

- That will create a new folder

  ``sh
    /path/to/GEOS/build-your-platform-release/html/docs/sphinx

which contains all the html files generated.
