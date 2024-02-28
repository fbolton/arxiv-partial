import qiskit.circuit
import numpy
import math

class GroverLong():

    def __init__(self):
        pass

    def get_g(self, lamb: float) -> int:
        """Returns the number of Grover-Long iterations required for the given lambda
        (based on the formula for $j_op$ in the paper by G. L. Long https://arxiv.org/abs/quant-ph/0106071)
        """
        assert lamb > 0.0, "lambda parameter in Grover-Long must be non-zero"
        # Changed this condition to 'lamb <= 0.6' to allow for small numerical inaccuracies
        assert lamb <= 0.6, "lambda parameter in Grover-Long must be less than or equal to 1/2"
        gl = math.ceil((numpy.pi/(4.0*numpy.arcsin(numpy.sqrt(lamb)))) - 0.5)
        return gl

    def get_alpha(self, lamb: float, g: int) -> float:
        """Returns the phase angle, alpha, (in units of radians) for the Grover-Long operators
        (based on the formula for $\phi$ in the paper by G. L. Long https://arxiv.org/abs/quant-ph/0106071)"""
        assert lamb > 0.0, "lambda parameter in Grover-Long must be non-zero"
        # Changed this condition to 'lamb <= 0.6' to allow for small numerical inaccuracies
        assert lamb <= 0.6, "lambda parameter in Grover-Long must be less than or equal to 1/2"
        assert g >= 1, "iteration count in Grover-Long must be >= 1"
        t = numpy.sin(numpy.pi/(4.0*float(g)+2.0))
        alpha = 2.0*numpy.arcsin(t/numpy.sqrt(lamb))
        return alpha  # Result is returned in units of radians (standard in Qiskit library)

    def get_oracle_kickback_circbox(self, n_index: int, flag_bits: list, phase: float) -> qiskit.circuit.Gate:
        """Returns a quantum gate for the phase oracle, using the specified partial oracle flag bits
        and the specified phase.

        :param n_index: Scaling factor for the circuit
        :param flag_bits: Specifies the list of flag bits (partial oracle bits) that are tested for this oracle.
            The bit indices must lie in the range `0..n_index-1`
        :param phase: The phase kickback from this oracle, specified in multiples of pi.
        :returns: A quantum gate whose `0..n_index-1` indices map to the oracle flag bits
            and `n_index` index maps to the ancilla bit
        """

        # Create the circuit for n_index flag bits + 1 ancilla bit
        circ = qiskit.circuit.QuantumCircuit(n_index+1, name="Kick")
        ancilla = n_index
        circ.mcx(flag_bits, ancilla)
        circ.u(0.0, 0.0, phase, ancilla)
        circ.mcx(flag_bits, ancilla)
        return circ.to_gate()

    def add_groverlong_circuit(
            self,
            c: qiskit.circuit.QuantumCircuit,
            n_index: int,
            lamb: float,
            flag_bits: list,
            flag_circbox: qiskit.circuit.Gate,
            inv_flag_circbox: qiskit.circuit.Gate,
            rotate_circbox: qiskit.circuit.Gate,
            inv_rotate_circbox: qiskit.circuit.Gate,
            withbarriers: bool = True
    ) -> None:
        """Adds gates for the Grover-Long algorithm, using the given parameters.

        :param c: Circuit to which the gates are added
        :param n_index: Scaling factor for the circuit
        :param lamb: Weighting factor (amplitude squared) of the target vector
        :param flag_bits: Specifies the list of flag bits (partial oracle bits) that are tested for this oracle.
            The bit indices must lie in the range `0..n_index-1`
        :param rotate_circbox: Operator gate that rotates from $\ket{0}$ to $\ket{\mu}$
        :param inv_rotate_circbox: Operator gate that rotates from $\ket{\mu}$ to $\ket{0}$
        :param withbarriers: Boolean flag indicating whether to add barriers to the circuit
        """
        gl = self.get_g(lamb)
        phase = self.get_alpha(lamb, gl)
        print('\ng_l = ' + str(gl))
        print('phase = ' + str(phase/numpy.pi)) # Print phase in units of pi

        # Create the oracle operator
        subcirc = qiskit.circuit.QuantumCircuit(2*n_index+1, name="Oracle")
        subcirc.append(flag_circbox, range(0, 2*n_index))
        kickback_circbox = self.get_oracle_kickback_circbox(n_index, flag_bits, phase)
        subcirc.append(kickback_circbox, range(n_index, 2*n_index+1))
        subcirc.append(inv_flag_circbox, range(0, 2*n_index))
        oracle_circbox = subcirc.to_gate()

        for i in range(0, gl):
            self.add_grover_iteration(c, n_index, phase, oracle_circbox, rotate_circbox, inv_rotate_circbox)

    def add_grover_iteration(
            self,
            c: qiskit.circuit.QuantumCircuit,
            n_index: int,
            phase: float,
            oracle_circbox: qiskit.circuit.Gate,
            rotate_circbox: qiskit.circuit.Gate,
            inv_rotate_circbox: qiskit.circuit.Gate,
            withbarriers: bool = True
    ) -> None:
        """Adds gates for a *single* iteration of the Grover-Long algorithm.

        :param c: Circuit to which the gates are added
        :param n_index: Scaling factor for the circuit
        :param phase: Phase factor that is used to mark the target states
        :param oracle_circbox: Operator gate that encapsulates the oracle and the steps for marking
            target states with a complex phase factor
        :param rotate_circbox: Operator gate that rotates from $\ket{0}$ to $\ket{\mu}$
        :param inv_rotate_circbox: Operator gate that rotates from $\ket{\mu}$ to $\ket{0}$
        :param withbarriers: Boolean flag indicating whether to add barriers to the circuit
        """
        x_qubits = list(range(0, n_index))
        y_qubits = list(range(n_index, 2*n_index))
        ancilla = 2*n_index
        all_qubits = list(range(0, 2*n_index+1))

        # Add the phase kickback from the oracle
        if withbarriers: c.barrier(all_qubits)
        c.append(oracle_circbox, all_qubits)

        # Add the Grover-Long diffusion operator to the circuit
        if withbarriers: c.barrier(all_qubits)
        c.append(inv_rotate_circbox, x_qubits)
        for i in x_qubits:
            c.x(i)
        c.mcx(x_qubits, ancilla)
        c.u(0.0, 0.0, phase, ancilla)
        c.mcx(x_qubits, ancilla)
        for i in x_qubits:
            c.x(i)
        c.append(rotate_circbox, x_qubits)
