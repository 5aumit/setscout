# LLM provider comparison for SetScout's two model calls

**Date:** 2026-07-22

**Scope:** Query decomposition and evidence-grounded candidate evaluation

**Source policy:** Provider documentation and official LangChain documentation/source only

## Executive recommendation

1. **Query decomposition:** replace the hosted `gemma-4-31b-it` default with
   **`gemini-3.5-flash-lite` at minimal thinking**, after removing the globally supplied
   `temperature` parameter and explicitly selecting native JSON-schema output. It is a GA model,
   has a 1,048,576-token input limit, supports structured output, and Google positions it for
   high-volume parsing and structured JSON. Keep `gpt-5-nano` as the low-cost cross-provider
   challenger in the evaluation harness.
2. **Evidence-grounded evaluation:** use **`gemini-3.5-flash-lite` as the new baseline**, but do
   not declare it the quality winner from provider documentation. Benchmark it against
   **`gpt-5.6-luna`** and **Claude Haiku 4.5** on SetScout's labeled queries, measuring grounding
   and semantic correctness, not just schema validity. Promote a challenger only if the report
   rubric or ranking metrics improve enough to justify its materially higher input price.
3. **Until that harness result exists:** keeping `gemini-2.5-flash-lite` for evaluation is the
   lowest-risk production choice. It already fits the workload, is the cheapest evaluated hosted
   baseline already wired into SetScout, and avoids a provider abstraction change.

These are recommendations, not measured conclusions. No provider publishes an apples-to-apples
benchmark for SetScout's prompts, nested Pydantic schemas, dataset-card evidence, or end-to-end
latency. Provider claims below are labeled as published facts; workload judgments are labeled as
inferences.

## What SetScout actually asks the models to do

### Call 1: decomposition

`setscout/graph/nodes/decomposer.py` sends five short form fields and asks for a `SearchSpec`:

- `expanded_keywords: list[str]`
- `mesh_terms: list[str]`
- `prioritized_sources: list[str]`
- nested `hard_constraints` with optional `min_samples` and `access`

This is a small extraction/classification task. Failures are contained by a deterministic fallback,
so latency, schema adherence, and operational simplicity matter more than frontier reasoning.

The current default is `gemma-4-31b-it`. Google documents Gemma 4 31B as an open-weight,
instruction-tuned model with a 256K context window and native function calling, and the Gemini API
offers hosted access to that model. However, Google's Gemma function-calling guide requires parsing
model-emitted tool-call syntax and validating results; it does not make the same constrained JSON
schema guarantee as Gemini native structured output. [Gemma 4 model card][gemma-4-card]
[Gemma hosted API][gemma-api] [Gemma function calling][gemma-tools]

### Call 2: evidence-grounded evaluation

`setscout/graph/nodes/evaluator.py` sends every candidate, the first evidence document for each,
and requests a nested `PipelineResult`: an array of ranked `CandidateEvaluation` objects, each with
requirement checks and issue findings, plus a Markdown report.

At defaults, `setscout/graph/nodes/searcher.py` caps the list at 8 candidates and
`setscout/graph/nodes/gather_evidence.py` includes up to 20,000 characters from each dataset card.
The evidence payload can therefore reach **160,000 characters**, before query text, headings,
schema/tool instructions, and output. Google's approximation of one Gemini token per four
characters makes that roughly **40,000 input tokens** for the card excerpts alone. Tokenization
varies, so the production system should count actual prompt tokens rather than rely on this
estimate. [Google token counting][gemini-tokens]

**Inference:** all compared models have ample nominal capacity for the default evaluator prompt.
The practical differentiators are whether the model finds and uses evidence distributed across the
prompt, follows semantic constraints such as “do not guess,” and emits a complete result for every
candidate. Context-window size by itself does not establish those abilities.

## Published capability and price comparison

Prices are standard synchronous API list prices in USD per one million tokens on 2026-07-22.
They exclude batch/flex/priority tiers, cache storage, and any cloud-marketplace premium.

| Model | Best SetScout role | Native constrained structured output | Input / max output | Input / output price | Provider's latency positioning |
|---|---|---|---:|---:|---|
| Gemini 2.5 Flash-Lite (current evaluator) | Low-cost baseline | Yes; subset of JSON Schema | 1,048,576 / 65,536 | $0.10 / $0.40 | Google's fastest and most budget-friendly 2.5 model |
| Gemini 3.5 Flash-Lite (GA) | Recommended baseline for both calls | Yes; subset of JSON Schema | 1,048,576 / 65,536 | $0.30 / $2.50 | Low latency; highest throughput in the 3.5 family |
| OpenAI GPT-5 nano | Decomposer challenger | Yes; native Structured Outputs | 400,000 / 128,000 | $0.05 / $0.40 | OpenAI's fastest, cheapest GPT-5 variant |
| OpenAI GPT-5.6 Luna | Evaluator quality challenger | Yes; native Structured Outputs | 1,050,000 / 128,000 | $1.00 / $6.00 | Cost-sensitive, high-volume member of the current 5.6 family |
| Claude Haiku 4.5 | Fast evaluator challenger | Yes; grammar-constrained JSON schema | 200,000 / 64,000 | $1.00 / $5.00 | Anthropic's fastest current Claude model |

Sources: [Gemini 2.5 Flash-Lite model][gemini-25-model],
[Gemini 3.5 Flash-Lite model][gemini-35-model], [Gemini API pricing][gemini-pricing],
[GPT-5 nano][gpt-5-nano], [OpenAI current models][openai-models],
[Claude model comparison][claude-models], and [Claude pricing][claude-pricing].

The labels “fast,” “fastest,” “low latency,” and “highest throughput” are the providers' own
within-family descriptions. They are not cross-provider measurements and should not be treated as
an end-to-end SetScout latency ranking.

### Illustrative evaluator cost

For a common comparison point—not a measured SetScout trace—assume 40,000 input tokens and 2,000
output tokens:

| Model | Approximate cost per evaluator call |
|---|---:|
| Gemini 2.5 Flash-Lite | $0.0048 |
| Gemini 3.5 Flash-Lite | $0.0170 |
| GPT-5 nano | $0.0028, but it is not the recommended evaluator-quality challenger |
| GPT-5.6 Luna | $0.0520 |
| Claude Haiku 4.5 | $0.0500 |

Calculation: `40,000 × input_rate / 1M + 2,000 × output_rate / 1M`. Real cost must use response
usage because reasoning tokens, schema overhead, the actual tokenizer, and report length differ.
For the tiny decomposer prompt, all of these token costs are negligible relative to request
latency and engineering complexity.

## Structured-output reliability

### What the providers guarantee

- **Gemini:** native structured output constrains output to a supported subset of JSON Schema.
  Google explicitly says syntactically correct JSON does not guarantee semantically correct values
  and tells applications to validate the result and retain error handling. Gemini 2.5 Flash-Lite
  and 3.5 Flash-Lite both list structured output as supported.
  [Gemini structured output][gemini-structured]
- **OpenAI:** native Structured Outputs guarantees conformance to the supplied schema on supported
  models. LangChain exposes it through `with_structured_output(..., method="json_schema")`; without
  that explicit method, `ChatOpenAI` defaults to function calling. Refusals or token exhaustion
  still need application handling. [LangChain ChatOpenAI][lc-openai]
- **Anthropic:** structured outputs compile JSON Schema into a grammar and guarantee schema-valid
  JSON for supported models, including Haiku 4.5. Anthropic documents exceptions for safety
  refusals and `max_tokens` truncation, either of which can produce output that does not match the
  schema. [Claude structured outputs][claude-structured]

### What those guarantees do not establish

Schema validity does not prove that:

- every input candidate appears exactly once;
- ranks are unique and contiguous;
- a requirement check is supported by the supplied card;
- an `IssueFinding.source_url` corresponds to the cited evidence;
- `report_markdown` agrees with the structured evaluations; or
- the model noticed evidence in the middle or end of a long batch prompt.

**Inference:** SetScout should treat native constrained decoding as necessary but not sufficient.
Pydantic validation catches structural failures, while custom post-validation and the report rubric
must catch semantic failures. The current `PipelineResult` schema does not encode list length,
unique ranks, candidate-ID membership, or report/evaluation agreement.

### Specific current risk: Gemma for decomposition

SetScout calls `llm.with_structured_output(SearchSpec)` without choosing a method. Modern
`langchain-google-genai` defaults that method to Gemini native JSON schema, while older versions
used function calling. The project does not pin dependency versions. Google documents Gemma 4
function calling, but the Gemini structured-output model-support list is for Gemini models and does
not list Gemma 4. **Inference:** the present `gemma-4-31b-it` path should be tested explicitly; it
should not be assumed to receive Gemini's native constrained-output guarantee merely because it is
served by the Gemini API. [LangChain Google integration][lc-google]
[LangChain Google 4.0 change][lc-google-4]

## Long-context evidence handling

### Capacity

- Gemini 2.5 and 3.5 Flash-Lite accept 1,048,576 input tokens.
- GPT-5 nano accepts 400,000; GPT-5.6 Luna accepts 1,050,000.
- Claude Haiku 4.5 accepts 200,000.

All comfortably exceed the approximately 40K excerpt-token default. Haiku's margin is the
smallest but still substantial. [Gemini 2.5 model][gemini-25-model]
[Gemini 3.5 model][gemini-35-model] [GPT-5 nano][gpt-5-nano]
[OpenAI current models][openai-models] [Claude models][claude-models]

### Evidence use

Google describes Gemini 3.5 Flash-Lite as improved for document understanding, data parsing, and
structured extraction. This is directionally aligned with SetScout, but Google's published
benchmarks are not SetScout grounding tests. Anthropic itself advises benchmarking actual prompts
and data when selecting a model. [Gemini latest-model guide][gemini-latest]
[Claude model selection][claude-selection]

**Inference:** the evaluator's head-only truncation and one-document-per-candidate design likely
limit grounding more than nominal model context. A larger context window cannot recover evidence
that `format_batch_excerpt()` omitted. Provider evaluation should therefore hold retrieval and
prompt construction constant.

## Latency

No primary source provides comparable time-to-first-token or completion-latency measurements for
these exact models on a 40K-token SetScout prompt. The providers only publish qualitative tiers,
and OpenAI publishes numerical latency SLAs only for separately priced Priority Processing—not
ordinary standard traffic. [OpenAI Priority Processing][openai-priority]

Measure at least:

- p50 and p95 end-to-end latency for each call separately;
- time to first token, if/when SetScout streams;
- output tokens per second;
- retry/fallback rate and rate-limit time;
- latency as candidate count and excerpt characters grow; and
- cold-schema versus warm-schema latency, because Anthropic compiles and caches structured-output
  grammars and warns that complex schemas take longer to compile.

For decomposition, run with minimal/no reasoning. For evaluation, compare minimal versus a bounded
reasoning setting where supported; reasoning output is billed and increases latency.

## Python and LangChain integration

### Gemini

SetScout already depends on `langchain-google-genai` and constructs
`ChatGoogleGenerativeAI`, so Gemini preserves the smallest change surface. LangChain supports
Pydantic schemas and recommends `method="json_schema"` because it constrains generation directly.
[LangChain Google integration][lc-google]

There is one required migration change for `gemini-3.5-flash-lite`: Google says to remove
`temperature`, `top_p`, and `top_k`. SetScout currently always supplies `temperature=0.2` in
`make_llm`, so changing only the model environment variable is not sufficient. Google recommends
minimal thinking for extraction, routing, and classification. [Gemini latest-model guide][gemini-latest]

### OpenAI

Use `ChatOpenAI` from the separately installed `langchain-openai` package and specify
`method="json_schema"`. SetScout would need a provider-neutral model factory and separate API-key
configuration; the node-level dependency injection already makes that refactor localized.
[LangChain ChatOpenAI][lc-openai]

### Anthropic

Use `ChatAnthropic` from `langchain-anthropic>=1.1.0` and specify
`method="json_schema"` for Anthropic's native structured output. It is not currently a dependency.
The same provider-neutral factory and credential changes apply. [LangChain ChatAnthropic][lc-anthropic]

**Inference:** LangChain integration is viable for all three providers. Gemini wins on migration
cost because it is already wired; the alternatives do not offer a unique integration capability
that alone justifies switching.

## Recommendation by call

### 1. Query decomposition

**Choose `gemini-3.5-flash-lite`, minimal thinking, native JSON schema.**

Why:

- the task matches Google's stated high-volume parsing/structured-JSON use case;
- native schema constraints are a clearer fit than Gemma's generated function-call syntax;
- its context limit is irrelevant but ample;
- the fallback already contains model failures; and
- staying in the current provider minimizes implementation and operational work.

Required gates before changing the default:

1. remove `temperature=0.2` for Gemini 3.5+;
2. pin compatible LangChain integration versions;
3. explicitly pass `method="json_schema"`;
4. run the decomposer test set for valid sources, constraint extraction, useful keyword expansion,
   fallback rate, and p50/p95 latency; and
5. compare `gpt-5-nano` as the cheapest external challenger. Its list rate is lower, but savings on
   such a short prompt are unlikely to pay for a second provider unless measured latency or quality
   is better.

### 2. Evidence-grounded candidate evaluation

**Adopt `gemini-3.5-flash-lite` as the next baseline, conditional on the harness; retain
`gemini-2.5-flash-lite` until the measurement passes.**

Why:

- it is GA, has ample context and native structured output, and is explicitly aimed at document
  parsing and structured extraction;
- it preserves the existing provider integration;
- at the illustrative workload it remains about one third the input cost of GPT-5.6 Luna or Haiku
  4.5; and
- provider documentation does not establish that either alternative is more evidence-grounded.

Challenge it with:

- **`gpt-5.6-luna`** for a current OpenAI quality/cost comparison with a 1.05M context window; and
- **Claude Haiku 4.5** for Anthropic's fastest tier and a separate constrained-output
  implementation.

Do not use schema-parse success as the winner criterion. Select on:

1. candidate-ID validity and coverage;
2. unique/contiguous ranks and ranking metric (Recall@k or nDCG);
3. requirement-check correctness;
4. unsupported-claim and hallucinated-ID rate;
5. citation/source-URL correctness;
6. report-to-structured-result consistency;
7. p50/p95 latency and fallback/retry rate; and
8. total cost per successful report, including retries and reasoning tokens.

## Decision rule

Use the planned 20-query harness as a paired comparison with identical candidate lists and evidence
excerpts. A provider/model should replace the Gemini baseline only if it:

- passes native schema plus SetScout semantic validation;
- improves the grounding/report rubric or ranking metric by a predeclared meaningful margin;
- does not regress p95 latency beyond the demo's acceptable budget; and
- has an acceptable cost per successful report, not merely a favorable token price.

That test converts provider marketing and API guarantees into evidence for SetScout's actual task.

## Primary sources

[claude-models]: https://platform.claude.com/docs/en/about-claude/models/overview
[claude-pricing]: https://platform.claude.com/docs/en/about-claude/pricing
[claude-selection]: https://platform.claude.com/docs/en/about-claude/models/choosing-a-model
[claude-structured]: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
[gemini-25-model]: https://ai.google.dev/gemini-api/docs/models/gemini-2.5-flash-lite
[gemini-35-model]: https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite
[gemini-latest]: https://ai.google.dev/gemini-api/docs/latest-model
[gemini-pricing]: https://ai.google.dev/gemini-api/docs/pricing
[gemini-structured]: https://ai.google.dev/gemini-api/docs/structured-output
[gemini-tokens]: https://ai.google.dev/gemini-api/docs/tokens
[gemma-4-card]: https://ai.google.dev/gemma/docs/core/model_card_4
[gemma-api]: https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api
[gemma-tools]: https://ai.google.dev/gemma/docs/capabilities/text/function-calling-gemma4
[gpt-5-nano]: https://developers.openai.com/api/docs/models/gpt-5-nano
[openai-models]: https://developers.openai.com/api/docs/models
[openai-priority]: https://openai.com/api-priority-processing/
[lc-anthropic]: https://docs.langchain.com/oss/python/integrations/chat/anthropic
[lc-google]: https://docs.langchain.com/oss/python/integrations/chat/google_generative_ai
[lc-google-4]: https://github.com/langchain-ai/langchain-google/discussions/1422
[lc-openai]: https://docs.langchain.com/oss/python/integrations/chat/openai
