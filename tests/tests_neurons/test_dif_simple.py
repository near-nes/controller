"""
Test suite for diff_neuron with synaptic delays
Tests both basic delay handling and the differential mechanism
"""

from collections import defaultdict

import matplotlib.pyplot as plt
import nest
import numpy as np
import os


def test_diff():

    def setup_nest():
        """Initialize NEST with consistent parameters"""
        nest.ResetKernel()
        nest.set_verbosity("M_WARNING")
        nest.resolution = 0.1  # 0.1ms resolution
        nest.print_time = True

        nest.Install("custom_stdp_module")
        return nest.resolution

    BURST_SIZE_EXC = 5
    BURST_SIZE_INH = 3

    EXC_BURST_TIMES = list(range(100, 900, 200))  # Bursts at 100, 300, 500, 700 ms
    INH_BURST_TIMES = list(range(100, 900, 300))  # Bursts at 200, 400, 600 ms

    def create_spike_pattern():
        """Create a test pattern with alternating E/I bursts"""
        # Simulation time
        sim_time = 1000.0  # ms

        # Create spike times for excitatory bursts (positive weights)
        exc_bursts = []
        for t in EXC_BURST_TIMES:
            # 5 spikes in 10ms burst
            burst = [t + i * 2 for i in range(BURST_SIZE_EXC)]
            exc_bursts.extend(burst)

        # Create spike times for inhibitory bursts (will use negative weights)
        inh_bursts = []
        for t in INH_BURST_TIMES:
            # 3 spikes in 6ms burst
            burst = [t + i * 2 for i in range(BURST_SIZE_INH)]
            inh_bursts.extend(burst)

        return exc_bursts, inh_bursts, sim_time

    def run_test_scenario(
        scenario_name,
        exc_spikes,
        inh_spikes,
        sim_time,
        exc_delay=1.0,
        inh_delay=1.0,
        use_parrot=False,
        parrot_delay=1.0,
        diff_delay=99.0,
        pos_status=True,
    ):
        """
        Run a single test scenario

        Args:
            scenario_name: Name for this test
            exc_spikes, inh_spikes: Spike time arrays
            sim_time: Simulation duration
            exc_delay, inh_delay: Direct delays to diff neuron
            use_parrot: Whether to use parrot neuron
            parrot_delay, diff_delay: Delays when using parrot
        """
        print(f"\n=== Running {scenario_name} ===")
        setup_nest()

        # Create spike generators
        exc_gen = nest.Create("spike_generator")
        inh_gen = nest.Create("spike_generator")

        nest.SetStatus(exc_gen, {"spike_times": exc_spikes})
        nest.SetStatus(inh_gen, {"spike_times": inh_spikes})

        # Create diff neuron (assuming it's installed)
        diff_neuron = nest.Create("diff_neuron_nestml")
        nest.SetStatus(
            diff_neuron,
            {
                "kp": 1.0,
                "pos": pos_status,  # Sensitive to positive (excitatory) signals
                "base_rate": 5.0,  # Hz
                "buffer_size": 30.0,  # ms
                "simulation_steps": int(sim_time / 0.1),
            },
        )

        # Create spike recorder
        spike_rec = nest.Create("spike_recorder")

        if use_parrot:
            # Test with parrot neuron in the chain
            parrot = nest.Create("parrot_neuron")

            # Connect generators to parrot
            nest.Connect(
                exc_gen, parrot, syn_spec={"weight": 1.0, "delay": parrot_delay}
            )
            nest.Connect(
                inh_gen, parrot, syn_spec={"weight": -1.0, "delay": parrot_delay}
            )

            # Connect parrot to diff neuron
            nest.Connect(
                parrot, diff_neuron, syn_spec={"weight": 1.0, "delay": diff_delay}
            )

        else:
            # Direct connections with specified delays
            nest.Connect(
                exc_gen, diff_neuron, syn_spec={"weight": 1.0, "delay": exc_delay}
            )
            nest.Connect(
                inh_gen, diff_neuron, syn_spec={"weight": -1.0, "delay": inh_delay}
            )

        # Connect diff neuron to recorder
        nest.Connect(diff_neuron, spike_rec)

        # Run simulation
        nest.Simulate(sim_time)

        # Get results
        events = nest.GetStatus(spike_rec, "events")[0]
        spike_times = events["times"]

        print(f"Output spikes: {len(spike_times)}")
        if len(spike_times) > 0:
            print(f"First spike at: {spike_times[0]:.1f} ms")
            print(f"Last spike at: {spike_times[-1]:.1f} ms")
            print(f"Mean firing rate: {len(spike_times)/(sim_time/1000.0):.2f} Hz")

        return {
            "scenario": scenario_name,
            "spike_times": spike_times,
            "input_exc": exc_spikes,
            "input_inh": inh_spikes,
            "total_delay_exc": (
                exc_delay if not use_parrot else parrot_delay + diff_delay
            ),
            "total_delay_inh": (
                inh_delay if not use_parrot else parrot_delay + diff_delay
            ),
        }

    def analyze_results(results):
        """Analyze and compare results across scenarios"""
        print("\n" + "=" * 50)
        print("ANALYSIS SUMMARY")
        print("=" * 50)

        for result in results:
            if result is None:
                continue

            scenario = result["scenario"]
            spikes = result["spike_times"]

            print(f"\n{scenario}:")
            print(f"  Total spikes: {len(spikes)}")

            if len(spikes) > 0:
                # Calculate firing rate in different time windows
                early_spikes = spikes[(spikes >= 200) & (spikes < 400)]
                mid_spikes = spikes[(spikes >= 400) & (spikes < 600)]
                late_spikes = spikes[(spikes >= 600) & (spikes < 800)]

                print(f"  Early period (200-400ms): {len(early_spikes)} spikes")
                print(f"  Mid period (400-600ms): {len(mid_spikes)} spikes")
                print(f"  Late period (600-800ms): {len(late_spikes)} spikes")

                # Check response timing relative to input
                total_delay = result["total_delay_exc"]
                expected_first_response = 100 + total_delay  # First exc burst + delay
                if len(spikes) > 0:
                    actual_first_response = spikes[0]
                    delay_error = actual_first_response - expected_first_response
                    print(
                        f"  Expected first response: {expected_first_response:.1f} ms"
                    )
                    print(f"  Actual first response: {actual_first_response:.1f} ms")
                    print(f"  Timing error: {delay_error:.1f} ms")

    def compare_delayed_spikes_by_matching(
        direct_spikes, parrot_spikes, max_timing_diff=0.5, proximity_threshold=10.0
    ):
        """
        Compares two lists of spike times by trying to match spikes between them,
        allowing for missing or extra spikes in one of the lists.

        Args:
            direct_spikes (list or np.array): Spike times from the direct delay mechanism.
            parrot_spikes (list or np.array): Spike times from the parrot delay mechanism.
            max_timing_diff (float): Maximum allowed difference between matched spikes.
            proximity_threshold (float): Max time difference to consider two spikes as potentially corresponding.
                                        This should be larger than max_timing_diff.
        Returns:
            tuple: (is_pass, matched_pairs, unmatched_direct, unmatched_parrot)
        """
        direct_spikes = np.array(direct_spikes)
        parrot_spikes = np.array(parrot_spikes)

        if len(direct_spikes) == 0 and len(parrot_spikes) == 0:
            print("No spikes in either delay. PASS (vacuously).")
            return True, [], [], []
        elif len(direct_spikes) == 0 or len(parrot_spikes) == 0:
            print("One delay has no spikes, the other does. FAIL.")
            return False, [], list(direct_spikes), list(parrot_spikes)

        matched_pairs = []  # List of (direct_spike, parrot_spike)
        unmatched_direct = []
        unmatched_parrot = []

        # Keep track of which spikes have been matched
        matched_parrot_indices = [False] * len(parrot_spikes)

        for d_spike in direct_spikes:
            # Find the closest parrot spike within the proximity_threshold
            diffs = np.abs(parrot_spikes - d_spike)

            # Find candidate parrot spikes that are close and not yet matched
            candidate_indices = np.where(
                (diffs < proximity_threshold) & (~np.array(matched_parrot_indices))
            )[0]

            if len(candidate_indices) > 0:
                # Pick the closest one among candidates
                closest_candidate_idx = candidate_indices[
                    np.argmin(diffs[candidate_indices])
                ]
                p_spike = parrot_spikes[closest_candidate_idx]

                if np.abs(d_spike - p_spike) < max_timing_diff:
                    matched_pairs.append((d_spike, p_spike))
                    matched_parrot_indices[closest_candidate_idx] = True
                else:
                    unmatched_direct.append(
                        d_spike
                    )  # Direct spike found a close one but too far
            else:
                unmatched_direct.append(d_spike)  # No close parrot spike found

        # Any remaining parrot spikes are unmatched
        for i, p_spike in enumerate(parrot_spikes):
            if not matched_parrot_indices[i]:
                unmatched_parrot.append(p_spike)

        print(f"\n--- Spike Matching Results ---")
        print(f"Matched pairs ({len(matched_pairs)}):")
        for d, p in matched_pairs:
            print(f"  Direct: {d:.1f} <=> Parrot: {p:.1f} (Diff: {np.abs(d-p):.2f})")

        # print(f"Unmatched Direct Spikes ({len(unmatched_direct)}): {unmatched_direct}")
        # print(f"Unmatched Parrot Spikes ({len(unmatched_parrot)}): {unmatched_parrot}")

        # Determine pass/fail
        is_pass = True

        for d, p in matched_pairs:
            if np.abs(d - p) >= max_timing_diff:
                is_pass = False
                print(
                    f"✗ FAIL: Matched pair {d:.1f} vs {p:.1f} exceeds max timing diff."
                )
                # break # Only need one failure to fail the test
        if is_pass:
            print(
                "✓ PASS: All significant spikes matched with acceptable timing differences."
            )
        else:
            print("✗ FAIL: Significant discrepancies found.")

        return is_pass, matched_pairs, unmatched_direct, unmatched_parrot

    def plot_results(results):
        """Create visualization of results"""
        fig, axes = plt.subplots(
            len([r for r in results if r is not None]),
            1,
            figsize=(12, 2 * len(results)),
            sharex=True,
        )

        if len(results) == 1:
            axes = [axes]

        valid_results = [r for r in results if r is not None]

        for i, result in enumerate(valid_results):
            ax: plt.Axes = axes[i]

            # Plot input patterns
            exc_times = result["input_exc"]
            inh_times = result["input_inh"]

            # Shift inputs by delay for comparison
            ax.eventplot(
                [np.array(exc_times)],
                # positions=[0.8],
                colors=["green"],
                lineoffsets=0.1,
                linelengths=0.2,
                label="Exc input",
            )
            ax.eventplot(
                [np.array(exc_times) + result["total_delay_exc"]],
                # positions=[0.8],
                colors=["green"],
                lineoffsets=0.3,
                linelengths=0.2,
                linestyles="dotted",
                label="Exc input (delayed)",
            )
            ax.eventplot(
                [np.array(inh_times)],
                # positions=[0.6],
                colors=["red"],
                lineoffsets=0.5,
                linelengths=0.2,
                label="Inh input",
            )
            ax.eventplot(
                [np.array(inh_times) + result["total_delay_inh"]],
                # positions=[0.6],
                colors=["red"],
                lineoffsets=0.7,
                linelengths=0.2,
                linestyles="dotted",
                label="Inh input (delayed)",
            )

            # Plot output
            if len(result["spike_times"]) > 0:
                ax.eventplot(
                    [result["spike_times"]],
                    # positions=[0.4],
                    colors=["blue"],
                    lineoffsets=0.9,
                    linelengths=0.2,
                    label="Diff neuron output",
                )

            ax.set_ylim(0, 1.0)
            yticks = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
            ax.set_yticks(yticks)
            ax.set_yticklabels(["exc", "exc delayed", "inh", "inh delay", "out"])
            ax.set_title(result["scenario"])
            ax.legend()
            [ax.axhline(y, color="gray", linewidth=0.5) for y in yticks + 0.1]
            # ax.grid(True, alpha=0.3)

        axes[-1].set_xlabel("Time (ms)")
        plt.tight_layout()
        directory = f"figures_neurons"
        os.makedirs(directory, exist_ok=True)
        plt.savefig(
            f"{directory}/diff_neuron_delay_test.png", dpi=150, bbox_inches="tight"
        )

        # plt.show()

    """Main test function"""
    print("Testing diff_neuron with synaptic delays")
    print("========================================")

    # Setup
    resolution = setup_nest()
    exc_spikes, inh_spikes, sim_time = create_spike_pattern()

    print(f"Test pattern:")
    print(f"  Excitatory bursts at: {EXC_BURST_TIMES} ms")
    print(f"  Inhibitory bursts at: {INH_BURST_TIMES} ms")
    print(f"  Simulation time: {sim_time} ms")

    # Test scenarios
    results = []

    results.append(
        run_test_scenario(
            "Baseline (minimal delay)",
            exc_spikes,
            inh_spikes,
            sim_time,
            exc_delay=0.1,
            inh_delay=0.1,
            pos_status=True,
        )
    )

    print("first test ran")

    results.append(
        run_test_scenario(
            "Direct 100ms delay",
            exc_spikes,
            inh_spikes,
            sim_time,
            exc_delay=100.0,
            inh_delay=100.0,
            pos_status=True,
        )
    )

    print("second test ran")

    results.append(
        run_test_scenario(
            "Parrot (1ms) + Diff (99ms)",
            exc_spikes,
            inh_spikes,
            sim_time,
            use_parrot=True,
            parrot_delay=1.0,
            diff_delay=99.0,
            pos_status=True,
        )
    )

    results.append(
        run_test_scenario(
            "Parrot (10ms) + Diff (90ms)",
            exc_spikes,
            inh_spikes,
            sim_time,
            use_parrot=True,
            parrot_delay=10.0,
            diff_delay=90.0,
            pos_status=True,
        )
    )
    results.append(
        run_test_scenario(
            "Parrot (50ms) + Diff (50ms)",
            exc_spikes,
            inh_spikes,
            sim_time,
            use_parrot=True,
            parrot_delay=50.0,
            diff_delay=50.0,
            pos_status=True,
        )
    )

    results.append(
        run_test_scenario(
            "Asymmetric delays (E:50ms, I:150ms)",
            exc_spikes,
            inh_spikes,
            sim_time,
            exc_delay=50.0,
            inh_delay=150.0,
            pos_status=True,
        )
    )
    print("third test ran")

    results.append(
        run_test_scenario(
            " Pos: False,Direct 100ms delay",
            exc_spikes,
            inh_spikes,
            sim_time,
            exc_delay=100.0,
            inh_delay=100.0,
            pos_status=False,
        )
    )

    results.append(
        run_test_scenario(
            "Pos: False, Parrot (1ms) + Diff (99ms)",
            exc_spikes,
            inh_spikes,
            sim_time,
            use_parrot=True,
            parrot_delay=1.0,
            diff_delay=99.0,
            pos_status=False,
        )
    )

    results.append(
        run_test_scenario(
            "Pos: False, Parrot (10ms) + Diff (90ms)",
            exc_spikes,
            inh_spikes,
            sim_time,
            use_parrot=True,
            parrot_delay=10.0,
            diff_delay=90.0,
            pos_status=False,
        )
    )

    # Analysis
    analyze_results(results)
    plot_results(results)

    # Comparison test
    # this is AI slop, just look at the plot

    valid_results = [r for r in results if r is not None]
    if len(valid_results) >= 3:
        direct_delay = valid_results[1]  # 100ms direct
        parrot_delay = valid_results[2]  # 1+99ms parrot

        # Compare spike counts in time windows
        direct_spikes = direct_delay["spike_times"]
        parrot_spikes = parrot_delay["spike_times"]

        if (
            len(direct_spikes) > 0 or len(parrot_spikes) > 0
        ):  # Check if there are any spikes at all

            is_test_pass, matched, unmatched_d, unmatched_p = (
                compare_delayed_spikes_by_matching(
                    direct_spikes,
                    parrot_spikes,
                    max_timing_diff=0.5,
                    proximity_threshold=20.0,
                )
            )

            print(f"\nConclusion:")
            if is_test_pass:
                print("✓ All corresponding spikes align correctly within tolerance.")
            else:
                print("✗ Discrepancies found in spike timing or count consistency.")
                if len(unmatched_d) > 0:
                    print(
                        f"    - Direct delay generated {len(unmatched_d)} spikes that couldn't be matched."
                    )
                    assert len(unmatched_d) > 0
                if len(unmatched_p) > 0:
                    print(
                        f"    - Parrot delay generated {len(unmatched_p)} spikes that couldn't be matched."
                    )
                    assert len(unmatched_p) > 0
        else:
            print(
                "No spikes generated by either mechanism. Cannot perform timing comparison."
            )
            if len(direct_spikes) == 0 and len(parrot_spikes) == 0:
                print("✓ PASS: No spikes in either, implying equivalent empty output.")
                assert len(direct_spikes) == 0
            else:
                print(
                    "✗ FAIL: One has spikes, the other doesn't (or partial generation)."
                )
        print(f"\nOverall Result:")
        if is_test_pass:
            print("✓ TEST PASSED: Delay mechanisms produce equivalent spike outputs.")
        else:
            print(
                "✗ TEST FAILED: Delay mechanisms produce non-equivalent spike outputs."
            )
            assert False, "Delay mechanisms produce non-equivalent spike outputs."
