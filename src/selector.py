import os
import qiskit
import qiskit_ibm_runtime
import qiskit.result
import qiskit.providers.basic_provider
import collections
from abc import ABC, abstractmethod

class Backend:
    def run(self, circuit, shots=None):
        pass

    def get_normalized_distrib_from_result(
            self,
            n_index: int,
            circuit: qiskit.circuit.QuantumCircuit,
            result
    ) -> qiskit.result.QuasiDistribution:
        pass

class LocalQiskitBackend(Backend):
    device = None
    shots = None
    _backend = None
    def __init__(self, device, shots=None):
        self.device = device
        self.shots = shots
        # BasicAer is obsolete in Qiskit 1.0.x
        #self._backend = qiskit.BasicAer.get_backend(self.device)
        self._backend = qiskit.providers.basic_provider.BasicProvider().get_backend(self.device)

    def run(self, circuit, shots=None):
        if shots is not None:
            self.shots = shots
        # Returns a Qiskit job object - formally 'Any'
        #return qiskit.execute(circuit, self._backend, shots=self.shots)
        new_circuit = qiskit.transpile(circuit, self._backend)
        job = self._backend.run(new_circuit, shots=self.shots)
        return job

    def get_normalized_distrib_from_result(
            self,
            n_index: int,
            circuit: qiskit.circuit.QuantumCircuit,
            result
    ) -> qiskit.result.QuasiDistribution:
        # Works for local Aer simulation
        counts = result.get_counts(circuit)
        # Analyse and convert the count
        parsed_count = dict()
        for bits, count in counts.items():
            mask = 0b1
            q_reg = 0b0
            bits = bits[::-1] # Reverses the string with a slice operation
            for i in range(2*n_index+1):
                if bits[i]=='1':
                    q_reg |= mask
                mask <<= 1
            parsed_count[q_reg] = float(count)/float(self.shots)
        quasi_distrib = qiskit.result.QuasiDistribution(parsed_count, shots=self.shots)
        return quasi_distrib




class IBMCloudBackend(Backend):
    device = None
    shots = None
    _ibm_svc_instance = None
    _ibm_svc_token = None
    _ibm_service = None
    _backend = None
    _primitive = None
    def __init__(self, device, shots=None):
        self.device = device
        self.shots = shots
        assert (('SUSD_IBM_SVC_INSTANCE' in os.environ) and ('SUSD_IBM_SVC_TOKEN' in os.environ)),\
            "No IBM service credentials provided"
        self._ibm_svc_instance = os.environ['SUSD_IBM_SVC_INSTANCE']
        self._ibm_svc_token = os.environ['SUSD_IBM_SVC_TOKEN']
        self._ibm_service = qiskit_ibm_runtime.QiskitRuntimeService(
            channel='ibm_cloud',
            instance=self._ibm_svc_instance,
            token=self._ibm_svc_token
        )

    def run(self, circuit, shots=None):
        session = qiskit_ibm_runtime.Session(self._ibm_service, backend="ibmq_qasm_simulator")
        self._primitive = qiskit_ibm_runtime.Sampler(session=session)
        return self._primitive.run(circuit, shots=shots)

    def get_normalized_distrib_from_result(
            self,
            n_index: int,
            circuit: qiskit.circuit.QuantumCircuit,
            result
    ) -> qiskit.result.QuasiDistribution:
        # Works with Sampler() primitive (remote IBM backend service)
        quasi_distrib = result.quasi_dists[0]
        return quasi_distrib



class BackendSelector:
    _available_backends = ['local_qiskit', 'ibm_cloud']
    selected_backend = 'local_qiskit'
    selected_device = 'basic_simulator'
    shots = 1024

    def select(self):
        # List of available BasicAer backends (simulations)
        # print(qiskit.BasicAer.backends())

        if 'SUSD_BACKEND' in os.environ:
            susd_backend = os.environ['SUSD_BACKEND']
            if susd_backend in self._available_backends:
                self.selected_backend = susd_backend
        if 'SUSD_DEVICE' in os.environ:
            self.selected_device = os.environ['SUSD_DEVICE']

        if self.selected_backend == 'local_qiskit':
            return LocalQiskitBackend(self.selected_device, self.shots)

        if self.selected_backend == 'ibm_cloud':
            # Default to 'ibmq_qasm_simulator' device
            if self.selected_device == 'basic_simulator':
                self.selected_device = 'ibmq_qasm_simulator'
            return IBMCloudBackend(self.selected_device, self.shots)
