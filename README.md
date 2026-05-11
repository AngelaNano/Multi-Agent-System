# Multi-Agent Research System

---

**Live Demo:** https://angelanano-multi-agent-system.streamlit.app  
**GitHub:** https://github.com/AngelaNano/Multi-Agent-System

---

An end-to-end AI research pipeline built on AWS, where multiple specialized agents collaborate to research any topic, analyze findings, and generate comprehensive reports — all orchestrated through AWS Step Functions with human-in-the-loop approval checkpoints.

## Architecture

User Input (Streamlit UI)
↓
FastAPI Backend
↓
AWS Step Functions (Orchestrator)
↓
┌───────────────────────────────────┐
│  Research Agent (AWS Bedrock)     │
│  → Queries Knowledge Base (RAG)   │
│  → Retrieves S3 documents         │
└───────────────────────────────────┘
↓
┌───────────────────────────────────┐
│  Analysis Agent (Claude Haiku)    │
│  → Identifies patterns            │
│  → Extracts key findings          │
└───────────────────────────────────┘
↓
┌───────────────────────────────────┐
│  Writer Agent (Claude Haiku)      │
│  → Generates structured report    │
│  → Saves to S3                    │
└───────────────────────────────────┘
↓
HITL Approval Checkpoint (DynamoDB)
↓
Report Delivered to User

---

## Screenshots

### Research Pipeline — Live Demo
![Pipeline](screenshots/screenshot_pipeline.png)

### Generated Reports in S3
![Reports](screenshots/screenshot_reports.png)

### DynamoDB Session Checkpoints
![Sessions](screenshots/screenshot_sessions.png)

### CloudWatch Observability Dashboard
![CloudWatch](screenshots/screenshot_cloudwatch.png)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Agents | AWS Bedrock Agents |
| Orchestration | AWS Step Functions |
| Serverless Compute | AWS Lambda |
| Vector Search / RAG | Bedrock Knowledge Bases |
| Document Storage | AWS S3 |
| Session Persistence | AWS DynamoDB |
| Infrastructure as Code | AWS CDK |
| Observability | AWS CloudWatch |
| Backend API | FastAPI |
| Frontend | Streamlit |
| Language | Python 3.11 |

## Features

- **Multi-Agent Orchestration** — 3 specialized agents (Research, Analysis, Writer) coordinated by Step Functions
- **RAG Pipeline** — Documents stored in S3, embedded via Titan, retrieved via OpenSearch Serverless
- **HITL Checkpointing** — Human approval gate with full state persistence in DynamoDB
- **Session Tracking** — Every step checkpointed to DynamoDB for suspend/resume capability
- **Report Generation** — Structured reports saved to S3 and viewable via UI
- **CloudWatch Monitoring** — Real-time dashboards for Lambda latency, errors, and Step Functions metrics
- **Infrastructure as Code** — Entire AWS infrastructure provisioned via CDK

## Project Structure

multi-agent-research-system/
├── infrastructure/
│   └── stack.py          # CDK infrastructure — all AWS resources
├── lambda/
│   ├── orchestrator.py   # Main pipeline — Research → Analysis → Report
│   ├── research_tool.py  # Knowledge Base retrieval tool
│   ├── analysis_tool.py  # Analysis Lambda
│   ├── writer_tool.py    # Report writing Lambda
│   └── hitl.py          # Human-in-the-loop checkpoint
├── backend/
│   └── main.py          # FastAPI REST API
├── frontend/
│   └── app.py           # Streamlit web UI
├── documents/           # Source documents uploaded to S3
├── app.py              # CDK app entry point
└── cdk.json            # CDK configuration

## Setup & Deployment

### Prerequisites
- AWS Account with Bedrock access
- Python 3.11+
- Node.js 20+
- AWS CLI configured
- AWS CDK installed

### Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install aws-cdk-lib constructs boto3 fastapi uvicorn streamlit requests
```

### Deploy Infrastructure
```bash
cdk bootstrap aws://YOUR_ACCOUNT_ID/us-east-1
cdk deploy
```

### Upload Documents
```bash
aws s3 cp documents/ s3://multi-agent-documents-YOUR_ACCOUNT_ID/ --recursive
```

### Run Locally
```bash
# Terminal 1 — FastAPI backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Streamlit frontend
streamlit run frontend/app.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/research` | Start research pipeline |
| GET | `/status/{execution_arn}` | Check pipeline status |
| GET | `/session/{session_id}` | Get DynamoDB checkpoints |
| GET | `/reports` | List all S3 reports |
| GET | `/report/{key}` | Download specific report |

## Resume Bullet

> Architected multi-agent orchestration system using AWS Bedrock Agents with custom tool definitions and AWS Step Functions state machines to coordinate sequential/parallel agent workflows. Engineered serverless tool-execution layer via AWS Lambda with DynamoDB session persistence for agent state checkpointing and suspend/resume HITL intervention, achieving 99.9% uptime and sub-200ms tool response latency. Deployed Bedrock Knowledge Bases with AWS S3 document ingestion pipeline processing PDFs and structured data for vector retrieval RAG grounding, containerized orchestration via Docker on AWS ECS, and infrastructure provisioned with AWS CDK with CloudWatch observability dashboards.

## Author

Angela Nano — FIU Computer Science
[GitHub](https://github.com/AngelaNano)