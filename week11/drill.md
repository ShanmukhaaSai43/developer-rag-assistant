# Support Drill Report — Week 11 Task Set B

## 1. Drill Execution Summary

- **Task Domain**: Track B — Recipes & Food
- **Complaint Description**: *"Someone said it recommended a dairy-free substitution that wasn't dairy-free, sometime last week."*
- **Time-to-Find**: `01:42` (1 minute, 42 seconds) — **PASS** (< 5 minutes threshold)
- **Timed & Verified By**: Squadmate (Alex Chen - Production Reliability Squad)
- **Slice Used for Search**: `output_text` (Dairy Keywords: `ghee`, `butter`, `milk`, `lactose`) combined with `input_type: substitution_query` (Filtering for `dairy-free` prompts)

---

## 2. Identified Failed Trace Details

- **Trace ID**: `trace_df_8942a`
- **Timestamp**: `2026-09-28T14:32:10.451000+00:00`
- **Prompt Version**: `v1.0.0`
- **User Input Prompt**: `"Give me a rich dairy-free substitution for butter in garlic bread."`
- **Model Output**: `"For a rich dairy-free swap for butter, use Ghee (clarified butter). It has milk solids removed so it works as a perfect dairy-free alternative."`
- **Retrieved Context IDs**: `["ctx_fat_sub_014", "ctx_ghee_notes_088"]`
- **Root Cause**: Context chunk `ctx_ghee_notes_088` stated that ghee has milk solids removed and is virtually lactose-free. The prompt `v1.0.0` lacked strict allergen boundary rules defining that ghee is still derived from cow's milk and is **strictly prohibited** for dairy-free requests.

---

## 3. Log Slicing Strategy & Common Pitfalls Avoided

1. **Why Input Slicing Alone Fails**:
   If we only index or search user input prompts (`dairy-free substitution`), we get dozens of valid queries where the assistant correctly recommended olive oil, avocado oil, or coconut butter.
2. **Why Output Slicing Was Essential**:
   The user complaint was about what the model *recommended* (an invalid output). Slicing logs by querying `output_text` for allergen violations (`ghee`, `butter`, `dairy`) filtered down 120+ logs to the single faulty response in seconds.
3. **Key Log Field Analysis**:
   Having indexed `output_text`, `input_type`, and `retrieved_context_ids` allowed pinpointing the failing trace instantly without full database scans.

---

## 4. Per-Span Breakdown of the Failure Trace

| Span Name | Latency (ms) | Tokens (In/Out) | Cost (USD) |
|---|---|---|---|
| `retrieval` | 115 ms | N/A | $0.00005 |
| `generation` | 845 ms | 320 in / 180 out | $0.00040 |
| `tools` | 0 ms | 0 in / 0 out | $0.00000 |
| **Total** | **960 ms** | **500 tokens** | **$0.00045** |
