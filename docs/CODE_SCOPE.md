# Source code scope

The candidate contains18 byte-for-byte core modules from the completed engineering project. Their original docstrings and identity fields remain unchanged, including historical DEMO/DIAGNOSTIC markers and OpenFly-compatible action terminology. Those identifiers do not imply OpenFly inference in the reported T-track experiments.

- `actions`, `camera`, `scene`, `scene_navigation`, `records`, `png`: action/pose/camera/data utilities.
- `trace_online`, `trace_replay`: frozen TRACE timing and controller seams.
- `judger_online`, `lance_judger`, `nova_judger`, `nova_evaluation_v2`: identity-bound HTTP client implementations; Nova v1 is a historical schema helper, v2 is the formal evaluation client.
- `judger_prefix_answer_v1`, `lance_prefix_v3`, `common_test_judgers_v1`: shared interpretation of completed responses, preserving raw errors.
- `judger_input`, `pilot_visibility`: image request and evaluation-truth utilities.

All imports within the selected `sfb` module closure are included. Some operations require NumPy or Pillow. `analysis/summarize_results.py` is independent and needs only the standard library.

This export intentionally excludes workstation-bound campaign/recovery launchers, private run outputs and Isaac scripts whose scene/asset dependencies are not yet distributable. It supports public inspection of the implemented core and offline aggregation. It is not a turnkey reproduction of the original full workspace. [Reproduction prerequisites](REPRODUCIBILITY.md).

For development of the core, after reviewing the pending license decision:

```bash
python -m venv .venv
# Activate this environment with your operating system's normal command.
python -m pip install -e ".[images,terrain]"
```

Do not install Isaac into this environment. No network inference is launched by the quick-start aggregation command. No credentials or live service access are provided.
