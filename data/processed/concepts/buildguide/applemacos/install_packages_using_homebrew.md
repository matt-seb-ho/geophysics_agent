**Context:** Buildguide > AppleMacOS > Install packages using homebrew

## Install packages using homebrew
.. code-block``
  brew install bison cmake gfortran git-lfs open-mpi lapack python3 ninja m4
  echo 'export PATH="/opt/homebrew/opt/bison/bin:$PATH"' >> ~/.zshrc
  echo 'export PATH="/opt/homebrew/opt/m4/bin:$PATH"' >> ~/.zshrc
  git lfs install
