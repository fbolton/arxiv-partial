import collections
import pathlib

import qiskit.circuit
import selector
import scrambler
import partial
import groverlong

# Doc for qiskit.visualization - https://qiskit.org/documentation/tutorials/circuits/2_plotting_data_in_qiskit.html
import qiskit.visualization

# Import the matplotlib backend
import matplotlib


# 'matplotlib' backend defaults to TkAgg (which requires package 'tkinter')
# If 'tkinter' is not yet installed on your machine, you can install it e.g. on Ubuntu, with the command:
# sudo apt-get install python3-tk

def main():
    # If you want to change the 'matplotlib' backend, use this code:
    matplotlib.use('TkAgg')
    #print(matplotlib.get_backend())

    # Select the backend:
    bs = selector.BackendSelector()
    backend = bs.select()

    # Define basic parameters for the calculation
    n_repeats = 1
    n_index: int = 8
    n_mask: int = int('1' * n_index, 2)  # 2 selects binary -> int conversion
    print('Scale factor = ' + str(n_index))
    # Number of shots for running the circuit on the backend at each stage
    n_shots = 100
    print('#Shots = ' + str(n_shots))
    # Inputs for Scrambler circuit
    print('Mask = ' + bin(n_mask))
    plain: int = 0b10110000101101001011010010010010 & n_mask
    key: int   = 0b01001101000100010001011101001100 & n_mask
    print('Plaintext (binary) = ' + bin(plain))
    print('Encryption key = ' + bin(key))

    # Set up the scrambler
    enc = scrambler.ScramblerBasic()
    cipher = enc.scramble(n_index, plain, key)
    print('Cipher text = ' + bin(cipher))
    assert plain == enc.unscramble(n_index, cipher, key)

    flag_circbox = enc.get_keyscan_circbox(n_index, plain, cipher)
    inv_flag_circbox = enc.get_inverse_keyscan_circbox(n_index, plain, cipher)
    partial_search = partial.Partial()
    grover = groverlong.GroverLong()

    for r in range(0, n_repeats):
        modelled_state = None
        modelled_entropy = float(n_index)
        sum_gl = 0
        for stage in range(1, n_index+1):
            print('\nSTAGE ' + str(stage) + ':')
            # Define the circuit
            x_qubits = list(range(0, n_index))
            y_qubits = list(range(n_index, 2 * n_index))
            circ = qiskit.circuit.QuantumCircuit(2*n_index+1)

            # Add the search circuit
            #partial_search.add_search_circuit(circ, n_index, keyscan_box, inv_keyscan_box)
            #partial_search.add_test_groverlong_circuit(circ, n_index, keyscan_box, inv_keyscan_box)
            rotate_circbox = partial_search.get_rotate_circbox(n_index, modelled_state)
            circ.append(rotate_circbox, x_qubits)

            lamb = partial_search.get_lambda_value(n_index, stage, modelled_entropy)
            print('lamb = ' + str(lamb))
            flag_bits = list(range(stage))
            sum_gl += grover.get_g(lamb)

            grover.add_groverlong_circuit(
                circ,
                n_index,
                lamb,
                flag_bits,
                flag_circbox,
                inv_flag_circbox,
                rotate_circbox,
                rotate_circbox
            )

            # Visualize the circuit
            # circuit.draw(output='mpl') # Uses 'matplotlib' instead of ASCII art
            #print(circ.draw())  # Uses ASCII art

            # Add the measurement gates for a proper run:
            circ.measure_all()

            # Run the circuit on the selected backend:
            job = backend.run(circ, shots=n_shots)
            result = job.result()
            # Works for local simulation
            #counts = result.get_counts(circ)
            # Works with Sampler() primitive (remote IBM backend service)
            #counts = result.quasi_dists[0]
            # Works with everything(!)
            distrib = backend.get_normalized_distrib_from_result(n_index, circ, result)
            #print(distrib)

            modelled_state = partial_search.get_modelled_state(n_index, n_shots, distrib)
            print(modelled_state)
            modelled_entropy = partial_search.get_entropy_from_modelled_state(n_index, modelled_state)
            print('entropy of modelled state = ' + str(modelled_entropy))

            # Analyse the count and check the results
            parsed_count = collections.Counter()
            for bits, probability in distrib.items():
                x_reg = bits & n_mask
                y_reg = bits & (n_mask << n_index)
                y_reg >>= n_index
                reg_tuple = (bin(x_reg), bin(y_reg))
                parsed_count[reg_tuple] = int(probability*n_shots)
            print()  # Blank line
            print(parsed_count.most_common(32))

            # Visualization
            #qiskit.visualization.plot_distribution(counts)
            #matplotlib.pyplot.show()

            # Check that the expected solution is present in the counts
            #expected_solution_key = (bin(key), bin(n_mask))
            #if expected_solution_key in parsed_count:
            #    print('Found solution ' + str(expected_solution_key) +
            #          ' with count = ' + str(parsed_count[expected_solution_key]))

        # Save result stats
        results_dir = pathlib.Path("../results")
        if not results_dir.exists():
            results_dir.mkdir()
        filepath = results_dir / "sampler.csv"
        first_time_opening = False
        if not filepath.exists():
            filepath.touch()
            first_time_opening = True
        with filepath.open("a") as file:
            if first_time_opening:
                file.write('N_INDEX,N_SHOTS,SUM_GL,PROBABILITY\n')
            expected_solution_key = (bin(key), bin(0))
            probability = parsed_count[expected_solution_key] / float(n_shots)
            file.write(str(n_index) + ',' + str(n_shots) + ',' + str(sum_gl) + ',' + str(probability) + '\n')


if __name__ == '__main__':
    # Execute when the module is not initialized from an import statement
    main()
