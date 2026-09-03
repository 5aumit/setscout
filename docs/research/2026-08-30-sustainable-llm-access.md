# Sustainable LLM access without a Gemini or OpenAI API key

**Research date:** 2026-08-30
**Source policy:** First-party product, pricing, and documentation pages only. Prices and service
limits can change. Recheck the linked pages before spending money.

## Scope and important distinction

SetScout makes two programmatic LLM calls for each search: a small structured `SearchSpec`
decomposition call and a much larger evidence-grounded report call. At the current defaults, the
report call can contain roughly 40,000 input tokens from dataset-card excerpts. This is an
estimate from the repository's 8-candidate and 20,000-characters-per-candidate defaults, not a
measured token count.

There are two separate needs which should not be confused:

1. A **development assistant** helps write and review SetScout code interactively.
2. A **runtime inference service** is called by `run_pipeline()` when an end user searches for a
   dataset.

A coding-assistant subscription does not provide a supported general API for the runtime service.
For example, OpenAI documents ChatGPT/Codex plan usage separately from API billing and states that
included Codex use is capped, with users able to wait for reset, upgrade, or buy credits.
[OpenAI Codex plan usage](https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan)

## What “without rate limits” can mean

No shared, managed inference API is unlimited. Its operator controls request and token limits to
protect shared capacity. For example, Groq publishes organisation-level RPM, RPD, TPM, and TPD
limits, and Together says its serverless limits are per-organisation, per-model, dynamic, and can
return HTTP 429.
[Groq rate limits](https://console.groq.com/docs/rate-limits)
[Together serverless rate limits](https://docs.together.ai/docs/serverless/rate-limits)

Running an open-weight model on hardware under the project's control removes a *provider request
quota*. It does not make capacity infinite: throughput is bounded by GPU memory, compute,
concurrent requests, and the chosen context length. A rented dedicated GPU similarly avoids a
token-API quota, but the cloud vendor can still have account-spend, stock, or instance-capacity
controls.

## Runtime options

| Route | Billing / current published price | Provider request quota | Operational facts relevant to SetScout |
|---|---|---|---|
| Local machine, open model and Ollama | No per-token charge. Hardware, electricity, and Internet are the direct costs. | No external provider quota once model files are downloaded. | Ollama exposes an OpenAI-compatible `/v1/chat/completions` endpoint. Its official Qwen 3 catalogue lists 32B at 20 GB model size with a 40K context window and Qwen 3 30B at 19 GB with 256K context. Gemma 3 27B is listed at 17 GB with 128K context. Actual usable context also consumes memory. |
| Rented dedicated GPU, self-hosted open model with vLLM | Runpod Pods: RTX A5000 24 GB $0.27/hr, RTX 4090 24 GB $0.74/hr, RTX A6000 48 GB $0.53/hr, A40 48 GB $0.44/hr, L40S 48 GB $0.99/hr, A100 80 GB $1.39/hr. Runpod Serverless: 24 GB $0.69/hr, 48 GB A6000/A40 $1.22/hr, A100 80 GB $2.72/hr, H100 80 GB $4.79/hr. | No LLM API request limit when self-hosted, but the chosen cloud account and GPU stock remain constraints. | vLLM offers an OpenAI-compatible server. A single always-on instance gives predictable ownership of its capacity; serverless can scale down but has cold-start and capacity behaviour to test. |
| Dedicated managed endpoint | Hugging Face documents a $0.50/GPU-hour entry point. It charges while an endpoint is initialising or running, bills by the minute, and requires an active HF subscription and credit card. | No shared token API tier, but endpoint instance quota applies. | HF scale-to-zero can return HTTP 502 while cold starting, and its documentation says there is no built-in request queue. |
| Shared serverless open-model API | Together publishes per-million-token prices, for example Qwen3.5 9B: $0.17 input / $0.25 output; GPT-OSS 20B: $0.05 / $0.20; GPT-OSS 120B: $0.15 / $0.60. HF Inference Providers has $0.10/month free credit for free accounts and $2/month for Pro, with further use paid. | Yes. Limits are part of normal shared-service operation. | Together uses an OpenAI-compatible API and says its serverless service has no provisioning latency. This route does require an API key and payment for continued use. |

Sources for the table: [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility),
[Ollama Qwen 3 catalogue](https://ollama.com/library/qwen3),
[Ollama Gemma 3 catalogue](https://ollama.com/library/gemma3),
[Ollama GPU support](https://docs.ollama.com/gpu), [Runpod pricing](https://www.runpod.io/pricing),
[Runpod Serverless overview](https://docs.runpod.io/serverless/overview),
[vLLM OpenAI-compatible server](https://docs.vllm.ai/en/latest/serving/online_serving/openai_compatible_server/),
[HF Inference Endpoints pricing](https://huggingface.co/docs/inference-endpoints/pricing),
[HF autoscaling](https://huggingface.co/docs/inference-endpoints/autoscaling),
[HF endpoint access and quotas](https://huggingface.co/docs/inference-endpoints/guides/access),
[Together model catalogue](https://docs.together.ai/docs/serverless/models),
[Together serverless overview](https://docs.together.ai/docs/serverless/overview), and
[Hugging Face Inference Providers pricing](https://huggingface.co/docs/inference-providers/pricing).

## Open models and licences

Two official, self-hostable model families with suitable published serving paths are:

- **Qwen3 32B:** the publisher's model page shows `vllm serve "Qwen/Qwen3-32B"` and a call to
  the resulting OpenAI-compatible `/v1/chat/completions` endpoint.
  [Qwen3 32B model page](https://huggingface.co/Qwen/Qwen3-32B)
- **OpenAI gpt-oss:** OpenAI says the gpt-oss weights are free under Apache 2.0 and can run on
  infrastructure under the user's control. Its documentation describes gpt-oss-120b as fitting in
  one H100 GPU and gpt-oss-20b as the lower-hardware model. OpenAI also documents structured
  outputs, tool use, and reasoning controls for the family.
  [gpt-oss availability and licence](https://help.openai.com/en/articles/11870455)
  [gpt-oss announcement](https://openai.com/index/introducing-gpt-oss/)
  [gpt-oss-120b model documentation](https://developers.openai.com/api/docs/models/gpt-oss-120b)

Published model size is not a safe capacity calculation by itself. A running service also needs
memory for model execution and its key-value cache, which grows with context length and concurrent
requests. SetScout's present evaluator prompt is therefore a workload that must be measured on the
actual model, quantisation, GPU, and concurrency setting before use.

## Integration impact in this repository

Today `setscout/graph/nodes/llm.py` creates `ChatGoogleGenerativeAI`, while `pipeline.py` rejects
requests without `GEMINI_API_KEY`. The graph already injects its LLMs into nodes, so a provider
change is confined mainly to the model factory and configuration validation, but it is not merely
an environment-variable change.

For Ollama, vLLM, Together, and Groq, an OpenAI-compatible endpoint can be used through
`langchain-openai`'s `ChatOpenAI` with a configured `base_url`. LangChain documents both the
`langchain-openai` package and `base_url` for a proxy or service emulator. Ollama documents that
the client API key is required by the OpenAI client but ignored locally. Each candidate must still
be tested for Pydantic structured-output reliability with the exact `SearchSpec` and
`PipelineResult` schemas.

Sources: [LangChain ChatOpenAI](https://docs.langchain.com/oss/python/integrations/chat/openai),
[Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility),
[Together OpenAI compatibility](https://docs.together.ai/docs/inference/openai-compatibility), and
[Groq OpenAI compatibility](https://console.groq.com/docs/openai).

## Cost equations and capacity checks

Use measured request token counts rather than an assumed price per query.

```text
shared API request cost = input_tokens * input_price_per_million / 1,000,000
                        + output_tokens * output_price_per_million / 1,000,000

dedicated GPU monthly cost = hourly_rate * hours_kept_running
```

For a constant 30-day service, `hours_kept_running` is 720. At the current listed Runpod Pod
prices, this is $194.40/month for a 24 GB RTX A5000, $316.80/month for a 48 GB RTX A6000, and
$1,000.80/month for an 80 GB A100, before storage and network charges. These are arithmetic
examples, not a forecast of available capacity or total cost.

The relevant acceptance checks before choosing any runtime route are:

1. Run the existing two calls on a fixed, saved set of realistic searches and cards.
2. Measure Pydantic-valid structured responses, candidate coverage, evidence grounding, latency,
   memory use, and concurrent-query behaviour.
3. For owned or dedicated capacity, apply an explicit queue and concurrency limit so a burst does
   not exhaust GPU memory.
4. For a shared API, test retry behaviour for HTTP 429 and set a spend cap.
5. Keep a deterministic fallback report, as the current pipeline already does for LLM failure.

This report lists facts and trade-offs only. It does not select a model, provider, or subscription.
