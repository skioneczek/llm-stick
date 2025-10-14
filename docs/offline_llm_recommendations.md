# Offline LLM Recommendations Optimized for Slower Hardware

The stick must stay fully offline, but it also has to answer quickly on older Windows laptops where CPU-only inference might be the norm. The picks below prioritize **latency and modest memory footprints** while still meeting the two core workloads:

* **A. Strategy sessions:** Sustain multi-turn planning and brainstorming with concise, accurate replies.
* **B. Direct file interaction:** Parse and summarize spreadsheets, Word docs, and PDFs via the stick’s audited helper tools—and, when the safety toggle is enabled, draft edits without hallucinating.

> **Tip:** Prefetch the exact quantized builds (e.g., GGUF Q4_K_M) during stick manufacturing so analysts only copy a single ~5–8 GB file onto the drive instead of large FP16 checkpoints.

## 1. Phi-3 Mini (3.8B) Instruct
* **Why for strategy sessions:** Microsoft optimized Phi-3 Mini for CPU/edge hardware. On a modern laptop CPU it sustains 15–25 tokens/s, keeping back-and-forth ideation snappy even without a GPU. Despite its size it outperforms many 7B models on instruction-following and short-form reasoning tasks.
* **Why for file interaction:** The model’s concise style works well with deterministic doc/xlsx/PDF extractors—ask for targeted summaries or calculations and it stays on topic. When you temporarily enable the write toggle, its grounded outputs help minimize risky edits.
* **Operational notes:** MIT license with commercial usage allowed. Distribute the 4-bit GGUF build (~2.5 GB) for CPU inference and optionally include the 8-bit ONNX build for machines with AVX2/AVX512 acceleration.

## 2. Llama 3.1 8B Instruct
* **Why for strategy sessions:** Llama 3.1 retains strong reasoning for planning conversations while remaining light enough to run at 8–12 tokens/s on an 8-core laptop CPU (20+ tokens/s on consumer GPUs). Long-context support (up to 128k in community builds) lets you feed meeting minutes or prior decisions without aggressive truncation.
* **Why for file interaction:** The thriving ecosystem around Llama models already ships retrieval agents, spreadsheet QA prompts, and JSON-formatted tool calls. With the stick’s helpers you can extract precise cell ranges, verify totals, and gate file edits via the safety toggle.
* **Operational notes:** Licensed for commercial use. Package both Q4_K_M and Q5_1 GGUF variants (~4–6 GB) so operators can trade memory for accuracy depending on the laptop.

## 3. Qwen2.5 7B Instruct
* **Why for strategy sessions:** Qwen2.5 7B offers multilingual support and solid reasoning while still running comfortably on CPU-only boxes (10–15 tokens/s in Q4). Its balanced style keeps strategy sessions moving without verbose detours.
* **Why for file interaction:** Alibaba’s tool-call demos translate cleanly to the stick’s audited helpers. The model handles numeric extraction and table QA better than many peers in the same size band, helping you confirm spreadsheet values before approving any writebacks.
* **Operational notes:** Apache 2.0 license. Ship both the Q4_K_M GGUF (~4.2 GB) and an optional GPU-friendly AWQ build (~7 GB) for analysts who plug the stick into an AI-ready workstation.

## Implementation Checklist
1. **Model packaging:** Store quantized weights under `Data/Models/` with SHA256 manifests so the audit subsystem verifies integrity before load. Keep per-model README files noting the recommended batch size and expected CPU/GPU token rates.
2. **Runtime adapters:** Ensure `core/model_runtime/` auto-detects CPU-only hardware and selects low-thread-count defaults (e.g., 6 threads) to avoid choking older dual-core machines. Surface a CLI switch so operators can lower context length for extra speed.
3. **Safety toggles:** Continue routing all write-capable helpers through the policy engine. Log the toggle state and selected model/quantization before any document change so slower laptops still produce complete audit trails.
4. **Evaluation:** Run the local latency harness on representative hardware (baseline stick laptop, “boss” low-end laptop) and record tokens-per-second alongside reasoning and spreadsheet QA accuracy. Use those numbers to guide which quantization ships as the default.

With these smaller, efficiency-tuned models, analysts get responsive conversations and trustworthy document work even on decade-old laptops—while the stick stays portable, auditable, and completely offline.
