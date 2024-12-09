This branch of the repository features all code needed to run simulations of reaching tasks on a virtual robotic arm driven by a closed-loop cerebellar controller.

The file `complete_control/complete.music` defines the two Python scripts containing the two simulations to be synchronized by MUSIC. In this branch, the NEST simulation is run by `complete_control/brain.py` and the PyBullet simulation by `receiver_plant.py`. The file `./complete_control/complete.music` can be modified to allocate the desired number of slots to both the controller script and the plant one. The simulation can be started by running:
`mpirun -np 2 music complete.music` inside `./complete_control`. The value of the -np parameter should be adjusted according to the number of processes allocated in the `complete.music` file.

Models of the neurons making up planner, feedforward motor cortex and brainstem are defined in `nestml/controller_module.nestml` and are generated through NESTML. The module can be compiled by running:
`python3 nestml/generate_controller_module.py`. This creates a `target` subfolder inside `nestml`, whose directory should be added to `LD_LIBRARY_PATH` for NEST to be able to find the module.

The Python script `settings.py` can be modified to set simulation and experiment parameters, such as initial and target position, simulation duration and resolution, and the configuration file for the reconstruction of cerebellar models. If initial and target positions are modified in the `settings.py` file, then new analog signals for trajectory and motor commands must be generated by running `python3 complete_control/generate_analog_signals.py`.

The scripts `planner.py`, `motor_cortex.py`, `stateestimator.py` and `sensoryneuron.py` define the classes implementing respectively the Planner block, the Motor Cortex block, the State Estimator block and the sensory system. 

The file `cerebellum_build.py` reconstructs cerebellar networks from the chosen HDF5 file according to the relative `.yaml` configuration file and instantiates NEST populations for them.

Other Python scripts contain helper functions for data processing and visualization.



