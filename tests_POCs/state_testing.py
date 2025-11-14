from complete_control.neural.neural_models import PopulationSpikes
from complete_control.config import paths
from complete_control.neural.nest_adapter import nest, initialize_nest
import numpy as np
import matplotlib.pyplot as plt
import datetime
from pathlib import Path

np.random.seed(12345)

initialize_nest("MUSIC")


def create_neurons(N, N_trials):
    ################## create neurons#########################
    # sensoryneuron
    sn_p = nest.Create("parrot_neuron", N)
    sn_n = nest.Create("parrot_neuron", N)

    # dcn neurons
    dcn_p = nest.Create("parrot_neuron", N)
    dcn_n = nest.Create("parrot_neuron", N)

    # feedback smoothed neuron
    pop_params = {
        "kp": 1.0,
        "buffer_size": 250,
        "base_rate": 1.0,
        "simulation_steps": 1500 * N_trials,
    }
    fbk_smooth_p = nest.Create("basic_neuron_nestml", N)
    nest.SetStatus(fbk_smooth_p, {**pop_params, "pos": True})
    fbk_smooth_n = nest.Create("basic_neuron_nestml", N)
    nest.SetStatus(fbk_smooth_n, {**pop_params, "pos": False})

    # prediction neuron
    pop_params = {
        "kp": 1.0,
        "buffer_size": 250,
        "base_rate": 1.0,
        "simulation_steps": 1500 * N_trials,
    }
    pred_p = nest.Create("diff_neuron_nestml", N)
    nest.SetStatus(pred_p, {**pop_params, "pos": True})
    pred_n = nest.Create("diff_neuron_nestml", N)
    nest.SetStatus(pred_n, {**pop_params, "pos": False})

    # state neuron
    buf_sz = 25
    param_neurons = {
        "kp": 1.4,
        "base_rate": 0.0,
        "N_fbk": N,
        "N_pred": N,
        "fbk_bf_size": N * int(buf_sz / 1.0),
        "pred_bf_size": N * int(buf_sz / 1.0),
        # the nestml model has a hardcoded solution to stop any spikes in time_wait
        "time_wait": 0,
    }
    print(f"Params state: {param_neurons}")

    state_p = nest.Create("state_neuron", N)  # "state_neuron_nestml" -> 50 rec_types
    nest.SetStatus(state_p, param_neurons)
    nest.SetStatus(state_p, {"pos": True})
    state_n = nest.Create("state_neuron", N)
    nest.SetStatus(state_n, param_neurons)
    nest.SetStatus(state_n, {"pos": False})

    rec_types_dict = nest.GetDefaults("state_neuron", ["receptor_types"])[0]
    print(f"Defaults rec_types: \n {list(rec_types_dict.items())[-5:]} \n \n")

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
    syn_spec_p = {
        "weight": 1.0,
        "delay": 1.0,
    }
    syn_spec_n = {
        "weight": 1.0,
        "delay": 1.0,
    }
    nest.Connect(
        sn_p,
        fbk_smooth_p,
        "one_to_one",  # "all_to_all",
        syn_spec=syn_spec_p,
    )
    nest.Connect(
        sn_n,
        fbk_smooth_n,
        "one_to_one",  # "all_to_all",
        syn_spec=syn_spec_n,
    )

    # dcn -> pred
    w = 1.0
    syn_spec_p = {
        "weight": w,
        "delay": 1.0,
    }
    syn_spec_n = {
        "weight": 0.0,  # -w,
        "delay": 1.0,
    }
    nest.Connect(
        dcn_p,
        pred_p,
        "one_to_one",  # "all_to_all",
        syn_spec=syn_spec_p,
    )
    nest.Connect(
        dcn_n,
        pred_p,
        "one_to_one",  # "all_to_all",
        syn_spec=syn_spec_n,
    )
    nest.Connect(
        dcn_n,
        pred_n,
        "one_to_one",  # "all_to_all",
        syn_spec=syn_spec_n,
    )
    nest.Connect(
        dcn_p,
        pred_n,
        "one_to_one",  # "all_to_all",
        syn_spec_p,
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
                "CV_fbk",
                "CV_pred",
                "total_CV",
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

    # plot all neurons
    else:
        for gid in np.unique(senders):
            mask = senders == gid
            plt.plot(times[mask], param[mask], label=f"Neuron {gid}")
        plt.title(f"{pop_name} - {param_name} - all neurons")
        plt.legend()

    plt.xlabel("Time (ms)")
    plt.ylabel(param_name)

    fig.savefig(plots_path / f"{pop_name}_{param_name}.png")
    plt.close(fig)
    return


def plot_params_from_mm(data_state, data_fbk_sm, data_pred, plots_path):

    # PLOT PARAMS 1 STATE NEURON (they are all the same)
    params_state = ["lambda_poisson", "var_fbk", "var_pred", "CV_fbk", "CV_pred"]
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


def connect_generators_sn(sn, sn_data):
    senders = sn_data.senders
    times = sn_data.times
    gids = sn_data.gids
    spike_gen = []

    for gid in gids:
        neuron_spike_times = times[senders == gid]
        neuron_spike_times = np.unique(np.sort(neuron_spike_times))
        sg = nest.Create(
            "spike_generator", 1, params={"spike_times": neuron_spike_times}
        )
        spike_gen.append(sg.global_id)

    nest.Connect(spike_gen, sn, "one_to_one")

    return


def connect_poiss_generators(dcn_p, dcn_n, lambda_mean, var, condition=None):
    dcn_gens_p_id = []
    dcn_gens_n_id = []
    dcn_gens_p = []
    dcn_gens_n = []
    lambda_p = []
    lambda_n = []

    if condition == "learning":
        print("DCN in learning condition: diverse lambda")
        for i in range(len(dcn_p)):
            x = np.random.normal(lambda_mean, var)
            while x < 0:
                x = np.random.normal(lambda_mean, var)
            lambda_p.append(x)
        for i in range(len(dcn_n)):
            x = np.random.normal(lambda_mean, var)
            while x < 0:
                x = np.random.normal(lambda_mean, var)
            lambda_n.append(x)
    else:
        print("DCN in default condition: same lambda")
        for i in range(len(dcn_p)):
            lambda_p.append(lambda_mean)
        for i in range(len(dcn_n)):
            lambda_n.append(lambda_mean)

    for l in lambda_p:
        g_p = nest.Create("poisson_generator", 1, {"rate": l})
        dcn_gens_p_id.append(g_p.global_id)
        dcn_gens_p.append(g_p)
    for l in lambda_n:
        g_n = nest.Create("poisson_generator", 1, {"rate": l})
        dcn_gens_n_id.append(g_n.global_id)
        dcn_gens_n.append(g_n)

    nest.Connect(dcn_gens_p_id, dcn_p, "one_to_one")  # connect by id
    nest.Connect(dcn_gens_n_id, dcn_n, "one_to_one")
    return dcn_gens_p, dcn_gens_n  # return NodeCollection


def plot_spikes(spike_rec, plots_path, plot_name):
    bf_sz = 10
    data = nest.GetStatus(spike_rec, "events")[0]
    senders = np.array(data["senders"])
    times = np.array(data["times"])

    gids = np.unique(senders)
    n_neurons = len(gids)

    t_min, t_max = np.min(times), np.max(times)
    bins = np.arange(t_min, t_max + bf_sz, bf_sz)
    counts, _ = np.histogram(times, bins=bins)

    rate = 1000 * counts / (n_neurons * bf_sz)

    rate_padded = np.pad(rate, pad_width=2, mode="reflect")
    rate_sm = np.convolve(rate_padded, np.ones(5) / 5, mode="valid")

    plt.figure(figsize=(10, 4))
    plt.plot(bins[:-1], rate_sm, color="tab:blue")
    """
    plt.bar(
        bin_centers,
        rate,
        width=bf_sz,
        align="center",
        color="tab:blue",
        edgecolor="none",
    )
    """
    plt.title(f"{plot_name}")
    plt.xlabel("Time (ms)")
    plt.ylabel("Mean firing rate (Hz)")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()

    out_path = Path(plots_path) / f"{plot_name}_PSTH.png"
    plt.savefig(out_path)
    plt.close()
    return


def update_lambda_dcn(lambda_mean, var, dcn_pg_p, dcn_pg_n, N):
    lambda_p = []
    lambda_n = []
    for i in range(N):
        x = np.random.normal(lambda_mean, var)
        while x < 0:
            x = np.random.normal(lambda_mean, var)
        lambda_p.append(x)
    for i in range(N):
        x = np.random.normal(lambda_mean, var)
        while x < 0:
            x = np.random.normal(lambda_mean, var)
        lambda_n.append(x)

    for g, l in zip(dcn_pg_p, lambda_p):
        nest.SetStatus(g, {"rate": l})
    for g, l in zip(dcn_pg_n, lambda_n):
        nest.SetStatus(g, {"rate": l})

    return


if __name__ == "__main__":
    nest.ResetKernel()

    if "custom_stdp_module" not in nest.Models():
        nest.Install("custom_stdp_module")
    nest.Install("state_check_module")
    # print("Nest Models: ", nest.Models())
    kernel_params = {
        "resolution": 1.0,
        "overwrite_files": True,
        "rng_seed": 12345,
    }
    nest.SetKernelStatus(kernel_params)

    ########################## SET EXPERIMENT PARAMS ############à
    N = 100  # SE CAMBI RICORDA DI CAMBIARE PATH INPUT SN, OFFSET RECEPTOR TYPE
    N_trials = 10

    t_trial = 500.0  # ms
    sim_time = N_trials * t_trial

    rate_mean = 50
    sdev = 50
    condition = None  # None  # "learning"  --> diverse lambda (distribuziuone norm con mean lambda_mean e varianza var)

    update_lambda = True
    max_var = 50
    min_var = 0
    step_var = (max_var - min_var) / N_trials
    var_t = np.arange(max_var, min_var, -step_var)

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
    ) = create_neurons(N, N_trials)
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

    # CONNECT GENERATORS
    # load spikes for sn (only sn_p spikes) --> !! CAMBIA SE USI DIVERSO N
    data_path = (
        paths.RUNS_DIR / "STATE_fbk1to1" / "data/neural"
    )  # STATE_fbk1to1 200SN_90140
    sn_p_path = data_path / "sensoryneur_p.json"
    with open(sn_p_path, "r") as f:
        sn_data_p = PopulationSpikes.model_validate_json(f.read())
    # connect_generators_sn(sn_p, sn_data_p)  #usa solo con 2 trial di 1500ms e N=50 o 200

    dcn_pg_p, dcn_pg_n = connect_poiss_generators(
        dcn_p, dcn_n, rate_mean, sdev, condition
    )
    sn_pg_p, sn_pg_n = connect_poiss_generators(
        sn_p, sn_n, rate_mean, sdev, condition=None
    )
    print("Spike generators connected to sensory neurons and dcn")

    # ############# - RUN SIMULATION - ########################
    print("Simulation Started")
    for n in range(N_trials):
        if update_lambda:
            var_tn = var_t[n]
            update_lambda_dcn(rate_mean, var_tn, dcn_pg_p, dcn_pg_n, N)

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
    plot_spikes(spike_sn, plots_paths, plot_name="Spikes_Sensory_Neurons")
    plot_spikes(spike_dcn, plots_paths, plot_name="Spikes_DCN")
    plot_spikes(spike_fbk, plots_paths, plot_name="Spikes_Feedback_smooth")
    plot_spikes(spike_pred, plots_paths, plot_name="Spikes_Pred")
    plot_spikes(spike_dcn_n, plots_paths, plot_name="Spikes_DCN_Neg")
    plot_spikes(spike_pred_n, plots_paths, plot_name="Spikes_Pred_Neg")
    plot_spikes(spike_state, plots_paths, plot_name="Spikes_State")
    print("Plots saved in ", plots_paths)
