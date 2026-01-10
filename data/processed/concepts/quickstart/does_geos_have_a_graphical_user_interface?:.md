**Context:** QuickStart > Does GEOS have a graphical user interface?:

## Does GEOS have a graphical user interface?:
Given the focus on rapid development and HPC environments, GEOS does not have a graphical user interface.
This is consistent with many other high performance computing packages, but we recognize it can be a deal-breaker for certain users.
For those who can get past this failing, we promise we still have a lot to offer.
In a typical workflow, you will prepare an XML-based input file describing your problem.
You may also prepare a mesh file containing geometric and property information describing, say, a reservoir you would like to simulate.
There is no shortage of GUI tools that can help you in this model building stage.
The resulting input deck is then consumed by GEOS to run the simulation and produce results.
This may be done in a terminal of your local machine or by submitting a job to a remote server.
The resulting output files can then be visualized by any number of graphical visualization programs (typically [VisIt ](https://wci.llnl.gov/simulation/computer-codes/visit/) or [paraview ](https://www.paraview.org/)).
Thus, while GEOS is GUI free, the typical workflow is not.
