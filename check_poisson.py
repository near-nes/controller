import numpy as np

SEED = 12345
np.random.default_rng(SEED)


def lam(signal):
    rate = 40 * abs(signal)
    return rate


if __name__ == "__main__":
    signal = 1.5

    rng = np.random.default_rng(SEED)
    lmd = lam(signal) * 0.001
    nEv = rng.poisson(lam=lmd, size=50)
    cnt = 0
    for i in nEv:
        if i > 0:
            cnt += 1

    print("lambda: ", lmd)
    print("distrib: ", nEv)
    print("firing neuron: ", cnt, "/50 --> freq ", cnt * 1000)
    print("expect Hz: ", lmd / 0.001)
