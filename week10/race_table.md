# Week 10 Practical — Race Table: Single Agent vs. Kitchen Squad

## 1. Executive Metric Comparison (4 Metrics x 2 Arms)

Evaluated on the exact **10 Week-6 test cases** (`sub_01` through `sub_10`) using the shared chemical & textural viability judge.

| Metric Dimension | Arm 1: Single Agent | Arm 2: Multi-Agent Squad | Delta / Multiplier | Winner |
|---|---|---|---|---|
| **Pass Rate (Quality)** | **100.0%** (10/10) | **100.0%** (10/10) | +0.0% | **Tie** |
| **p50 Latency (Speed)** | **4.17s** | **10.2s** | 2.4x slower | **Single Agent** |
| **p99 Latency (Worst-case)** | **38.75s** | **46.72s** | 1.2x slower | **Single Agent** |
| **Total Tokens Consumed** | **13,669** | **35,168** | **2.6x** tokens | **Single Agent** |
| **Average Cost per Question** | **$0.000226** | **$0.000559** | 2.5x cost | **Single Agent** |

---

## 2. Multiplier & Dominant Hand-Off Attribution

> **Context re-send multiplier: 2.6x (multi tokens: 35168 / single tokens: 13669), with dominant hand-off attributed to 'workers -> orchestrator synthesis' accounting for 45.1% of all squad tokens.**

### Per-Handoff Token Distribution:
- **orchestrator -> substitution_worker**: 6,510 tokens (18.5% of total squad bill)
- **orchestrator -> allergen_worker**: 12,786 tokens (36.4% of total squad bill)
- **workers -> orchestrator synthesis**: 15,872 tokens (45.1% of total squad bill)

---

## 3. The 10 Week-6 Evaluation Cases Tested
- **sub_01**: Country Sourdough Loaf — All-Purpose Flour (10% protein) 1:1 with 5% hydration reduction
- **sub_02**: Country Sourdough Loaf — 100% Coconut Flour 1:1 without additional binders or water adjustment
- **sub_03**: Country Sourdough (3-Loaf Batch) — 3x Batch Multiplication (3000g Flour, 2250g Water, 600g Starter, 60g Salt)
- **sub_04**: Classic Baechu Kimchi — Yondu Umami Vegetable Broth + Dried Kelp (Dashima) Soaking Water
- **sub_05**: Classic Baechu Kimchi — Iodized Table Salt with Sodium Ferrocyanide Anti-Caking Agent 1:1 by weight
- **sub_06**: Primary Kombucha Batch (1 Gallon) — 1 US Gallon Scaling (3785g Water, 270g Cane Sugar, 27g Black Tea, 378g Starter Liquid)
- **sub_07**: Primary Kombucha — Raw Unpasteurized Antibacterial Honey 1:1 by weight
- **sub_08**: Traditional Red Miso Paste — Barley Koji (Mugi Koji) cultivated with Aspergillus oryzae 1:1 by weight
- **sub_09**: Traditional Red Miso Paste — Low-Sodium Modification reducing salt to 20g (4.0% ratio)
- **sub_10**: Naturally Fermented Garlic Dill Pickles — Black Tea Leaves (Assam) in cheesecloth sachet (2g) for natural tannins

---

## 4. Per-Case Granular Results Table

| Case ID | Dish Name | Proposed Substitution | Single Pass | Single Latency | Multi Pass | Multi Latency |
|---|---|---|---|---|---|---|
| `sub_01` | Country Sourdough Loaf | All-Purpose Flour (10% protein) 1:1 wi... | PASS | 3.772s | PASS | 9.128s |
| `sub_02` | Country Sourdough Loaf | 100% Coconut Flour 1:1 without additio... | PASS | 3.869s | PASS | 4.36s |
| `sub_03` | Country Sourdough (3-Loaf Batch) | 3x Batch Multiplication (3000g Flour, ... | PASS | 2.966s | PASS | 46.622s |
| `sub_04` | Classic Baechu Kimchi | Yondu Umami Vegetable Broth + Dried Ke... | PASS | 5.961s | PASS | 12.225s |
| `sub_05` | Classic Baechu Kimchi | Iodized Table Salt with Sodium Ferrocy... | PASS | 4.346s | PASS | 10.046s |
| `sub_06` | Primary Kombucha Batch (1 Gallon) | 1 US Gallon Scaling (3785g Water, 270g... | PASS | 3.393s | PASS | 9.787s |
| `sub_07` | Primary Kombucha | Raw Unpasteurized Antibacterial Honey ... | PASS | 41.997s | PASS | 10.351s |
| `sub_08` | Traditional Red Miso Paste | Barley Koji (Mugi Koji) cultivated wit... | PASS | 4.064s | PASS | 28.908s |
| `sub_09` | Traditional Red Miso Paste | Low-Sodium Modification reducing salt ... | PASS | 4.285s | PASS | 8.437s |
| `sub_10` | Naturally Fermented Garlic Dill Pickles | Black Tea Leaves (Assam) in cheeseclot... | PASS | 5.121s | PASS | 46.725s |
