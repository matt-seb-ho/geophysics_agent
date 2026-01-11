**Context:** Buildguide > SpackUberenv > Adding a Dependency (Advanced)

## Adding a Dependency (Advanced)
Adding a dependency to GEOS is straight forward **if** the dependency already builds with Spack. If that is the case, then all you need to do is add a `depends_on('cool-new-library')` to the GEOS `package.py` file. If however the dependency doesn't have a Spack package, you will have to add one by creating a `cool-new-library/package.py` file in the `scripts/spack_packages/packages`` directory and adding the logic to build it there. For instructions on how to create a package recipe from scratch, Spack has provided a `Spack Packing Guide ](https://spack.readthedocs.io/en/latest/packaging_guide.html).

Oftentimes (unfortunately), even when a package already exists in Spack, it might not work out of the box for your system. In this case copy over the existing `package.py` file from the Spack repository into `scripts/spack_packages/packages/cool-new-library/package.py`, as if you were adding a new package, and perform your modifications there. Once you have the package working, copy the package back into the Spack repository and commit+push your changes to Spack.
