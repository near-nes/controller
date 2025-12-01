#!/usr/bin/env python3

from neural.nest_adapter import initialize_nest, nest

initialize_nest("MUSIC")

nest.Install("state_check_module")

if __name__ == "__main__":

    params = [
        "N_fbk",
        "N_pred",
        "receptor_types",
    ]
    neuron = nest.Create("state_neuron")

    print(f'Defaults: \n {nest.GetDefaults("state_neuron", params)} \n \n')

    # nest.SetStatus(neuron, {"N_fbk": 150, "N_pred": 150})
    nest.GetDefaults("state_neuron", params)
    print(f"State params: {nest.GetStatus(neuron, params)}")
