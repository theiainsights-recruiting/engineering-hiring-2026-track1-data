"""Point-in-time classification join — starter.

Running this file as-is just prints the two inputs, so it doubles as a
check that your environment works. Restructure it however you like.
"""

from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent

classifications = pd.read_csv(HERE / "classifications.csv")
holdings = pd.read_csv(HERE / "holdings.csv")

print(classifications.to_string(index=False))
print()
print(holdings.to_string(index=False))

# TODO: add a micro_theme column to holdings — the classification as it
# stood on each holding's as_of_date. See TASK.md.

# result.to_csv(HERE / "output.csv", index=False)
