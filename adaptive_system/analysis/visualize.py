import json
import matplotlib.pyplot as plt

with open("storage/memory.json") as f:
    data = json.load(f)

failure_rates = [x["metrics"]["failure_rate"] for x in data["history"]]
timestamps = list(range(len(failure_rates)))

plt.figure(figsize=(10, 5))
plt.plot(timestamps, failure_rates, marker="o")
plt.title("System Failure Rate Over Time")
plt.xlabel("Time Step")
plt.ylabel("Failure Rate")
plt.grid(True)
plt.show()
