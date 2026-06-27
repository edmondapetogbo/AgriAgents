# AgriAgents API Contracts

## Overview

This document defines the data exchanged between the agents of the AgriAgents system.

---

# Diagnosis Agent

## Input

```json
{
    "image_path": "path/to/image.jpg"
}
```

## Output

```json
{
    "crop": "Tomato",
    "disease": "Early Blight",
    "confidence": 97.2,
    "affected_area_percent": 23.7
}
```

---

# Forecast Agent

## Input

```json
{
    "location": "Ahmedabad",
    "crop": "Tomato",
    "disease": "Early Blight",
    "affected_area_percent": 23.7
}
```

## Output

```json
{
    "spread_risk": "Medium",
    "risk_score": 62,
    "weather_summary": "High humidity expected within 48 hours."
}
```

---

# Advisory Agent

## Input

```json
{
    "crop": "Tomato",
    "disease": "Early Blight",
    "affected_area_percent": 23.7,
    "spread_risk": "Medium"
}
```

## Output

```json
{
    "recommendations": [
        "Apply recommended fungicide.",
        "Improve airflow.",
        "Inspect nearby plants."
    ],
    "prevention": [
        "Avoid overhead irrigation.",
        "Rotate crops."
    ]
}
```

---

# Report Agent

## Input

```json
{
    "diagnosis": {},
    "forecast": {},
    "advisory": {}
}
```

## Output

```json
{
    "summary": "Tomato plant diagnosed with Early Blight.",
    "diagnosis": {},
    "forecast": {},
    "advisory": {}
}
```
