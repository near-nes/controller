* mini test to see if nest works
* experiment WITHOUT nrp
* start trying to port experiment? 


* Isolate the nest-simulator initialization:
    - Kernel setup
    - Network setup
    - Define the recorders and connectors for the NRP (what will be  and populated by the NRP)

    We should create a script that can be sent to nest-server as a payload for /exec endpoint. It would be good to import as few Python modules as possible, as each of them should be enabled in nest-server. For example, we can isolate mpi here.

* Isolate nest-simulator simulation step
    - if anything should be done with the data to/from nest, we will put it to tranceiver functions

* Isolate PyBullet initialization:
    - World setup
    - DataPAcks definition

* Isolate PyBullet simulation step
    - Define the data unpacking and converting it to pyBullet actions
