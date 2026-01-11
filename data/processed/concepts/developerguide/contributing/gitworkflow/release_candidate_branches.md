**Context:** Developerguide > Contributing > GitWorkflow > Release Candidate Branches

## Release Candidate Branches
When `develop` has progressed to a point where we would like to create a new
`release`, we will create a release candidate branch with the name consisting
of `release_major.minor.x` number, where the `x` represents the sequence of patch tags that
will be applied to the branch.
For instance if we were releasing version `1.2.0`, we would name the branch
`release_1.2.x`.
Once the release candidate is ready, it is merged back into `develop`.
Then the `develop` branch is merged into the `release` branch and tagged.
From that point the `release` branch exists to provide a basis for maintaining
a stable release version of the code.
Note that the absence of `hotfix` branches, the history for `release` and
`develop` would be identical.

An example lifecycle diagram for a release candidate branch:

``console
                                     v1.2.0          (tag)
                                     G               (release)
                                     ^
                                     |
   A----B-----C----D-----E-----F-----G------------   (develop)
         \          \         /
          \          \       /
          BA----BB----BC----BD                       (release_1.2.x)

