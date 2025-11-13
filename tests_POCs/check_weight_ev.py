import sys

sys.path.append("/sim/controller/complete_control")


from complete_control.neural.neural_models import SynapseBlock
from complete_control.neural.result_models import NeuralResultManifest
from complete_control.config.ResultMeta import ResultMeta

ids = [
    "20251112_142047_7bri-singletrial",
    "20251113_104618_uhx3-singletrial",
    "20251113_113025_ukpm-singletrial",
    "20251113_113319_99um-singletrial",
]


def main():
    for i in range(1):
        for id in ids:
            meta = ResultMeta.from_id(id)
            neural = meta.load_neural()
            with open(neural.weights[0], "r") as f:
                block = SynapseBlock.model_validate_json(f.read())
            print(
                f"{meta.id}->{block.source_pop_label}-{block.target_pop_label}[0]:{block.synapse_recordings[i].weight}"
            )


if __name__ == "__main__":
    main()
