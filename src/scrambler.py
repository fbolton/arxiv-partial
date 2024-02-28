import qiskit.circuit

class Scrambler():

    def __init__(self):
        pass

    def scramble(self, bit_width: int, plain: int, key: int) -> int:
        """Scramble the given plaintext with the specified key, returning the ciphertext"""
        # Encryption performed simply as XOR of plaintext and key
        return plain ^ key

    def unscramble(self, bit_width: int, cipher: int, key: int) -> int:
        """Unscramble the given ciphertext with the specified key, returning the plaintext"""
        # Decryption performed simply as XOR of cipher and key
        return cipher ^ key

    def get_keyscan_circbox(self, n_index: int, plain: int, cipher: int) -> qiskit.circuit.Gate:
        """Encapsulates the keyscan circuit in a single gate"""
        # Create a sub-circuit to span the x and y qubits, but not the ancilla qubit
        subcirc = qiskit.QuantumCircuit(2*n_index, name="Scramble")
        self.add_keyscan_circuit(subcirc, n_index, plain, cipher, withbarriers=False)
        return subcirc.to_gate()

    def get_inverse_keyscan_circbox(self, n_index: int, plain: int, cipher: int) -> qiskit.circuit.Gate:
        """Encapsulates the inverse (hermitian adjoint) keyscan circuit in a single gate"""
        # Create a sub-circuit to span the x and y qubits, but not the ancilla qubit
        subcirc = qiskit.QuantumCircuit(2*n_index, name="Scramble")
        self.add_keyscan_circuit(subcirc, n_index, plain, cipher, withbarriers=False)
        invcirc = subcirc.inverse()
        invcirc.name = "InvScramble"
        return invcirc.to_gate()

    def add_keyscan_circuit(
            self,
            c: qiskit.circuit.QuantumCircuit,
            n_index: int,
            plain: int,
            cipher: int,
            withbarriers: bool = True
    ) -> None:
        """Add the Scrambler operator to the specified circuit. The Scrambler operator applies
        the key register (presumed to be in an equal superposition of states) to the plaintext,
        and compares the resulting ciphertext with the (specified) target cipher text.
        If there is a match between the resulting ciphertext and the target cipher text,
        the flag qubits are all equal to 1."""
        mask = 0b1
        x_qubits = list(range(0, n_index))
        y_qubits = list(range(n_index, 2*n_index))

        # Set up the plaintext bits on q[n_index]...q[2*n_index-1] using X gates
        for i in y_qubits:
            if (plain & mask):
                c.x(i)
            mask <<= 1
        if withbarriers: c.barrier(y_qubits)

        # XOR the key with the plaintext to generate the ciphertext
        for i in x_qubits:
            c.cx(i, i+n_index)
        if withbarriers: c.barrier(y_qubits)

        # NOT-XOR the given cipher with the generated cipher to generate flag bits
        mask = 0b1
        for i in y_qubits:
            if ( ~cipher & mask):
                c.x(i)
            mask <<= 1
        if withbarriers: c.barrier(y_qubits)
