import pyreadr
import pandas as pd

# Load the smallest file first — fault-free training data
result = pyreadr.read_r('../data/TEP_FaultFree_Training.rdata')

# pyreadr returns a dict — let's see what's inside
print(type(result))
print(result.keys())
