**Context:** Developerguide > Contributing > GitWorkflow > Feature Branches

## Feature Branches
New developments (new features or modifications to features) are branched off
of [develop` into a `feature` branch.
The naming of feature branches should follow `feature/[developer]/[branch-description]`
if you expect that only a single developer will contribute to the branch,
or `feature/[branch-description]` if you expect it will be a collaborative effort.
For example, if a developer named `neo` were to add or modify a code feature
expecting that they would be the only contributor, they would create a branch
using the following commands to create the local branch and push it to the remote
repository:

``console
  git checkout -b feature/neo/freeYourMind
  git push -u origin feature/neo/freeYourMind

However if the branch is a collaborative branch amongst many developers, the
appropriate commands would be:

``console
  git checkout -b feature/freeYourMind
  git push -u origin feature/freeYourMind

When `feature` branches are ready to be merged into `develop`, a `Pull Request`
should be created to perform the review and merging process.

An example lifecycle diagram for a feature branch:

```console
   create new feature branch:
   git checkout -b feature/neo/freeYourMind

   A-------B-------C (develop)
            \
             \
             BA      (feature/neo/freeYourMind)

   Add commits to 'feature/neo/freeYourMind' and merge back into develop:

   A-------B--------C-------D--------E (develop)
            \              /
             \            /
             BA----BB----BC            (feature/neo/freeYourMind)

See below for details about :ref:`Submitting_a_Pull_Request`.
