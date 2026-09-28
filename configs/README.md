# configs/

**Scaffold for upcoming implementation. No configurations have been finalized yet.**

This directory will hold YAML configuration files so that every experiment is reproducible from a single config. Planned fields:

- **Model name:** e.g., `meta-llama/Llama-3.2-3B-Instruct` for the pilot. Llama-3.1-8B is deferred unless compute allows.
- **Random seed(s).**
- **Paths:** data, model cache, and output/results directories.
- **Probe settings:** which hidden layer(s) to read.
- **Thresholds:** the trajectory-risk and per-turn-risk intervention thresholds (θ_traj, θ_local).
