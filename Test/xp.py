import time
from tqdm import tqdm

# Wrap the range() function with tqdm()
for i in tqdm(range(100), desc="Processing items"):
    # Simulate some work
    time.sleep(0.01)

print("Loop finished!")