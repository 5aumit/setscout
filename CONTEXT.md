# SetScout

SetScout helps ML researchers discover and assess datasets against a stated research need.

## Language

**Run**:
A single execution of SetScout for one submitted dataset search request, ending in results, failure, or cancellation.
_Avoid_: Job, session, pipeline execution

**Run Event**:
A typed, presentation-independent fact emitted as a Run advances, such as a Stage starting, an Activity Update changing, or the Run completing.
_Avoid_: Log message, Markdown update, callback

**Search Brief**:
The compact, read-only presentation of the submitted dataset search request shown after its editable form collapses.
_Avoid_: Query, prompt, form summary

**Stage**:
A stable, user-facing phase of a SetScout run that communicates meaningful progress without exposing the pipeline's implementation structure.
_Avoid_: Node, graph node, step

**Stage Lifecycle**:
The allowed progression of a Stage: Waiting, then Running, then one of Completed, Completed with warnings, or Failed.
_Avoid_: Node status

**Completed with warnings**:
A Stage outcome indicating that useful work completed with partial data or a fallback, so the run may continue but the limitation must remain visible in the results.
_Avoid_: Success, Failed

**Failed**:
A Stage outcome indicating that the Stage could not produce meaningful input for the next Stage, so the run cannot continue.
_Avoid_: Completed with warnings

**Activity Update**:
A curated, user-facing milestone emitted while a Stage is Running. It communicates meaningful progress without exposing prompts, stack traces, retries, or low-level tool calls.
_Avoid_: Log, trace, node update

**Run Summary**:
A compact post-run record of Stage outcomes. It permanently replaces transient Activity Updates while preserving expandable durations, completion counts, outcomes, and Result Limitations.
_Avoid_: Logs, trace output

**Recovery View**:
The post-failure presentation that preserves completed Stage outcomes and user inputs, explains the failure in plain language, and offers a safe next action.
_Avoid_: Error dump, results

**Cancelled**:
A Run outcome indicating that the user stopped execution. It preserves Stage history but does not produce incomplete final results.
_Avoid_: Failed, aborted

**Queued**:
A Run state indicating that the request is waiting for execution capacity and no Stage has begun.
_Avoid_: Waiting Stage, Running

**Results**:
The structured, ranked dataset assessments produced by a completed Run, including requirement checks, known issues, fit summaries, and source links.
_Avoid_: Report, response, answer

**Empty Results**:
A completed Run outcome in which the configured sources were searched successfully but no dataset candidates matched. It invites search refinement and is not a failure or warning.
_Avoid_: Failed, no output

**Result Overview**:
A concise generated narrative that orients the user to the Results without replacing their structured evidence.
_Avoid_: Report, results

**Evidence Citation**:
A source document reference and supporting excerpt attached to a specific requirement check or known issue in the Results.
_Avoid_: Dataset link, raw evidence, source dump

**Requirement Check**:
An evidence-backed assessment of whether a dataset meets one stated search requirement: Meets, Partially meets, Does not meet, or Not verified.
_Avoid_: Score, validation

**Not verified**:
A Requirement Check outcome indicating that available evidence does not establish whether the dataset meets the requirement.
_Avoid_: Unknown, Does not meet

**Result Limitation**:
A visible qualification describing reduced coverage or confidence in otherwise meaningful Results. Run-wide limitations appear with the Result Overview; dataset-specific limitations appear on the affected result card.
_Avoid_: Degradation warning, error, failure
