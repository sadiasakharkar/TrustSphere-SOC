# TrustSphere-SOC

TrustSphere-SOC is an AI-driven Security Operations Center platform designed to help analysts detect, correlate, prioritize, and respond to cyber incidents in regulated environments. The system is built for offline-first and air-gapped deployments, making it suitable for banking, fintech, and other security-sensitive domains where data sovereignty and controlled infrastructure are critical.

## Overview

TrustSphere-SOC combines behavioral analytics, incident correlation, risk-based prioritization, and analyst-guided response generation into a unified workflow. It is designed to reduce alert fatigue, improve incident triage quality, and provide evidence-backed, approval-required recommendations without relying on external cloud AI services.

## Core Capabilities

- Multi-format ingestion for structured and semi-structured security telemetry
- Canonical normalization across heterogeneous log formats and field schemas
- Rule-based and machine learning-assisted prefiltering
- Behavioral anomaly detection across users, IPs, hosts, protocols, and actions
- Incident correlation with duplicate suppression and timeline reconstruction
- Risk-based incident prioritization with asset context and recurrence awareness
- Offline or secured-remote LLM integration for analyst-only playbook generation
- Feedback-driven improvement for prioritization and retraining workflows

## Architecture

- `frontend/` user interface and analyst workflow experience
- `backend/` service-layer application logic
- `ingestion/` source parsing and record loading
- `normalization/` canonical event mapping and validation
- `prefiltering/` rule scoring, first-stage classification, and fusion logic
- `anomaly_detection/` behavioral feature engineering and anomaly models
- `correlation/` incident construction, deduplication, and evidence building
- `prioritization/` incident ranking and LLM gating
- `llm_service/` local and secured-remote LLM client integrations
- `playbook_generation/` structured evidence packaging and response recommendations
- `feedback_loop/` analyst feedback capture and retraining signal generation

## Security Principles

- Offline-first design for controlled and air-gapped environments
- Structured evidence handling instead of uncontrolled raw-log forwarding
- Analyst-only response recommendations
- Human approval required for playbook actions
- Support for authenticated and signed remote LLM requests
- Least-privilege and compliance-oriented deployment model

## Technology Stack

- Python
- FastAPI-ready backend structure
- Scikit-learn-based detection and anomaly models
- Local LLM support through Ollama
- Extensible pipeline for incident reasoning and playbook generation

## Use Cases

- SOC alert triage and noise reduction
- Behavioral threat detection
- Insider threat and suspicious activity review
- Incident correlation across multiple telemetry sources
- Evidence-backed response playbook generation for regulated environments

## Repository

This repository contains the core platform code, pipeline components, evaluation scripts, and supporting project assets for TrustSphere-SOC.
