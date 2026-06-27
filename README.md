

# 🌱 AgriAgents

 **An AI-powered multi-agent decision support system for crop disease diagnosis, severity estimation, disease spread forecasting, and treatment recommendations.**

AgriAgents combines **Computer Vision**, **Multi-Agent AI**, **Weather Intelligence**, and a **Knowledge Base** to help farmers detect crop diseases early, estimate infection severity, predict disease spread, and receive actionable recommendations through a simple and intuitive interface.

---

## 🚀 Project Overview

Crop diseases are responsible for significant agricultural losses worldwide. Many farmers rely on manual inspection or expert consultation, which can be time-consuming, costly, and inaccessible in remote areas. Delayed diagnosis often allows diseases to spread rapidly, reducing crop yield and increasing treatment costs.

AgriAgents addresses this challenge by providing an intelligent decision support system capable of analyzing leaf images, estimating disease severity, considering current weather conditions, and generating practical recommendations to support informed agricultural decisions.

Unlike traditional image classification systems, AgriAgents follows a **multi-agent architecture**, where specialized AI agents collaborate to produce a comprehensive diagnosis rather than a single prediction.

---

# 🌍 The Story Behind AgriAgents

AgriAgents began long before I started studying Computer Engineering.

Growing up, I spent part of my childhood in a rural farming community, where I regularly worked alongside my uncle on his farm. Like many small-scale farmers, he faced recurring challenges caused by crop diseases. Disease identification relied mostly on experience, access to agricultural experts was limited, and treatment decisions were often made after significant damage had already occurred.

Watching months of hard work affected by diseases that might have been managed earlier left a lasting impression on me. My uncle often hoped that someone in our family would one day study agricultural engineering and develop practical solutions that could help farmers like him improve crop health and productivity.

Although my academic journey eventually led me toward Computer Engineering and Artificial Intelligence instead of agricultural engineering, I made a personal promise that one day I would use the skills I developed to contribute to solving those same challenges.

AgriAgents is the first realization of that promise.

It represents the intersection of my personal experience, my passion for Artificial Intelligence, and my commitment to building technology that addresses real-world problems. By combining computer vision, weather intelligence, knowledge-based reasoning, and a modular multi-agent architecture, AgriAgents aims to provide farmers with practical decision support that is accessible, explainable, and actionable.

For me, this project is more than a technical achievement—it is an opportunity to transform a childhood experience into a solution that can positively impact farming communities.


# 🎯 Problem Statement

Farmers face several challenges when managing crop diseases:

* Difficulty identifying diseases at an early stage.
* Limited access to agricultural experts.
* Lack of information about disease severity.
* Uncertainty about how weather conditions influence disease spread.
* Difficulty choosing appropriate treatment and prevention strategies.

Existing crop disease classifiers generally stop after predicting the disease label. They rarely explain the severity of infection, estimate future spread, or provide structured recommendations for decision making.

---

# 💡 Proposed Solution

AgriAgents extends traditional crop disease classification by integrating multiple specialized agents into a single intelligent workflow.

The system:

* Detects crop species and disease using a trained deep learning model.
* Estimates the percentage of infected leaf area using OpenCV image processing.
* Retrieves current weather conditions to evaluate disease spread risk.
* Consults an agricultural knowledge base to generate recommendations and prevention strategies.
* Produces a comprehensive report that assists farmers in making timely and informed decisions.

By combining these capabilities into a modular multi-agent system, AgriAgents transforms image classification into a complete agricultural decision support platform.


# ✨ Key Features

AgriAgents provides an end-to-end intelligent crop disease diagnosis and decision support workflow through the collaboration of multiple specialized AI agents.

### 🌿 Crop & Disease Identification

* Detects crop species and diseases from leaf images using a deep learning model trained on the PlantVillage dataset.
* Supports Tomato, Potato, and Corn crops.
* Provides confidence scores for every prediction.

---

### 📊 Disease Severity Estimation

* Uses OpenCV image processing to estimate the percentage of the infected leaf area.
* Provides quantitative severity information instead of only a disease label.
* Helps prioritize treatment based on the extent of infection.

---

### 🌦 Weather-Aware Disease Spread Forecasting

* Retrieves real-time weather conditions using the Open-Meteo API.
* Evaluates environmental factors such as temperature, humidity, and rainfall.
* Estimates the potential risk of disease spread using an explainable rule-based scoring system.

---

### 📚 Knowledge-Based Recommendations

* Uses a structured agricultural knowledge base to generate recommendations.
* Suggests treatment strategies.
* Provides preventive measures to reduce future outbreaks.

---

### 📄 Comprehensive Decision Support Report

* Combines diagnosis, severity estimation, weather analysis, and recommendations into a single report.
* Presents information in a simple and intuitive format suitable for farmers and agricultural professionals.

---

### 🧩 Modular Multi-Agent Architecture

* Independent AI agents perform specialized tasks.
* Each component can be improved or replaced without affecting the rest of the system.
* Designed for scalability and future expansion to additional crops and diseases.

---

# 🏗 Multi-Agent Architecture

AgriAgents follows a modular multi-agent architecture in which each agent is responsible for a specific stage of the decision-making process. Rather than relying on a single monolithic model, specialized agents collaborate to produce an explainable and comprehensive agricultural diagnosis.

## Agent Responsibilities

### 🔍 Diagnosis Agent

Responsibilities

* Detect crop species.
* Identify plant disease.
* Estimate affected leaf area using OpenCV.
* Produce structured diagnosis results.

Output

* Crop
* Disease
* Confidence Score
* Estimated Affected Area

---

### 🌦 Forecast Agent

Responsibilities

* Retrieve current weather conditions.
* Evaluate environmental factors.
* Estimate disease spread risk.

Output

* Temperature
* Humidity
* Rain Probability
* Risk Score
* Spread Risk Level

---

### 🌱 Advisory Agent

Responsibilities

* Query the agricultural knowledge base.
* Generate treatment recommendations.
* Generate prevention strategies.
* Determine intervention priority.

Output

* Recommendations
* Prevention Measures
* Priority Level

---

### 📋 Report Agent

Responsibilities

* Aggregate outputs from all agents.
* Generate a comprehensive farmer-friendly report.
* Present all results through the Streamlit interface.

Output

* Final Decision Support Report

---

# 🤖 Multi-Agent Workflow

```text
                    Farmer
                       │
                       ▼
                Upload Leaf Image
                       │
                       ▼
              Diagnosis Agent
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
 Disease Classification      OpenCV Severity Estimation
         └─────────────┬─────────────┘
                       ▼
               Diagnosis Result
                       │
                       ▼
               Forecast Agent
                       │
                Weather MCP Tool
                       ▼
               Spread Risk Score
                       │
                       ▼
               Advisory Agent
                       │
            Knowledge Base Tool
                       ▼
       Recommendations & Prevention
                       │
                       ▼
                 Report Agent
                       │
                       ▼
              Streamlit Frontend
                       │
                       ▼
                  Final Farmer Report
```

### End-to-End Workflow

1. The farmer uploads a leaf image.
2. The Diagnosis Agent identifies the crop and disease and estimates the affected leaf area.
3. The Forecast Agent retrieves weather information and evaluates disease spread risk.
4. The Advisory Agent consults the knowledge base to generate treatment and prevention recommendations.
5. The Report Agent combines all outputs into a comprehensive agricultural report.
6. The Streamlit application presents the results through a simple and user-friendly interface.

7. The Streamlit interface presents the results to the farmer.

# 🏗 System Architecture

AgriAgents follows a modular multi-agent architecture where specialized AI agents collaborate to provide comprehensive crop disease diagnosis and decision support.

Each agent performs an independent task, making the system easier to maintain, test, and extend.

<p align="center">
  <img src="docs/demo_images/architecture.png" alt="AgriAgents Architecture" width="100%">
</p>

# 🛠 Technology Stack

| Category | Technologies |
|-----------|--------------|
| Programming Language | Python 3.13 |
| Machine Learning | PyTorch |
| Computer Vision | OpenCV |
| User Interface | Streamlit |
| Weather Intelligence | Open-Meteo API |
| Knowledge Base | JSON |
| Testing | Pytest |
| Version Control | Git & GitHub |
| Dataset | PlantVillage |

# ⚙ Installation

Clone the repository

```bash
git clone https://github.com/edmondapetogbo/AgriAgents.git

cd AgriAgents
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate it

macOS/Linux

```bash
source .venv/bin/activate
```

Windows

```bash
.venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

# 🚀 Usage

Launch the Streamlit application

```bash
streamlit run frontend/app.py
```

Upload a leaf image and the system will automatically:

- Detect the crop
- Diagnose the disease
- Estimate affected area
- Evaluate weather conditions
- Predict spread risk
- Generate treatment recommendations
- Produce a comprehensive report

# 🧪 Testing

Run all tests

```bash
pytest
```

Current Status

✅ 32 tests passed

The test suite validates:

- Disease detection
- Severity estimation
- Diagnosis Agent
- Forecast Agent
- Advisory Agent
- Weather tool
- Knowledge Base
- Model integration

# 🖼 Application Preview

## Home Screen

The Streamlit interface allows farmers to upload a leaf image, optionally specify the crop and location, and initiate the AI-powered diagnosis.

<p align="center">
  <img src="docs/demo_images/Home.jpeg" alt="AgriAgents Home Screen" width="90%">
</p>

---

## Diagnosis and Summary Report

After analysis, AgriAgents provides a comprehensive decision support report that includes disease identification, confidence score, estimated affected area, weather-aware spread risk, treatment recommendations, and preventive measures.

<p align="center">
  <img src="docs/demo_images/Result_diagnosis.jpeg" alt="AgriAgents Diagnosis Report" width="90%">
</p>

<p align="center">
  <img src="docs/demo_images/Result_Summary.jpeg" alt="AgriAgents Diagnosis Report" width="90%">
</p>
