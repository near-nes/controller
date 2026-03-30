from complete_control.neural.neural_models import PopulationSpikes
from complete_control.config import paths
from complete_control.neural.nest_adapter import nest, initialize_nest
import numpy as np
import matplotlib.pyplot as plt
import datetime
from pathlib import Path

np.random.seed(12345)

initialize_nest("MUSIC")


def create_neurons(N, N_trials, t_trial):
    ################## create neurons#########################
    # sensoryneuron
    sn_p = nest.Create("parrot_neuron", N)
    sn_n = nest.Create("parrot_neuron", N)

    # dcn neurons
    dcn_p = nest.Create("parrot_neuron", 65)
    dcn_n = nest.Create("parrot_neuron", 65)

    # feedback smoothed neuron
    N_fbk = N
    pop_params = {
        "kp": 1.0,
        "buffer_size": 100,
        "base_rate": 1.0,
        "simulation_steps": int(t_trial * N_trials),
    }
    fbk_smooth_p = nest.Create("basic_neuron_nestml", N_fbk)
    nest.SetStatus(fbk_smooth_p, {**pop_params, "pos": True})
    fbk_smooth_n = nest.Create("basic_neuron_nestml", N_fbk)
    nest.SetStatus(fbk_smooth_n, {**pop_params, "pos": False})

    # prediction neuron
    N_pred = N
    pop_params = {
        "kp": 1.0,
        "buffer_size": 100,
        "base_rate": 1.0,
        "simulation_steps": int(t_trial * N_trials),
    }
    pred_p = nest.Create("diff_neuron_nestml", N_pred)
    nest.SetStatus(pred_p, {**pop_params, "pos": True})
    pred_n = nest.Create("diff_neuron_nestml", N_pred)
    nest.SetStatus(pred_n, {**pop_params, "pos": False})

    # state neuron
    buf_sz = 150
    param_neurons = {
        "kp": 1.0,
        "base_rate": 0.0,
        "buffer_size": buf_sz,
        "N_fbk": N_fbk,
        "N_pred": N_pred,
        # USELESS, HAVE TO CHANGE NESTML CODE (ARRAYS ARE INITILISED AT COMPILE TIME)
        "fbk_bf_size": N_fbk * int(buf_sz / 1.0),
        "pred_bf_size": N_pred * int(buf_sz / 1.0),
        # the nestml model has a hardcoded solution to stop any spikes in time_wait
        "time_wait": 0,
    }
    print(f"Params state: {param_neurons}")

    # state_neuron -> 400 rec, "state_neuron_nestml" -> 50 rec_types,   state_MAD_neuron
    state_p = nest.Create("state_neuron", N)
    nest.SetStatus(state_p, param_neurons)
    nest.SetStatus(state_p, {"pos": True})
    state_n = nest.Create("state_neuron", N)
    nest.SetStatus(state_n, param_neurons)
    nest.SetStatus(state_n, {"pos": False})

    rec_types_dict = nest.GetDefaults("state_neuron", ["receptor_types"])[0]
    print(f"Defaults rec_types: \n {list(rec_types_dict.items())} \n \n")

    return (
        sn_p,
        sn_n,
        fbk_smooth_p,
        fbk_smooth_n,
        pred_p,
        pred_n,
        state_p,
        state_n,
        dcn_p,
        dcn_n,
    )


def connect_neurons(
    sn_p,
    sn_n,
    fbk_smooth_p,
    fbk_smooth_n,
    pred_p,
    pred_n,
    state_p,
    state_n,
    dcn_p,
    dcn_n,
):
    # Sensory Input -> Feedback Smoothed Neurons
    w = 1.0
    """
    N_indegree_fbk = 1
    conn_spec = {
        "rule": "fixed_indegree",
        "indegree": N_indegree_fbk,
        "allow_multapses": False,
    }
    """
    syn_spec_p = {
        "weight": w,  # 0.008,
        "delay": 150.0,
    }
    syn_spec_n = {
        "weight": w,
        "delay": 150.0,
    }
    nest.Connect(
        sn_p,
        fbk_smooth_p,
        "one_to_one",  # conn_spec=conn_spec,  # "one_to_one",  # "all_to_all",
        syn_spec=syn_spec_p,
    )
    nest.Connect(
        sn_n,
        fbk_smooth_n,
        "one_to_one",  # conn_spec=conn_spec,  # "one_to_one",  # "all_to_all",
        syn_spec=syn_spec_n,
    )

    # dcn -> pred
    w = 1.0  # 0.008
    N_indegree_pred = 1
    conn_spec = {
        "rule": "fixed_indegree",
        "indegree": N_indegree_pred,
        "allow_multapses": False,
    }
    syn_spec_p = {
        "weight": w,
        "delay": 1.0,
    }
    syn_spec_n = {
        "weight": -w,
        "delay": 1.0,
    }
    nest.Connect(
        dcn_p,
        pred_p,
        conn_spec=conn_spec,  # conn_spec=conn_spec,  # "one_to_one",  # "all_to_all",
        syn_spec=syn_spec_p,
    )
    nest.Connect(
        dcn_n,
        pred_p,
        conn_spec=conn_spec,  # conn_spec=conn_spec,  # "one_to_one",  # "all_to_all",
        syn_spec=syn_spec_n,
    )
    nest.Connect(
        dcn_n,
        pred_n,
        conn_spec=conn_spec,  # conn_spec=conn_spec,  ## "one_to_one",  # "all_to_all",
        syn_spec=syn_spec_n,
    )
    nest.Connect(
        dcn_p,
        pred_n,
        conn_spec=conn_spec,  # conn_spec=conn_spec,  ## "one_to_one",  # "all_to_all",
        syn_spec=syn_spec_p,
    )

    # INTO state neurons
    st_p = state_p
    st_n = state_n
    fbk_sm_state_spec = {
        "weight": 1.0,
        "receptor_type": 2,
        "delay": 1.0,
    }
    for i, pre in enumerate(fbk_smooth_p):
        nest.Connect(
            pre,
            st_p,
            "all_to_all",
            syn_spec={**fbk_sm_state_spec, "receptor_type": i + 1},
        )
    for i, pre in enumerate(fbk_smooth_n):
        nest.Connect(
            pre,
            st_n,
            "all_to_all",
            syn_spec={**fbk_sm_state_spec, "receptor_type": i + 1},
        )
    offset = 201  # it doesn't have to be N but the number of FBK receptors of the state neuron
    pred_state_spec = {
        "weight": 1.0,
        "receptor_type": 1,
        "delay": 1.0,
    }
    for i, pre in enumerate(pred_p):
        nest.Connect(
            pre,
            st_p,
            "all_to_all",
            syn_spec={**pred_state_spec, "receptor_type": i + offset},
        )
    for i, pre in enumerate(pred_n):
        nest.Connect(
            pre,
            st_n,
            "all_to_all",
            syn_spec={**pred_state_spec, "receptor_type": i + offset},
        )

    return


def connect_mm(fbk_smooth_p, pred_p, state_p, sn_p, dcn_p):
    # use multimeter to record neuron parameters
    mm_state = nest.Create(
        "multimeter",
        {
            "record_from": [
                "in_rate",
                "lambda_poisson",
                "mean_fbk",
                "mean_pred",
                "var_fbk",
                "var_pred",
                "w_fbk",
                "w_pred",
                "CV_fbk",
                "CV_pred",
                # "total_CV",
                # "error_rate",
                # "fbk_rate",
                # "error_counts",
                # "current_error_input",
            ]
        },
    )
    mm_fbk_sm = nest.Create(
        "multimeter", {"record_from": ["in_rate", "lambda_poisson"]}
    )
    mm_pred = nest.Create("multimeter", {"record_from": ["in_rate", "lambda_poisson"]})

    nest.Connect(mm_state, state_p)
    nest.Connect(mm_fbk_sm, fbk_smooth_p)
    nest.Connect(mm_pred, pred_p)

    spike_rec_sn = nest.Create("spike_recorder")
    spike_rec_dcn = nest.Create("spike_recorder")
    spike_rec_state = nest.Create("spike_recorder")
    spike_rec_fbk = nest.Create("spike_recorder")
    spike_rec_pred = nest.Create("spike_recorder")

    nest.Connect(sn_p, spike_rec_sn)
    nest.Connect(dcn_p, spike_rec_dcn)
    nest.Connect(state_p, spike_rec_state)
    nest.Connect(fbk_smooth_p, spike_rec_fbk)
    nest.Connect(pred_p, spike_rec_pred)

    return (
        mm_state,
        mm_fbk_sm,
        mm_pred,
        spike_rec_sn,
        spike_rec_dcn,
        spike_rec_state,
        spike_rec_fbk,
        spike_rec_pred,
    )


def set_cereb_error(N, N_trials, t_trial, sn_p, sn_n, dcn_p, dcn_n, state_p, state_n):
    # create cereb feedback
    pop_params = {
        "kp": 1.0,
        "buffer_size": 10,
        "base_rate": 0.0,
        "simulation_steps": int(t_trial * N_trials),
    }
    feedback_p = nest.Create("basic_neuron_nestml", N)
    nest.SetStatus(feedback_p, {**pop_params, "pos": True})
    feedback_n = nest.Create("basic_neuron_nestml", N)
    nest.SetStatus(feedback_n, {**pop_params, "pos": False})

    # create cereb error pop
    pop_params = {
        "kp": 1.0,
        "buffer_size": 30,
        "base_rate": 1.0,
        "simulation_steps": int(t_trial * N_trials),
    }
    error_p = nest.Create("diff_neuron_nestml", N)
    nest.SetStatus(error_p, {**pop_params, "pos": True})
    error_n = nest.Create("diff_neuron_nestml", N)
    nest.SetStatus(error_n, {**pop_params, "pos": False})

    # connect cereb feedback (from sn)
    w = 0.005
    syn_spec_p = {"weight": w, "delay": 150.0}
    syn_spec_n = {"weight": -w, "delay": 150.0}
    nest.Connect(
        sn_p,
        feedback_p,
        "all_to_all",
        syn_spec=syn_spec_p,
    )
    nest.Connect(
        sn_n,
        feedback_n,
        "all_to_all",
        syn_spec=syn_spec_n,
    )

    # connect cereb error (from cereb feedback & dcn)
    # from cereb_feedback
    w = 0.005
    syn_spec_p = {"weight": w, "delay": 1.0}
    syn_spec_n = {"weight": -w, "delay": 1.0}
    nest.Connect(
        feedback_p,
        error_p,
        "all_to_all",
        syn_spec=syn_spec_p,
    )
    nest.Connect(
        feedback_p,
        error_n,
        "all_to_all",
        syn_spec=syn_spec_p,
    )
    nest.Connect(
        feedback_n,
        error_p,
        "all_to_all",
        syn_spec=syn_spec_n,
    )
    nest.Connect(
        feedback_n,
        error_n,
        "all_to_all",
        syn_spec=syn_spec_n,
    )

    # from dcn
    w = -0.0154
    syn_spec_p = {"weight": w, "delay": 150.0}
    syn_spec_n = {"weight": -w, "delay": 150.0}
    nest.Connect(
        dcn_n,
        error_p,
        "all_to_all",
        syn_spec=syn_spec_n,
    )
    nest.Connect(
        dcn_n,
        error_n,
        "all_to_all",
        syn_spec=syn_spec_n,
    )
    nest.Connect(
        dcn_p,
        error_p,
        "all_to_all",
        syn_spec=syn_spec_p,
    )
    nest.Connect(
        dcn_p,
        error_n,
        "all_to_all",
        syn_spec=syn_spec_p,
    )

    # connect to state
    error_state_params = {
        "buffer_size_error": 25,
        "N_error": N,
        "C_error": 5,
        "error_bf_size": 25,
    }
    nest.SetStatus(state_p, error_state_params)
    nest.SetStatus(state_n, error_state_params)
    w_error = 1.0
    syn_spec_p = {"weight": w_error, "delay": 1.0, "receptor_type": 401}
    syn_spec_n = {"weight": -w_error, "delay": 1.0, "receptor_type": 401}
    nest.Connect(
        error_p,
        state_p,
        "all_to_all",
        syn_spec=syn_spec_p,
    )
    nest.Connect(
        error_n,
        state_p,
        "all_to_all",
        syn_spec=syn_spec_n,
    )
    nest.Connect(
        error_p,
        state_n,
        "all_to_all",
        syn_spec=syn_spec_p,
    )
    nest.Connect(
        error_n,
        state_n,
        "all_to_all",
        syn_spec=syn_spec_n,
    )

    # connect spike recorder
    spike_rec_error_p = nest.Create("spike_recorder")
    spike_rec_error_n = nest.Create("spike_recorder")
    spike_rec_fbk_p = nest.Create("spike_recorder")
    spike_rec_fbk_n = nest.Create("spike_recorder")

    nest.Connect(error_p, spike_rec_error_p)
    nest.Connect(error_n, spike_rec_error_n)
    nest.Connect(feedback_p, spike_rec_fbk_p)
    nest.Connect(feedback_n, spike_rec_fbk_n)

    return spike_rec_error_p, spike_rec_error_n, spike_rec_fbk_p, spike_rec_fbk_n


def connect_generators_from_file(sn, sn_data, N200=None):
    senders = sn_data.senders
    times = sn_data.times
    gids = sn_data.gids
    spike_gen = []

    if N200 is not None:
        use_gids = gids[:N200]
    else:
        use_gids = gids

    for gid in use_gids:
        neuron_spike_times = times[senders == gid]
        neuron_spike_times = np.unique(np.sort(neuron_spike_times))
        sg = nest.Create(
            "spike_generator", 1, params={"spike_times": neuron_spike_times}
        )
        spike_gen.append(sg.global_id)

    nest.Connect(spike_gen, sn, "one_to_one")

    return spike_gen


def connect_poiss_generators(dcn, lambda_mean, var, condition=None):
    dcn_gens_id = []
    dcn_gens = []
    lambdas = []

    if condition == "learning":
        print("DCN in learning condition: diverse lambda")
        for i in range(len(dcn)):
            x = np.random.normal(lambda_mean, var)
            while x < 0:
                x = np.random.normal(lambda_mean, var)
            lambdas.append(x)

    else:
        print("DCN in default condition: same lambda")
        for i in range(len(dcn)):
            lambdas.append(lambda_mean)

    for l in lambdas:
        g_p = nest.Create("poisson_generator", 1, {"rate": l})
        dcn_gens_id.append(g_p.global_id)
        dcn_gens.append(g_p)

    nest.Connect(dcn_gens_id, dcn, "one_to_one")  # connect by id

    return dcn_gens  # return NodeCollection


def update_lambda_dcn(lambda_mean, var, dcn_pg_p, dcn_pg_n, N):
    lambda_p = []
    lambda_n = []
    for i in range(65):
        x = np.random.normal(lambda_mean, var)
        while x < 0:
            x = np.random.normal(lambda_mean, var)
        lambda_p.append(x)
    for i in range(65):
        x = np.random.normal(lambda_mean, var)
        while x < 0:
            x = np.random.normal(lambda_mean, var)
        lambda_n.append(x)

    for g, l in zip(dcn_pg_p, lambda_p):
        nest.SetStatus(g, {"rate": l})
    for g, l in zip(dcn_pg_n, lambda_n):
        nest.SetStatus(g, {"rate": l})

    return


def generate_param_plot(data, pop_name, param_name, plots_path, plot_one_n=True):
    senders = np.array(data["senders"])
    times = np.array(data["times"])
    param = np.array(data[param_name])

    fig = plt.figure(figsize=(10, 6))

    # take one neuron (id=sender)
    if plot_one_n:
        gid = np.unique(senders)[0]
        mask = senders == gid
        plt.plot(times[mask], param[mask])
        plt.title(f"{pop_name} - {param_name} - neuron {gid}")
        # if param_name == "CV_fbk" or param_name == "CV_pred":
        #    plt.ylim(0, 1)

    # plot all neurons
    else:
        for gid in np.unique(senders):
            mask = senders == gid
            plt.plot(
                times[mask], param[mask], color=(0, 0, 0, 0.05), label=f"Neuron {gid}"
            )
        plt.title(f"{pop_name} - {param_name} - all neurons")
        # plt.legend()

    plt.xlabel("Time (ms)")
    plt.ylabel(param_name)

    fig.savefig(plots_path / f"{pop_name}_{param_name}.png")
    plt.close(fig)
    return


def plot_params_from_mm(data_state, data_fbk_sm, data_pred, plots_path):

    # PLOT PARAMS 1 STATE NEURON (they are all the same)
    params_state = [
        "lambda_poisson",
        "var_fbk",
        "var_pred",
        "mean_fbk",
        "mean_pred",
        "w_fbk",
        "w_pred",
        "CV_fbk",
        "CV_pred",
        # "error_rate",
        # "fbk_rate",
        # "error_counts",
        # "current_error_input",
    ]
    pop_name = "State_Estimator"
    for param in params_state:
        generate_param_plot(data_state, pop_name, param, plots_path, plot_one_n=True)

    # PLOT PARAMS ALL NEURON OF ONE POP
    params_fbk_sm = ["lambda_poisson"]
    pop_name = "Fbk_Smooth"
    for param in params_fbk_sm:
        generate_param_plot(data_fbk_sm, pop_name, param, plots_path, plot_one_n=False)

    params_pred = ["lambda_poisson"]
    pop_name = "Prediction"
    for param in params_pred:
        generate_param_plot(data_pred, pop_name, param, plots_path, plot_one_n=False)

    return


def compute_rate_from_spikes(spike_rec):
    bf_sz = 10
    data = nest.GetStatus(spike_rec, "events")[0]
    senders = np.array(data["senders"])
    times = np.array(data["times"])

    if times.size == 0:
        return np.array([]), np.array([])

    gids = np.unique(senders)
    n_neurons = len(gids)

    t_min, t_max = np.min(times), np.max(times)
    bins = np.arange(t_min, t_max + bf_sz, bf_sz)
    counts, _ = np.histogram(times, bins=bins)

    rate = 1000 * counts / (n_neurons * bf_sz)

    rate_padded = np.pad(rate, pad_width=2, mode="reflect")
    rate_sm = np.convolve(rate_padded, np.ones(5) / 5, mode="valid")

    times_plot = bins[:-1]

    return times_plot, rate_sm


def plot_spikes(spike_rec_p, spike_rec_n, plots_path, plot_name):
    t_p, rate_p = compute_rate_from_spikes(spike_rec_p)
    t_n, rate_n = compute_rate_from_spikes(spike_rec_n)

    plt.figure(figsize=(10, 4))

    if t_p.size > 0 and rate_p.size > 0:
        plt.plot(t_p, rate_p, label=f"{plot_name} +", linewidth=2, color="tab:red")
    else:
        plt.plot([], [], label=f"{plot_name} + ")

    if t_n.size > 0 and rate_n.size > 0:
        plt.plot(t_n, rate_n, label=f"{plot_name} -", linewidth=2, color="tab:blue")
    else:
        plt.plot([], [], label=f"{plot_name} - ")

    plt.title(f"{plot_name}")
    plt.xlabel("Time (ms)")
    plt.ylabel("Mean firing rate (Hz)")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()

    out_path = Path(plots_path) / f"{plot_name}_PSTH.png"
    plt.savefig(out_path)
    plt.close()
    return


def plot_spikes_overlay(spike_sn, spike_fbk, spike_pred, spike_state, plots_path):
    t_sn, r_sn = compute_rate_from_spikes(spike_sn)
    t_fbk, r_fbk = compute_rate_from_spikes(spike_fbk)
    t_pred, r_pred = compute_rate_from_spikes(spike_pred)
    t_state, r_state = compute_rate_from_spikes(spike_state)

    plt.figure(figsize=(12, 5))

    plt.plot(t_sn, r_sn, label="Sensory", linewidth=2)
    plt.plot(t_fbk, r_fbk, label="Fbk Smooth", linewidth=2)
    plt.plot(t_pred, r_pred, label="Prediction", linewidth=2)
    plt.plot(t_state, r_state, label="State", linewidth=2)

    plt.title("Overlay Firing Rates of Populations")
    plt.xlabel("Time (ms)")
    plt.ylabel("Rate (Hz)")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()

    out_path = Path(plots_path) / "Overlay_PSTH.png"
    plt.savefig(out_path)
    plt.close()
    return


if __name__ == "__main__":
    nest.ResetKernel()

    if "custom_stdp_module" not in nest.Models():
        nest.Install("custom_stdp_module")
    nest.Install("state_check_module")
    # nest.Install("state_MAD_module")
    # print("Nest Models: ", nest.Models())
    kernel_params = {
        "resolution": 1.0,
        "overwrite_files": True,
        "rng_seed": 12345,
    }
    nest.SetKernelStatus(kernel_params)

    ########################## SET EXPERIMENT PARAMS ############à
    N = 200  # SE CAMBI RICORDA DI CAMBIARE PATH INPUT SN, OFFSET RECEPTOR TYPE e pesi in connessioni AtoA
    N_trials = 1

    t_trial = 1000.0  # ms
    sim_time = N_trials * t_trial

    postlearning = False

    use_cereb_error = False

    rate_mean_pre = 50
    sdev_pre = 50
    rate_mean_post = 1
    sdev_post = 1
    condition = "learning"  # None  # "learning"  --> diverse lambda (distribuziuone norm con mean lambda_mean e varianza var)

    """
    update_lambda = False
    max_var = 50
    min_var = 0
    step_var = (max_var - min_var) / N_trials
    # var_t = np.arange(max_var, min_var, -step_var)
    var_t = [50, 0]
    """

    ############################ CREATE 5 CONNECT NETWORK NODES #############################
    # create neurons
    (
        sn_p,
        sn_n,
        fbk_smooth_p,
        fbk_smooth_n,
        pred_p,
        pred_n,
        state_p,
        state_n,
        dcn_p,
        dcn_n,
    ) = create_neurons(N, N_trials, t_trial)
    print("Neurons created")

    # connect neurons
    connect_neurons(
        sn_p,
        sn_n,
        fbk_smooth_p,
        fbk_smooth_n,
        pred_p,
        pred_n,
        state_p,
        state_n,
        dcn_p,
        dcn_n,
    )
    print("Neurons connected")

    # connect mm & spikes_rec
    (
        mm_state,
        mm_fbk_sm,
        mm_pred,
        spike_sn,
        spike_dcn,
        spike_state,
        spike_fbk,
        spike_pred,
    ) = connect_mm(fbk_smooth_p, pred_p, state_p, sn_p, dcn_p)
    (
        mm_state_n,
        mm_fbk_sm_n,
        mm_pred_n,
        spike_sn_n,
        spike_dcn_n,
        spike_state_n,
        spike_fbk_n,
        spike_pred_n,
    ) = connect_mm(fbk_smooth_n, pred_n, state_n, sn_n, dcn_n)
    print("Multimeters connected")

    # CREATE & CONNECT CEREB_ERROR
    if use_cereb_error:
        (
            spike_cereb_error_p,
            spike_cereb_error_n,
            spike_cereb_fbk_p,
            spike_cereb_fbk_n,
        ) = set_cereb_error(
            N, N_trials, t_trial, sn_p, sn_n, dcn_p, dcn_n, state_p, state_n
        )

    # CONNECT GENERATORS
    # load spikes for sn (only sn_p spikes) --> !! CAMBIA SE USI DIVERSO N
    # STATE_fbk1to1 200SN_90140
    data_path = paths.RUNS_DIR / "A_N200_nostate" / "data/neural"
    sn_p_path = data_path / "sensoryneur_p.json"
    with open(sn_p_path, "r") as f:
        sn_data_p = PopulationSpikes.model_validate_json(f.read())

    connect_generators_from_file(sn_p, sn_data_p, N200=None)

    if postlearning:
        dcn_pg_p = connect_generators_from_file(dcn_p, sn_data_p, N200=65)
        dcn_pg_n = connect_poiss_generators(
            dcn_n, rate_mean_post, sdev_post, condition=None
        )
    else:
        dcn_pg_p = connect_poiss_generators(
            dcn_p, rate_mean_pre, sdev_pre, condition="learning"
        )
        dcn_pg_n = connect_poiss_generators(
            dcn_n, rate_mean_pre, sdev_pre, condition="learning"
        )

    print("Spike generators connected to sensory neurons and dcn")

    # ############# - RUN SIMULATION - ########################
    print("Simulation Started")
    for n in range(N_trials):
        """
        if update_lambda:
            var_tn = var_t[n]
            update_lambda_dcn(rate_mean, var_tn, dcn_pg_p, dcn_pg_n, N)
        """
        nest.Simulate(t_trial)
    print("Simulation Completed")

    # ############# - PLOTS - ########################
    data_state = nest.GetStatus(mm_state, "events")[0]
    data_fbk_sm = nest.GetStatus(mm_fbk_sm, "events")[0]
    data_pred = nest.GetStatus(mm_pred, "events")[0]

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = Path(__file__).parent
    plots_paths = base_path / "runs_tests_state" / f"run_{timestamp}"
    plots_paths.mkdir(parents=True, exist_ok=True)
    plot_params_from_mm(data_state, data_fbk_sm, data_pred, plots_paths)
    plot_spikes(spike_sn, spike_sn_n, plots_paths, plot_name="Spikes_Sensory_Neurons")
    plot_spikes(spike_dcn, spike_dcn_n, plots_paths, plot_name="Spikes_DCN")
    plot_spikes(spike_fbk, spike_fbk_n, plots_paths, plot_name="Spikes_Feedback_smooth")
    plot_spikes(spike_pred, spike_pred_n, plots_paths, plot_name="Spikes_Pred")
    plot_spikes(spike_state, spike_state_n, plots_paths, plot_name="Spikes_State")
    if use_cereb_error:
        plot_spikes(
            spike_cereb_error_p,
            spike_cereb_error_n,
            plots_paths,
            plot_name="Spikes_Cereb_Error",
        )
        plot_spikes(
            spike_cereb_fbk_p,
            spike_cereb_fbk_n,
            plots_paths,
            plot_name="Spikes_Cereb_Fbk",
        )

    plot_spikes_overlay(spike_sn, spike_fbk, spike_pred, spike_state, plots_paths)
    print("Plots saved in ", plots_paths)
