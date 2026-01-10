**Context:** Physicssolvers > SolutionStrategy > Line Search

## Line Search
A line search method can be applied along with the Newton's method to facilitate Nonlinear
convergence. After the Newton update, if the residual norm has increased instead
of decreased, a line search algorithm is employed to correct the Newton update.


The user can choose between two different behaviors in case the line search fails
to provide a reduced residual norm:

1. accept the solution and move to the next Newton iteration;

2. reject the solution and request a timestep cut;

# Timestepping Strategy
The actual timestep size employed is determined by a combination of several factors.
In particular, specific output events may have timestep requirements that force a
specific timestep to be used. However, physics solvers do have the possibility of
requesting a specific timestep size to the event manager based on their specific
requirements. In particular, in case of fast convergence indicated by a small number of
Newton iterations, i.e.



the physics solver will require to double the timestep size. On the other hand,
if a large number of nonlinear iterations are necessary to
find the solution at timestep :math:`n`



the physics solver will request the next timestep, :math:`n+1`, to be half the size of timestep :math:`n`.
Here,

Additionally, in case the nonlinear solver fails to converge with the timestep provided by the
event manager, the timestep size is cut, i.e.



and the nonlinear loop is repeated with the new timestep size.


# Parameters
All parameters defining the behavior of the nonlinear solver and determining the
timestep size requested by the physics solver are defined in the NonlinearSolverParameters
and are presented in the following table.


