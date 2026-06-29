# MCP Architecture

## Overview

The AgriAgents MCP Server exposes the capabilities of the AgriAgents multi-agent system as callable tools for AI assistants.

The MCP server does not contain business logic.

It acts as a thin interface between external AI agents and the existing AgriAgents backend.

---

## Goals

- Reuse the existing backend.
- Avoid code duplication.
- Expose each AI agent independently.
- Allow AI assistants to invoke only the tools they need.
- Preserve the modular architecture.

---

## Architecture

AI Assistant
        │
        ▼
   MCP Server
        │
 ┌──────┴──────────────┐
 │                     │
Diagnosis Tool         Forecast Tool
 │                     │
 ▼                     ▼
Diagnosis Agent    Forecast Agent
 │                     │
 └──────────┬──────────┘
            ▼
      Advisory Tool
            │
            ▼
      Advisory Agent
            │
            ▼
       Report Tool
            │
            ▼
       Report Agent

---

## Tools

### diagnose_crop

Purpose:

Identify crop species, disease and affected area.

Returns:

- crop
- disease
- confidence
- affected_area

---

### forecast_disease

Purpose:

Estimate disease spread risk using weather conditions.

Returns:

- spread_risk
- risk_score
- weather

---

### generate_advice

Purpose:

Generate treatment recommendations and prevention strategies.

Returns:

- priority
- recommendations
- prevention

---

### generate_report

Purpose:

Aggregate all outputs into a final farmer report.

Returns:

Complete report JSON.

---

## Design Principles

- Thin server
- Modular tools
- Existing agents remain unchanged
- No duplicated logic
- Easy future extension
