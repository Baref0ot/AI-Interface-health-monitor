# Interface Health Monitor

Real-time AI-powered incident intelligence system.

## Architecture

Producer → Kafka → Consumer → PostgreSQL → Embeddings → Similarity Search → (LLM soon)

## Features

- Real-time streaming (Kafka)
- Persistent storage (PostgreSQL)
- AI embeddings (sentence-transformers)
- Similarity-based anomaly detection

## Run

### Start infrastructure
docker compose up -d

### Start consumer
python3 -m src.streaming.consumer

### Start producer
python3 -m src.streaming.producer



## Architectural Diagram

```mermaid
flowchart TD
    A[Synthetic Data Generator] -->|publishes events| B[Kafka]
    B -->|consumes events| C[Anomaly Detection Service]

    C --> D[Hugging Face<br>(classify)]
    C --> E[Pinecone<br>(find similar past anomalies)]

    D --> F[Escalation Logic]
    E --> F

    F -->|if yes| G[OpenAI / Claude<br>(root-cause analysis)]

    G --> H[PostgreSQL<br>(store result)]
    H --> I[FastAPI<br>(serve results via API)]
    I --> J[MCP Server<br>(expose as tools)]
``



Architectural Diagram:

[Synthetic Data Generator]
        │
        ▼ (publishes events)
    [ Kafka ]
        │
        ▼ (consumes events)
[Anomaly Detection Service]
    │           │
    ▼           ▼
[Hugging Face]  [Pinecone]
 (classify)    (find similar past anomalies)
    │           │
    └─────┬─────┘
          ▼
   [Escalation Logic]
    "Is this worth sending to the cloud LLM?"
          │
          ▼ (if yes)
      [OpenAI / Claude]
       (root-cause analysis)
          │
          ▼
    [PostgreSQL]
     (store result)
          │
          ▼
    [FastAPI]
     (serve results via API)
          │
          ▼
    [MCP Server]
     (expose as tools)