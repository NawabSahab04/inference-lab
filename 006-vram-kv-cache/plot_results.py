import csv
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).parent
with (HERE / "measurements.csv").open() as file:
    rows = list(csv.DictReader(file))

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
for parallel in (1, 4):
    points = [row for row in rows if int(row["parallel"]) == parallel]
    axes[0].plot([int(row["context_tokens"]) for row in points],
                 [int(row["vram_used_mib"]) for row in points], marker="o", label=f"parallel {parallel}")
axes[0].set(xlabel="Configured context tokens", ylabel="Idle VRAM used (MiB)", title="Context and parallelism increase VRAM")
axes[0].ticklabel_format(axis="x", style="plain")
axes[0].grid(alpha=0.3)
axes[0].legend()

with (HERE / "gpu_trace.csv").open() as file:
    trace = list(csv.reader(file))
times = [datetime.strptime(row[0], "%Y/%m/%d %H:%M:%S.%f") for row in trace]
seconds = [(time - times[0]).total_seconds() for time in times]
memory = [int(row[1].split()[0]) for row in trace]
utilization = [int(row[3].split()[0]) for row in trace]
axes[1].plot(seconds, [value - min(memory) for value in memory], label="VRAM growth")
axis = axes[1].twinx()
axis.plot(seconds, utilization, color="tab:orange", alpha=0.6, label="GPU utilization")
axes[1].set(xlabel="Time (seconds)", ylabel="VRAM above 13,132 MiB", title="Generation adds at most 7 MiB")
axis.set_ylabel("GPU utilization (%)")
axes[1].grid(alpha=0.3)
fig.tight_layout()
fig.savefig(HERE / "vram_and_gpu_activity.png", dpi=160)
