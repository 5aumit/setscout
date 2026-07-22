# Stream typed Run Events to presentation layers

SetScout will expose execution progress as typed, presentation-independent Run Events rather than rendered text or polled state snapshots. This keeps pipeline facts stable while allowing the Gradio UI—and future presentation layers—to choose their own wording, layout, animation, and post-run retention behavior.

## Considered Options

- Stream rendered Markdown messages, which is initially simple but couples pipeline behavior to one presentation.
- Stream typed Run Events, which requires an explicit event contract but keeps presentation replaceable.
- Poll full state snapshots, which avoids a stream contract but adds latency and client-side change detection.
