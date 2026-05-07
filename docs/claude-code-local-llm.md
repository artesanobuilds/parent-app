# Running Claude Code with a Local LLM

## Recommended Model

**Qwen3.5 35B A3B Q8_0** (~37.8 GB)

- Mixture-of-experts: 35B total params, only 3B active at a time = fast inference
- 256K context window support
- Strong tool-calling and agentic coding capabilities
- Q8 quantization = near-lossless quality

### Why this model?

On an M4 Max with 128GB unified memory, this model runs at 50-60+ tok/s via MLX, leaves ~90GB for context and system overhead, and has the best tool-calling support for Claude Code's agentic workflow.

### Alternatives

| Model | RAM Usage | Notes |
|-------|-----------|-------|
| GLM-4.7 (full) | ~50GB | Strongest agentic coding benchmark scores |
| Llama 3.3 70B Q6 | ~55GB | Largest general-purpose option that fits comfortably |
| Qwen3-Coder 30B Q8 | ~32GB | Purpose-built for agentic coding |
| DeepSeek-V3 Q4 | ~100GB | Near-frontier reasoning, needs 128GB machine |

## Setup

### 1. Install & Load Model in LM Studio

- Download **LM Studio** (v0.4.1+ required for Anthropic-compatible endpoint)
- Download `Qwen3.5 35B A3B Q8_0` (GGUF format, ~37.8 GB)
- Load the model in LM Studio

### 2. Configure Context Length

**Critical:** Set `n_ctx` (context length) to at least **65536** (64K) or higher.

Claude Code's system prompt alone is ~58K tokens. The default 4096 will fail with:
```
Cannot truncate prompt with n_keep (58765) >= n_ctx (4096)
```

With 128GB RAM, you can safely set it to **131072** (128K).

### 3. Start LM Studio Server

- Go to the Server tab in LM Studio
- Start the server on **port 1234** (default)
- Verify it's running: `curl http://localhost:1234/v1/models`

### 4. Set Environment Variables

```bash
export ANTHROPIC_BASE_URL=http://localhost:1234
export ANTHROPIC_AUTH_TOKEN=lmstudio
```

Add these to your `~/.zshrc` or `~/.bashrc` to persist across sessions.

### 5. Run Claude Code

```bash
claude --model qwen3.5-35b-a3b
```

The `--model` value must match the model ID shown by LM Studio. Verify with:
```bash
curl http://localhost:1234/v1/models
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `n_keep >= n_ctx` error | Increase context length in LM Studio to 64K+ |
| Slow inference | Use MLX backend in LM Studio (20-30% faster than llama.cpp on Apple Silicon) |
| Model not found | Check exact model ID with `curl http://localhost:1234/v1/models` |
| Connection refused | Make sure LM Studio server is running on the correct port |

## Hardware Reference

- **Machine:** Apple M4 Max, 128GB unified memory, 40 GPU cores
- **RAM budget:** Model (~38GB) + context + overhead = ~50-60GB used, ~70GB free
- **Expected speed:** 50-60+ tokens/second with Qwen3.5 35B A3B Q8

## Sources

- [How to Run Local LLMs with Claude Code - Unsloth](https://unsloth.ai/docs/basics/claude-code)
- [Use LM Studio Models in Claude Code](https://lmstudio.ai/blog/claudecode)
- [Best Local LLMs for Mac in 2026](https://insiderllm.com/guides/best-local-llms-mac-2026/)
- [Best Local LLMs on Apple Silicon](https://apxml.com/posts/best-local-llm-apple-silicon-mac)
