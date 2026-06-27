# AgriAgents System Flow

## Workflow

Farmer uploads an image.

↓

Diagnosis Agent

* Detect crop
* Detect disease
* Estimate affected area

↓

Forecast Agent

* Retrieve weather data
* Estimate disease spread risk

↓

Advisory Agent

* Read diseases.json
* Generate recommendations
* Generate prevention strategies

↓

Report Agent

* Combine all outputs
* Produce final report

↓

Display final results to the farmer.

---

## Multi-Agent Architecture

User

↓

Diagnosis Agent

↓

Forecast Agent

↓

Advisory Agent

↓

Report Agent

↓

Final Report
