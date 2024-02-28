import qiskit.circuit

class Scrambler():

    def scramble(self, bit_width: int, plain: int, key: int) -> int:
        pass

    def unscramble(self, bit_width: int, cipher: int, key: int) -> int:
        pass

    def get_keyscan_circbox(self, n_index: int, plain: int, cipher: int) -> qiskit.circuit.Gate:
        pass

    def get_inverse_keyscan_circbox(self, n_index: int, plain: int, cipher: int) -> qiskit.circuit.Gate:
        pass

    def add_keyscan_circuit(
            self,
            c: qiskit.circuit.QuantumCircuit,
            n_index: int,
            plain: int,
            cipher: int,
            withbarriers: bool = True
    ) -> None:
        pass


class ScramblerBasic(Scrambler):

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

class ScramblerWithSwap(Scrambler):

    def __init__(self):
        pass

    def _swap_bits(self, bit_width: int, cipher: int, pos1: int, pos2: int) -> int:
        mask1 = (0b1 << pos1)
        mask2 = (0b1 << pos2)
        bit1 = cipher & mask1
        bit2 = cipher & mask2
        assert pos1 < pos2
        shift = pos2 - pos1
        bit1 <<= shift
        bit2 >>= shift
        cipher = (cipher & ~mask2) | bit1
        cipher = (cipher & ~mask1) | bit2
        return cipher

    def scramble(self, bit_width: int, plain: int, key: int) -> int:
        cipher = plain ^ key
        cipher = self._swap_bits(bit_width, cipher, 0, 4)
        cipher = self._swap_bits(bit_width, cipher, 2, 6)
        return cipher

    def unscramble(self, bit_width: int, cipher: int, key: int) -> int:
        cipher = self._swap_bits(bit_width, cipher, 2, 6)
        cipher = self._swap_bits(bit_width, cipher, 0, 4)
        plain = cipher ^ key
        return plain

    def get_keyscan_circbox(self, n_index: int, plain: int, cipher: int) -> qiskit.circuit.Gate:
        # Create a sub-circuit to span the x and y qubits, but not the ancilla qubit
        subcirc = qiskit.QuantumCircuit(2*n_index, name="Scramble")
        self.add_keyscan_circuit(subcirc, n_index, plain, cipher, withbarriers=False)
        return subcirc.to_gate()

    def get_inverse_keyscan_circbox(self, n_index: int, plain: int, cipher: int) -> qiskit.circuit.Gate:
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
        assert n_index >= 8, "ScramblerWithSwap requires at least n_index = 8"
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
        # Swap bits to mix up the ciphertext
        c.swap(n_index+0, n_index+4)
        c.swap(n_index+2, n_index+6)

        # NOT-XOR the given cipher with the generated cipher to generate flag bits
        mask = 0b1
        for i in y_qubits:
            if ( ~cipher & mask):
                c.x(i)
            mask <<= 1
        if withbarriers: c.barrier(y_qubits)
