**Context:** Developerguide > Contributing > WorkInteractivelyOnCI > Step 2: Inspect the CI and grab server address

# Step 2: Inspect the CI and grab server address
``console
    Run lhotari/action-upterm@v1
    upterm
    
    Auto-generating ~/.ssh/known_hosts by attempting connection to uptermd.upterm.dev
    Pseudo-terminal will not be allocated because stdin is not a terminal.
    
    Warning: Permanently added 'uptermd.upterm.dev' (ED25519) to the list of known hosts.
    
    runner@uptermd.upterm.dev: Permission denied (publickey).
    
    Adding actor "GitHubLogin" to allowed users.
    Fetching SSH keys registered with GitHub profiles: GitHubLogin
    Fetched 2 ssh public keys
    Creating a new session. Connecting to upterm server ssh://uptermd.upterm.dev:22
    Created new session successfully
    Entering main loop 
    === Q16OBOFBLODJVA3TRXPL                                                                                                 
    Command:                tmux new -s upterm -x 132 -y 43                                                                 
    Force Command:          tmux attach -t upterm                                                                           
    
    Host:                   ssh://uptermd.upterm.dev:22                                                                     
    SSH Session:            ssh Q16oBofblOdjVa3TrXPl:ZTc4NGUxMWRiMjI5MDgudm0udXB0ZXJtLmludGVybmFsOjIyMjI=@uptermd.upterm.dev

