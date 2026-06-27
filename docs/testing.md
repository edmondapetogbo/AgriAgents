# AgriAgents Testing Plan

## Objective

Validate that each module works independently before testing the complete multi-agent workflow.

---

# Test Case 1

Healthy Leaf

Expected Result

* Disease: Healthy
* Confidence > 90%
* Affected Area: 0–5%

---

# Test Case 2

Mild Disease

Expected Result

* Correct disease detected
* Confidence > 85%
* Affected Area: 10–30%

---

# Test Case 3

Severe Disease

Expected Result

* Correct disease detected
* Confidence > 85%
* Affected Area > 40%

---

# Test Case 4

Missing Image

Expected Result

Return a structured error.

Example

```json
{
    "error": "Image not found."
}
```

---

# Test Case 5

Invalid Image

Example

* Car
* Dog
* Building

Expected Result

Return a structured error without crashing.

---

# Integration Test

Input

Leaf image

Expected Pipeline

Image

↓

Diagnosis Agent

↓

Forecast Agent

↓

Advisory Agent

↓

Report Agent

Expected Result

Complete agricultural diagnosis report generated successfully.
