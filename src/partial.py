import numpy
import qiskit.circuit
import qiskit.result
import scrambler
import groverlong


class Partial():

    def __init__(self):
        pass

    def get_modelled_state(self, n_index: int, n_shots: int, distrib: qiskit.result.QuasiDistribution) -> list:
        """Returns a modelled state in the form of a list of tuples
        [(cos(beta_1),sin(beta_1)), ..., (cos(beta_n),sin(beta_n))]

        :param n_index: Scaling factor for the circuit
        :param n_shots: Number of shots used to collect the job results
        :param distrib: Instance of a QuasiDistribution that holds the results from the last set of measurements.
        """
        modelled_state = list()
        bit_counts = [0] * n_index
        for bits, probability in distrib.items():
            mask = 0b1
            for i in range(n_index):
                if bits & mask:
                    bit_counts[i] += int(probability*n_shots)
                mask <<= 1

        # Estimator of minimum probability, in case we missed measuring a low-probability bit value
        # See https://en.wikipedia.org/wiki/Binomial_distribution#Estimation_of_parameters
        min_weight = 1.0/(float(n_shots) + 2.0)
        empirical_factor = 0.2
        min_weight *= empirical_factor

        for i in range(n_index):
            weight_for_bit_equals_1 = bit_counts[i]/n_shots
            # Weight should not be exactly equal to 1 or 0
            weight_for_bit_equals_1 = max(weight_for_bit_equals_1, min_weight)
            weight_for_bit_equals_1 = min(weight_for_bit_equals_1, 1.0 - min_weight)
            sin_beta = numpy.sqrt(weight_for_bit_equals_1)
            cos_beta = numpy.sqrt(1.0 - weight_for_bit_equals_1)
            modelled_state.append( (cos_beta, sin_beta) )
        return modelled_state

    def get_entropy_from_modelled_state(self, n_index: int, modelled_state: list) -> float:
        """Returns the Shannon entropy of the modeled state

        :param n_index: Scaling factor for the circuit
        :param modelled_state: A modelled state in the form of a list of tuples
        [(cos(beta_1),sin(beta_1)), ..., (cos(beta_n),sin(beta_n))]
        """
        entropy: float = 0.0
        for i in range(n_index):
            cos_beta, sin_beta = modelled_state[i]
            c2 = cos_beta**2
            s2 = sin_beta**2
            if c2 > 0.0:
                entropy += -c2*numpy.log2(c2)
            if s2 > 0.0:
                entropy += -s2*numpy.log2(s2)
        return entropy

    def get_rotate_circbox(self, n_index: int, modelled_state: list = None) -> qiskit.circuit.Gate:
        """Create the operator gate for the rotation operator that takes $\ket{0}$ to $\ket{\mu}$

        :param n_index: Scaling factor for the circuit
        :param modelled_state: A modelled state in the form of a list of tuples
        [(cos(beta_1),sin(beta_1)), ..., (cos(beta_n),sin(beta_n))]
        """
        rotate_circ = qiskit.circuit.QuantumCircuit(n_index, name="R")
        if (modelled_state is None) or (modelled_state==[]):
            for i in range(n_index):
                rotate_circ.h(i)
        else:
            for i in range(n_index):
                cos_beta, sin_beta = modelled_state[i]
                # beta is in units of radians in qiskit
                beta = numpy.arccos(cos_beta)
                rotate_circ.u(2.0*beta, 0.0, numpy.pi, i)
        return rotate_circ.to_gate()

    def get_lambda_value(self, n_index: int, stage: int, modelled_entropy: float) -> float:
        """Estimate the weight of the target vector (lambda) for this stage"""
        if stage==1:
            return 0.5
        else:
            return 2.0**(float(n_index - stage) - modelled_entropy)
