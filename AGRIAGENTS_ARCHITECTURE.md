# AGRIAGENTS ARCHITECTURE DOCUMENT

## Project Information

### Project Name

AgriAgents

### Track

Agents for Good

### Problem Statement

Small and medium-scale farmers often lack immediate access to agricultural experts, leading to delayed disease diagnosis and treatment. AgriAgents is a multi-agent AI system that analyzes crop images, detects diseases, estimates affected area, predicts disease spread risk using weather conditions, and generates actionable recommendations with minimal farmer input.

---

# Objectives

1. Reduce farmer intervention.
2. Detect crop diseases from images.
3. Estimate affected leaf area percentage.
4. Predict disease spread risk using weather conditions.
5. Provide context-aware recommendations.
6. Generate farmer-friendly reports.

---

# User Inputs

Required:

* Crop Image

Optional:

* Crop Name
* Location

Example:

{
"image": "crop.jpg",
"crop_name": "Tomato",
"location": "Ahmedabad"
}

---

# Dataset

Dataset:
PlantVillage

Supported Crops:

1. Tomato
2. Potato
3. Corn

Supported Classes:

Tomato:

* Healthy
* Early Blight
* Late Blight
* Leaf Mold
* Yellow Leaf Curl Virus

Potato:

* Healthy
* Early Blight
* Late Blight

Corn:

* Healthy
* Common Rust
* Northern Leaf Blight
* Gray Leaf Spot

Total Classes:
12

---

# AI Architecture

## Disease Detection Model

Model:
EfficientNet-B0

Input:
Crop Image

Output Example:

{
"crop": "Tomato",
"disease": "Early Blight",
"confidence": 92.4
}

---

# OpenCV Module

Purpose:
Estimate affected leaf area percentage.

Input:
Crop Image

Output Example:

{
"affected_area_percent": 27.1
}

---

# Agent Architecture

Farmer
↓
Diagnosis Agent
↓
Forecast Agent
↓
Advisory Agent
↓
Report Agent
↓
Farmer

---

## Agent 1: Diagnosis Agent

Responsibilities:

* Crop Identification
* Disease Detection
* Confidence Calculation
* Affected Area Estimation

Tools Used:

* detect_crop_disease()
* estimate_affected_area()

Output Example:

{
"crop": "Tomato",
"disease": "Early Blight",
"confidence": 92.4,
"affected_area_percent": 27.1
}

---

## Agent 2: Forecast Agent

Responsibilities:

* Retrieve Weather Data
* Predict Disease Spread Risk
* Calculate Risk Score

Tools Used:

* get_weather()
* calculate_spread_risk()

Output Example:

{
"temperature": 32,
"humidity": 84,
"rain_expected": true,
"spread_risk_score": 77
}

---

## Agent 3: Advisory Agent

Responsibilities:

* Analyze Disease Impact
* Generate Recommendations
* Generate Prevention Plans
* Prioritize Actions

Tools Used:

* get_disease_info()
* get_prevention_plan()

Output Example:

{
"priority": "High",
"recommendations": [],
"preventive_actions": []
}

---

## Agent 4: Report Agent

Responsibilities:

* Generate Summary
* Generate PDF Report

Tools Used:

* generate_report()

Output Example:

{
"report_path": "report.pdf"
}

---

# MCP Tool Contracts

## detect_crop_disease()

Input:

{
"image_path": "..."
}

Output:

{
"crop": "...",
"disease": "...",
"confidence": 92.4
}

---

## estimate_affected_area()

Input:

{
"image_path": "..."
}

Output:

{
"affected_area_percent": 27.1
}

---

## get_weather()

Input:

{
"location": "Ahmedabad"
}

Output:

{
"temperature": 32,
"humidity": 84,
"rain_expected": true
}

---

## calculate_spread_risk()

Input:

{
"disease": "...",
"affected_area_percent": 27.1,
"humidity": 84,
"rain_expected": true
}

Output:

{
"spread_risk_score": 77
}

---

## get_disease_info()

Input:

{
"crop": "...",
"disease": "..."
}

Output:

{
"description": "...",
"cause": "...",
"symptoms": [],
"spread_conditions": []
}

---

## get_prevention_plan()

Input:

{
"crop": "...",
"disease": "..."
}

Output:

{
"preventive_actions": []
}

---

## generate_report()

Input:

Diagnosis + Forecast + Advisory outputs

Output:

{
"report_path": "report.pdf"
}

---

# Knowledge Base

Storage Type:
JSON

File:

knowledge_base/diseases.json

Contains:

* Description
* Cause
* Symptoms
* Spread Conditions
* Recommendations
* Preventive Actions

No RAG for MVP.

---

# Security Requirements

1. File Type Validation

Allowed:

* jpg
* jpeg
* png

2. File Size Validation

Maximum:
10 MB

3. API Key Protection

Store:

* Gemini API Key
* Weather API Key

In:
.env

4. Input Sanitization

Validate location and user inputs.

5. Prompt Injection Mitigation

Only structured agent outputs may be passed to Gemini.

---

# Testing Strategy

## Model Testing

Metrics:

* Accuracy
* Precision
* Recall

Target Accuracy:
90%+

---

## OpenCV Testing

Validate affected area estimation on sample images.

---

## Agent Testing

Test:

* Diagnosis Agent
* Forecast Agent
* Advisory Agent
* Report Agent

---

## End-to-End Testing

Image
↓
Diagnosis
↓
Forecast
↓
Advisory
↓
Report

Must complete successfully.

---

# Success Metrics

Model Accuracy:
≥ 90%

Inference Time:
< 3 seconds

End-to-End Processing:
< 10 seconds

Weather Retrieval Success:

> 95%

Report Generation Success:
100%

---

# MVP Scope

Included:

* Disease Detection
* Crop Detection
* Affected Area Estimation
* Weather-Based Risk Prediction
* Recommendations
* PDF Reports
* Multi-Agent Workflow
* MCP Tools

Excluded:

* Mobile App
* User Accounts
* Database Storage
* Historical Tracking
* Drone Integration
* Satellite Imagery
* Yield Prediction
* Voice Assistant

---

# Development Timeline

Day 1:
Disease Detection Model

Day 2:
OpenCV + Diagnosis Agent

Day 3:
Forecast Agent

Day 4:
Advisory Agent

Day 5:
Report Agent + Streamlit + Integration

Days 6–10:
Testing, Security, Optimization, Documentation, Demo, Submission
