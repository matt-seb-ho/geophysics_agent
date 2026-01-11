**Context:** Buildguide > AppleMacOS > Install homebrew

## Install homebrew
Taken from the [homebrew website](https://brew.sh)
.. code-block```
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  (echo; echo 'eval "$(/opt/homebrew/bin/brew shellenv)"') >> ~/.zprofile
  
  note: this is the command for `zsh`. Other shells will require different commands. Homebrew should provide the correct command after install is complete.
  eval "$(/opt/homebrew/bin/brew shellenv)"
