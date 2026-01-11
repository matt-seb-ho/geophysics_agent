**Context:** Developerguide > Contributing > WorkInteractivelyOnCI > Step 1: Adding a GHA to establish a connection

# Step 1: Adding a GHA to establish a connection
First, as much as you can, try to reduce the number of jobs you're triggering by commenting out the configurations you do not require for your debugging.
Then in your branch, add the following GHA step to the `.github/build_and_test.yml` (see full documentation of the action `here <https://github.com/lhotari/action-upterm>_`).

```console
  - name: ssh  
      uses: lhotari/action-upterm@v1  
      with:
        ## limits ssh access and adds the ssh public key for the user which triggered the workflow
        limit-access-to-actor: true
        ## limits ssh access and adds the ssh public keys of the listed GitHub users
        limit-access-to-users: GitHubLogin

The action should be added after whichever step triggers an error. In case of a build failure it is best to add the action after the `build, test and deploy` step.
It is also important to prevent the job to exit upon failure. For instance, it is suggested to comment the following lines in the `build, test and deploy` step.

``console
    set -e

``console
    exit ${EXIT_STATUS}


You can now commit the changes and push them to your remote branch.
