**Context:** Developerguide > Contributing > WorkInteractivelyOnCI > Step 4: Run the docker container interactively

# Step 4: Run the docker container interactively
Once you are connected to the machine it is convenient to follow these steps to interactively run the docker container:

``console
    docker ps -a


The id of the existing docker container will be displayed and you can use it to commit the container.

``console
    docker commit <id> debug_image

and then run it interactively, e.g.

```console
    docker run -it --volume=/home/runner/work/GEOS/GEOS:/tmp/geos -e ENABLE_HYPRE=ON -e ENABLE_HYPRE_DEVICE=CUDA -e ENABLE_TRILINOS=OFF --cap-add=SYS_PTRACE --entrypoint /bin/bash debug_image
