#!/usr/bin/env python
import re
import matplotlib.pyplot as plt
from collections import Counter

# Paths to your files
gaps_file_path = 'posting_list_gaps.txt'  # Update this to your actual file path
frequencies_file_path = 'posting_list_term_frequencies.txt'  # Update this to your actual file path

# Function to extract numbers from a file
def extract_numbers(file_path):
    with open(file_path, 'r') as file:
        file_content = file.read()
    return list(map(int, re.findall(r'\d+', file_content)))

# Extract numbers from both files
gaps_numbers = extract_numbers(gaps_file_path)
frequencies_numbers = extract_numbers(frequencies_file_path)

# Count the occurrences of each number
gaps_counts = Counter(gaps_numbers)
frequencies_counts = Counter(frequencies_numbers)

# Sort the counts by the unique number (key)
gaps_sorted = sorted(gaps_counts.items())
frequencies_sorted = sorted(frequencies_counts.items())

gaps_keys, gaps_values = zip(*gaps_sorted)
frequencies_keys, frequencies_values = zip(*frequencies_sorted)

# Create subplots (2 rows, 1 column)
fig, axs = plt.subplots(2, 1, figsize=(10, 10))

# Plot the frequency of gaps in the first subplot
axs[0].bar(gaps_keys, gaps_values, label='Posting List Gaps', color='blue')
axs[0].set_title('Frequency of Posting List Gaps')
axs[0].set_xlabel('Number')
axs[0].set_ylabel('Count')
# axs[0].set_yscale('log')  # Apply logarithmic scale for better visibility
axs[0].grid(True)
axs[0].legend()

# Plot the frequency of term frequencies in the second subplot
axs[1].bar(frequencies_keys, frequencies_values, label='Term Frequencies', color='orange')
axs[1].set_title('Frequency of Term Frequencies')
axs[1].set_xlabel('Number')
axs[1].set_ylabel('Count')
# axs[1].set_yscale('log')  # Apply logarithmic scale for better visibility
axs[1].grid(True)
axs[1].legend()

# Adjust layout to prevent overlapping
plt.tight_layout()

# Show both plots in the same window
plt.show()
