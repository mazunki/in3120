# IN4120 - Posting list compression

The precode for this assignment used Variable Byte Encoding (VBC) for compressing gaps and term frequencies. I initially wanted to implement Elias-Gamma Encoding (EGC) mostly due to its simplicity. Since Python operates mainly at the byte level, I decided to modify the upstream implementation, swapping `bytearray` for `bitarray` to allow more consistent bit-level encoding and decoding between VBC and EGC.

I experimented around combining these two codecs and analyzing how changes in encoding affect storage size, eventually leading to the development of a custom codec, which I’ve named `OneshotCodec`.

# Methods

I started by converting the original VBC implementation from `bytearray` to `bitarray`. To investigate the nature of the data, I logged two files: one for the gaps and one for the term frequencies. Each posting list was appended as a new line. This gave me information about the range of values in the data, with most gaps being either exactly 1, or shooting of into the 5000-10000 range. Term frequencies, on the other hand, were 1 most of the time, and otherwise falling into rather low values.

With these findings in mind, I first implemented a mixed approach: using VBC for gaps and EGC for term frequencies, expecting the change to optimize compression due to the characteristics of the data. To track the effectiveness of the compression techniques, I first attempted to just use the precode statistics, but the output did not change between my algorithms, even when adding 1024 fake bits per posting; I suspect this is due to how Python's stack allocator extends at harmonic interval. To circumvent this issue, I instead measured the bit-length of the posting lists after finalizing the inverted index, which gave me the information I needed to compare my encoding approaches.

# Results
Initially, using only VBC, the total bit-length came out to 2.01M bits. Applying EGC to the term frequencies brought the size down to 1.39M bits. Surprisingly, using only EGC across both gaps (adjusting for off-by-one due to some gaps being zero) and term frequencies further reduced the size to 1.34M bits, which while doing better in some cases, wasn't a consistent improvement.

After running multiple tests, the combination of VBC for gaps and EGC for term frequencies proved more reliable in reducing the overall bit-length, as expected. However, the biggest improvement came when I developed my own codec. This codec optimizes for values that are frequently exactly 1, which is common in our dataset for gaps. It works similarly to VBC but adds a 0-bit prefix for values of 1 before using VBC for larger numbers. Using our custom codec, I reduced the total bit-length from 2.01M to 1.29M bits, a notable improvement, with a final total across all tests of 2.79M bits, compared to 4.30M with the original VBC implementation.

After getting some successful results, I measured the time difference between compressing and not compressing. From this I observe the compression taking roughly double the time than the uncompressed version. The ratio specifically is 0.61 on my machine, which isn't all that bad.

# Discussion

The results show that combining VBC for gaps and EGC for term frequencies provides better compression than using either codec alone. This is consistent with the data, as gaps tend to not be super large nor super low, while term frequencies tend to fall under the magnitude of a few bits. The custom OneshotCodec offers the most significant compression improvement, reducing both gaps and term frequencies more effectively due to its specific handling of frequent 1-values.

The success of OneshotCodec demonstrates the benefit of tailoring your codec to leverage the characteristics of the data being compressed. I'm not sure if using a variably byte encoder under my custom codec is the best choice, so for further improvements this may be worked on.

I'd also like to understand further why Python's stack allocator compression ratio doesn't change as I modify the size of my posting lists. Is there something we can do to get more exact results in this regard?


# File change summary

I have edited a few files from the upstream along with this code:
- `variablebytecodec.py`: includes the VBC, GEC and OC codecs. should really be renamed to `codecs.py`
- `postinglist.py`: to make use of my encodings
- `tests/assginments.py`: to run the tests on the compressed index (adding `d-2` as a target, consequently running `TestCompressedInMemoryPostingList` and `TestInMemoryInvertedIndexWithCompression`)
- `invertedindex.py`: to print information about the compressed posting lists


