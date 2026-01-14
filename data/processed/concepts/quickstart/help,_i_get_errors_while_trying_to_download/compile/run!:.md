**Context:** QuickStart > Help, I get errors while trying to download/compile/run!:

## Help, I get errors while trying to download/compile/run!:
Unfortunately, no set of instructions is foolproof.
It is simply impossible to anticipate every system configuration or user.
If you run into problems during the installation, we recommend the following five-step process:

#. Take a moment to relax, and then re-read the instructions carefully.
   Perhaps you overlooked a key step?  Re-read the error message(s) closely.
   Modern compilation tools are often quite helpful in reporting exactly why things fail.

#. Type a few keywords from your error into a search engine.
   It is possible someone else out there has encountered your problem before, and a well-chosen keyword can often produce an instant solution.
   Note that when a compilation fails, you may get pages and pages of errors.  Try to identify the *first* one to occur and fix that.
   One error will often trigger subsequent errors, and looking at the *last* error on the screen may not be so helpful.

#. If you encounter problems building one of the third-party libraries we depend on, check out their support pages.
   They may be able to help you more directly than we can.

#. Still stuck? Check out our [issues tracker ](https://github.com/GEOS-DEV/GEOS/issues), searching current or closed issues that may address your problem.
   Perhaps someone has had an identical issue, or something close.  The issue tracker has a convenient search bar where you can search for relevant keywords.
   Remember to remove the default [is:open` keyword to search both open and closed issues.

#. If you have exhausted the options above, it is time to seek help from the developers.
   Post an issue on our issue tracker.
   Be specific, providing as much information as possible about your system setup and the error you are encountering.
   Please be patient in this process, as we may need to correspond a few times and ask you to run additional tests.
   Most of the time, users have a slightly unusual system configuration that we haven't encountered yet, such as an older version of a particular library.
   Other times there is a legitimate bug in GEOS to be addressed.
   Take pride in the fact that you may be saving the next user from wasted time and frustration.

# Repository Organization
The source for GEOS and related tools are hosted on `Github ](https://github.com).
We use [Git workflows ](https://git-scm.com) to version control our code and manage the entire development process.
On Github, we have a [GEOS Organization ](https://github.com/GEOS-DEV) that hosts several related repositories.

You should sign up for a free Github account, particularly if you are interested in posting issues to our issue tracker and communicating with the developers.
The main repository of interest is obviously GEOS itself: [GEOS ](https://github.com/GEOS-DEV/GEOS)

We also rely on two types of dependencies: first-party and third-party.
First-party dependencies are projects directly associated with the GEOS effort, but kept in separate repositories because they form stand-alone tools.
For example, there is an equation-of-state package called [PVTPackage ](https://github.com/GEOS-DEV/PVTPackage) or the streamlined CMake-based foundation [BLT ](https://github.com/LLNL/blt) .
These packages are handled as [Git Submodules ](https://git-scm.com/book/en/v2/Git-Tools-Submodules), which provides a transparent way of coordinating multiple code development projects.
Most users will never have to worry that these modules are in fact separate projects from GEOS.

We also rely on several open-source Third-Party Libraries (TPLs) (see [thirdPartyLibs ](https://github.com/GEOS-DEV/thirdPartyLibs)).
These are well-respected projects developed externally to GEOS.
We have found, however, that many compilation issues stem from version incompatibilities between different packages.
To address this, we provide a mirror of these TPLs, with version combinations we know play nicely together.
We also provide a build script that conveniently and consistently builds those dependencies.

Our build system will automatically use the mirror package versions by default.
You are welcome to tune your configuration, however, to point to different versions installed on your system.
If you work on an HPC platform, for example, common packages may already be available and optimized for platform hardware.
For new users, however, it may be safer to begin with the TPL mirror.


   Inquire with your institution's point-of-contact whether this option already exists.
   For all LLNL systems, the answer is yes.

Finally, there are also several private repositories only accessible to the core development team, which we use for behind-the-scene testing and maintenance of the code.

# Username and Authentication
New users should sign up for a free [Github account ](https://github.com).

If you intend to develop in the GEOS codebase, you may benefit from setting up your git credentials (see :ref:[GitWorkflow`).


# Download
It is possible to directly download the source code as a zip file.
We strongly suggest, however, that users don't rely on this option.
Instead, most users should use Git to either *clone* or *fork* the repository.
This makes it much easier to stay up to date with the latest releases and bug fixes.
If you are not familiar with the basics of Git, `here is a helpful resource ](https://git-scm.com) to get you started.

The tutorial here assumes you will use a https clone with no specific credentials.
Using an ssh connection pattern requires a very slight modification.
See the **Additional Notes** at the end of this section for details.

If you do not already have Git installed on your system, you will need to install it.
We recommend using a relatively recent version of Git, as there have been some notable improvements over the past few years.
You can check if Git is already available by opening a terminal and typing

[``sh
  git --version

You'll also need the `git-lfs ](https://git-lfs.github.com/) large file extension.

The first task is to clone the `GEOS` and `thirdPartyLibs` repositories.
If you do not tell it otherwise, the build system will expect the GEOS and thirdPartyLibs to be parallel to each other in the directory structure.
For example,

``sh
  codes/
  ├── GEOS/
  └── thirdPartyLibs/

where the toplevel `codes` directory can be re-named and located wherever you like.
It is possible to customize the build system to expect a different structure, but for now let us assume you take the simplest approach.

First, using a terminal, create the `codes` directory wherever you like.

``sh
  cd /insert/your/desired/path/
  mkdir codes
  cd codes

Inside this directory, we can clone the GEOS repository.
We will also use some Git commands to initialize and download the submodules (e.g. `LvArray`).

``sh
   git clone https://github.com/GEOS-DEV/GEOS.git
   cd GEOS
   git lfs install
   git submodule init
   git submodule update
   cd ..

If all goes well, you should have a complete copy of the GEOS source at this point.
The most common errors people encounter here have to do with Github not recognizing their authentication settings and/or repository permissions.
See the previous section for tips on ensuring your SSH is working properly.

*Note*: Previous versions of GEOS also imported the integratedTests submodule, which is not publicly available (access is limited to the core development team).
This may cause the `git submodule update` command to fail.
In that case, run `git submodule deinit integratedTests` before `git submodule update`.
This submodule is not required for building GEOS.

``sh
   cd GEOS
   git submodule update --init src/cmake/blt
   git submodule update --init src/coreComponents/LvArray
   git submodule update --init src/coreComponents/fileIO/coupling/hdf5_interface
   git submodule update --init src/coreComponents/constitutive/PVTPackage
   cd ..

Once we have grabbed GEOS, we do the same for the thirdPartyLibs repository.  From the `codes` directory, type

``sh
   git clone https://github.com/GEOS-DEV/thirdPartyLibs.git
   cd thirdPartyLibs
   git lfs install
   git pull
   git submodule init
   git submodule update
   cd ..

Again, if all goes well you should now have a copy of all necessary TPL packages.

**Additional Notes:**

#. `git-lfs` may not function properly (or may be very slow) if your version of git and git-lfs are not current.
If you are using an older version, you may need to add `git lfs pull` after `git pull` in the above procedures.

#. You can adapt the commands if you use an ssh connection instead.
The clone `https://github.com/GEOS-DEV/GEOS.git` becomes `git clone git@github.com:GEOS-DEV/GEOS.git`.
You may also be willing to insert your credentials in the command line (less secure) `git clone https://${USER}:${TOKEN}@github.com/GEOS-DEV/GEOS.git``.

# Configuration 
Before proceeding, make sure to have installed all the minimal prerequisites as described in :ref:`Prerequisites`
Note that GEOS supports a variety of parallel computing models, depending on the hardware and software environment.
Advanced users are referred to the :ref:`BuildGuide` for a discussion of the available configuration options.

Before beginning, it is a good idea to have a clear idea of the flavor and version of the build tools you are using.
If something goes wrong, the first thing the support team will ask you for is this information.

``sh
  cpp --version
  mpic++ --version
  cmake --version

Here, you may need to replace `cpp` with the full path to the C++ compiler you would like to use, depending on how your path and any aliases are configured.
