# LLM Runtime — Placeholder Wiring

All inference remains offline. The launcher and services expect CPU-only `llama.cpp` binaries and GGUF models to be staged manually.

## Directory Layout
```
App/
  bin/
    llama/
      llama-windows-x64.exe
      llama-macos-arm64
      llama-linux-x64
  models/
    llm/
      main.gguf
      instruct.gguf
```

Use architecture-specific names so wrappers can select the correct binary without probing the network. Add additional builds (AVX2, AVX512, Metal) using the same folder with suffixes, e.g. `llama-macos-arm64-metal`.

## Invocation Contract
- Launchers call `core.llm.invoke.run(prompt, model_path, binary_path)` (to be implemented) and pass explicit paths — no implicit downloads.
- All stdout/stderr is captured into `Data/logs/llm.log` for auditing.
- Temporary prompts are written to `Data/tmp/` (created by `net_guard.enable_temp_sandbox`).

## TODO (Day 2)
- Wrap llama.cpp binary in a Python helper (`core/llm/invoke.py`).
- Support batching for prompt + system message; stay within CPU-only envelope.
- Provide failover message when binaries/models missing: “LLM binary not found. Drop files under `App/bin/llama/` and retry.”
