from pathlib import Path

import structlog
from config.core_models import SimulationParams
from config.module_params import (
    MotorCortexModuleConfig,
    PlannerModuleConfig,
    TrajGeneratorType,
)


def generate_traj(
    params: PlannerModuleConfig,
    sim: SimulationParams,
    input_image_path: Path,
):
    log = structlog.get_logger("main.generate_signals")

    traj_gen_type = params.trajgen_type
    log.info(f"Generating trajectory using '{traj_gen_type}' planner...")

    if traj_gen_type == TrajGeneratorType.MOCKED:
        from complete_control.utils_common.generate_signals_minjerk import (
            generate_trajectory_minjerk,
        )

        return generate_trajectory_minjerk(sim)
    elif traj_gen_type == TrajGeneratorType.GLE:
        from complete_control.utils_common.generate_signals_gle import (
            generate_trajectory_gle,
        )

        return generate_trajectory_gle(
            input_image_path, params.gle_config.model_path, sim
        )
    else:
        raise NotImplementedError(f"Unknown planner type: {traj_gen_type}")


def generate_mock_motor_commands(
    sim: SimulationParams,
):
    from complete_control.utils_common.generate_signals_minjerk import (
        generate_motor_commands_minjerk,
    )

    log = structlog.get_logger("main.generate_signals")
    log.info(f"Generating motor commands...")

    return generate_motor_commands_minjerk(sim)
