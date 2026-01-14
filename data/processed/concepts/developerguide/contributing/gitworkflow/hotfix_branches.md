**Context:** Developerguide > Contributing > GitWorkflow > Hotfix Branches

## Hotfix Branches
A `hotfix` branch fixes a bug in the `release` branch.
It uses the same naming convention as a `bugfix` branch.
The main difference with a `bugfix` branch is that the primary target branch is the
`release` branch instead of `develop`.
As a soft policy, merging a `hotfix` into a `release` branch should result in
a patch increment for the release sequence of tags.
So if a `hotfix` was merged into `release` with a most recent tag of
`1.2.1`, the merged commit would be tagged with `1.2.2`.
Finally, at some point prior to the next major/minor release, the `release`
branch should be merged back into `develop` to incorporate any hotfix changes
into `develop`.


An example lifecycle diagram for hotfix branchs:

``console
        v1.2.0       v1.2.1       v1.2.2         v1.3.0 (tag)
        B------------H1-----------H2             I      (release)
        ^\          /| \         / \             ^
        | \        /  \ \       /   \            |
        |  BA-----BB   \ H1A--H1B    \           |      (hotfix/xyz)
        |               \             \          |
   A----B-----C-----D----E------F------G----H----I---   (develop)


