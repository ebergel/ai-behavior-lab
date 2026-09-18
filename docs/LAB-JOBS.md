# Lab Jobs

Lab Jobs separates the execution of a prepared JEV assessment from the conversation with a coding assistant. A detached Python worker sends requests, validates and saves responses, enforces the frozen limits, and exposes compact progress. No supervising model is called for execution, polling, arithmetic or status reporting. The researcher authorized this workflow on 18 September 2026, with a default **$10 expenditure ceiling** and no repeated JEV approval prompt.

The first registered job is **Mind & discourse · four-wording comparison**: 48 existing model-output passages and twelve synthetic controls, 27 questions across four wordings, 240 unique requests. It retains its earlier, stricter **$2** frozen cap and maximum 252 attempts. The first four technical checks are included in that allocation. Existing TypeSafe questions, classifier and response validation are unchanged.

## Use

Open [Lab Jobs](http://127.0.0.1:8765/#view=jobs) in the sidebar. Start or Resume launches the registered job without a confirmation dialog. Progress, attempts, known cost, reserved unknown usage and effective cap update approximately every five seconds while the view is visible. Open results leads to the existing Mind & discourse workspace.

Pause takes effect between requests. A request already sent is allowed to finish so its receipt can be preserved; a permitted overload backoff may also finish before pausing. Resume continues the same finite allocation. A completed allocation cannot dispatch more requests. Failed or uncertain outcomes stop the worker and remain available for examination. An in-flight request with a running worker is not a failed request.

The worker survives closing the browser or restarting Explorer. If the Mac or worker stops during a request, its durable request marker remains and further dispatch is blocked until the uncertain outcome is examined. Runtime locks and state live under ignored `workspace/.lab-jobs/`; authoritative assessment evidence remains in `workspace/mind-lenses/discourse-portraits-20260918-v2/` and is included in the research snapshot.

## Implementation boundary

- `behaviorlab.lab_jobs` maps one registered job ID to an exact plan fingerprint, frozen runner and authorization. The UI cannot submit shell commands, paths, URLs, model names, payloads or new budgets.
- GET `/api/jobs` reports status. POST `/api/jobs/start` and `/api/jobs/pause` accept only the registered ID and use the Explorer's existing local Host, Origin and token checks.
- Start is protected by a control lock; repeated clicks do not spawn duplicate work. A separate worker lock prevents duplicate workers, and the original runner lock guards its evidence.
- Each worker step calls the unchanged frozen runner with `max_calls=1`, preserving its input hashes, costs, overload-only retry rules and aggregate limits. A short interval separates requests. The original allocation and source code remain intact.
- Raw exceptions are not exposed to the UI, and neither credentials nor bulk logs enter progress responses. The API returns compact counts and links, while the existing result view reads the original receipts.
- New job types must be explicitly registered with frozen inputs, finite request counts and a ceiling within the user's $10 limit. This screen does not launch arbitrary batches or participant-generation campaigns. No scheduler is installed.

The user-approved use of cheaper models was applied to implementation: GPT-5.6 Luna built the frontend and focused browser-logic tests. Runtime execution uses Python. A local-model narrative summarizer remains optional future work; it is not required by this job and has not been installed or invoked.

## Verification

Offline tests exercise registry/budget/authorization checks, duplicate Start behavior, detached process invocation, graceful pause/resume, completion, exception redaction and uncertain-request blocking. Browser-logic tests use mocked APIs to cover actions, stale visits and pause state. The real assessment continued across an Explorer restart. Live pausing solely for UI verification was rejected by automatic approval review and was not attempted through another route; simulated tests cover that behavior without altering the running assessment.

Validation at implementation: **355 Python tests and 80 JavaScript tests passed**. Live browser checks verified progress, cost display, normal in-flight status and navigation; the actual worker continued through an Explorer restart.

The first real job completed **240 / 240 requests, 6,480 probabilities, $0.047085024 reported cost**, without retries or unknown-cost reserves. Its finite allocation is exhausted; completed job controls cannot launch additional inference. See [the comparison report](MIND-DISCOURSE-RESULTS.md).

## Full-corpus Mind & discourse job

`mind-discourse-corpus-v1` is the second allowlisted job. Its separately pinned plan and release authorize 19,196 new calls plus 120 exact pilot reuses, under an aggregate $10 cap. It uses the frozen concurrent coordinator, which drains active calls before pausing, and continues independently of Explorer. Its results link selects the full-corpus dataset. The original pilot remains a separate completed job. See [the full protocol](MIND-DISCOURSE-CORPUS.md).
