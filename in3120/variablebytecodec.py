# pylint: disable=missing-module-docstring
# pylint: disable=consider-using-f-string

from typing import Tuple

from bitarray import bitarray


class VariableByteCodec:
    """
    A simple encoder/decoder for variable-byte codes. See Figure 5.8 in
    https://nlp.stanford.edu/IR-book/pdf/05comp.pdf for details.
    """

    @staticmethod
    def encode(number: int, destination: bitarray) -> int:
        """
        Encodes the given number, and appends the resulting bytes to the given
        destination buffer. Returns the number of bits that were appended.
        """
        assert destination is not None
        assert number >= 0

        if number == 0:
            destination.extend([1] + [0]*7)
            return 8

        segments = []
        while number > 0:
            segments.append(number & 0b0111_1111)
            number >>= 7
        segments[0] |= 0b1000_0000

        for seg in reversed(segments):
            for bit in range(7, -1, -1):
                destination.append((seg >> bit) & 1)

        return len(segments) * 8

    @staticmethod
    def decode(source: bitarray, start: int) -> Tuple[int, int]:
        """
        Starting at the given position in the source buffer, decodes the next number.
        Returns a pair comprised of the decoded number, and the number of bits
        read from the source buffer.
        """
        assert source is not None
        assert start >= 0
        # assert start == 0 or source[start - 8] >= 128

        number = 0
        n_bytes = 0
        while True:
            segment = 0
            for i in range(8):
                segment = (segment << 1) | source[start + n_bytes*8 + i]

            number = (number << 7) | (segment & 0b0111_1111)
            n_bytes += 1

            if segment & 0b1000_0000:
                break

        return number, n_bytes*8


class EliasGammaCodec:
    @staticmethod
    def encode(number: int, destination: bitarray) -> int:
        """
        Encodes the given number using Elias-Gamma encoding and appends the resulting
        bits to the given bitarray destination.
        """
        assert number > 0

        n = number.bit_length()
        for i in range(n):
            destination.append(0)

        for i in range(n-1, -1, -1):
            destination.append((number >> i) & 1)

        return 2*n
    
    @staticmethod
    def decode(source: bitarray, start: int) -> Tuple[int, int]:
        """
        Decodes the next Elias-Gamma encoded number starting from position `start` in
        the bitarray source. Returns a tuple of the decoded number and the number of
        bits read.
        """
        assert start < len(source)

        n = 0
        while source[start + n] == 0:
            n += 1

        binary_repr = source[start+n:start+2*n]
        number = int(binary_repr.to01(), 2)

        return (number, 2*n)


