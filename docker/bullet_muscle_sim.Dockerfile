FROM nrp-local/nrp-t3.4:local

ENV DEPS_DIR=$HOME/sim/dependencies
ENV BULLET_MUSCLE_DIR=$DEPS_DIR/bullet_muscle_sim
ENV SDF_MODELS_DIR=/sim/embodiment_sdf_models
# RUN mkdir -p $BULLET_MUSCLE_DIR $SDF_MODELS_DIR

# Install bullet muscle simulation
# RUN git clone https://github.com/near-nes/bullet_muscle_sim.git $BULLET_MUSCLE_DIR
# RUN git clone https://github.com/near-nes/embodiment_sdf_models.git $SDF_MODELS_DIR
# For the experiment, we need to use the cloned version and not remove it
# RUN sudo rm -rf /sim/dependencies/bullet_muscle_sim/arm_1dof

# ENV PYTHONPATH=${PYTHONPATH}:${BULLET_MUSCLE_DIR}
