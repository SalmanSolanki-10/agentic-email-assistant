# Agentic Email Agent

## About
- This project is an agentic email assistant built in Python that monitors an inbox, understands incoming messages using an LLM, and generates context-aware replies automatically. The system is designed with a modular, production-style architecture that separates email ingestion, reasoning, response generation, and delivery.

- The assistant continuously watches an email inbox via IMAP, classifies and processes new messages, invokes a LangChain-based reasoning agent to determine an appropriate response, and sends replies via SMTP. To ensure safety and reliability, the system tracks processed message IDs to prevent duplicate responses across restarts and exposes a lightweight Flask web interface for monitoring activity and basic controls.


## Prerequisites

- At a minimum, the project depends on:
    - flask
    - langchain
    - langchain-community
    - langchain-openai (or Ollama equivalent if configured)
    - python-dotenv
    - imaplib (stdlib)
    - smtplib (stdlib)

- Before running the email agent, make sure the following are installed:

  - Python version:
    `Python 3.9+`

  - Create and activate a virtual environment (recommended):

    `python3 -m venv .venv`

    `source .venv/bin/activate`

  - Install required dependencies:

    `pip install -r requirements.txt`

## Using Ollama (Local LLM)
- This project supports running fully locally using Ollama instead of a hosted LLM (for example, OpenAI). This is useful for privacy, offline development, and portfolio demonstrations of local LLM orchestration.

### Install Ollama
- Follow the official installation instructions for your OS

    ```bash
    https://ollama.com/download
    ```

- Verify installation:

    ```bash 
    ollama --version
    ```

- Pull a Model:

  - Pull at least one supported model (example: llama3):
    ```bash 
    ollama pull llama3
    ```

- List installed models:
    ```bash 
    ollama list
    ```

- Configure Environment Variables
    ```bash
    export OLLAMA_MODEL="llama3"
    export ENABLE_TOOLS="true"
    ```

Note: 
- By default, the application connects to Ollama at:
    http://localhost:11434
    No API key is required.

- Ollama must be running before starting the agent:
```bash 
ollama serve
```


## Run

- In order to run the application, please follow the steps listed below:

```bash
cd refactored_email_agent
python3 run_email_agent.py
```

## Required environment variables (Gmail)
Use a Gmail **App Password** (recommended).

```bash
export GMAIL_ADDRESS="you@gmail.com"
export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
```

## Optional (SMTP)
If not set, sending runs in demo mode (responses are generated but not emailed).

```bash
export SMTP_USER="$GMAIL_ADDRESS"
export SMTP_APP_PASSWORD="$GMAIL_APP_PASSWORD"
```

## Optional (Tools / tracing)
```bash
export OLLAMA_MODEL="llama3"
export ENABLE_TOOLS="true"
export TAVILY_API_KEY="..."
export LANGCHAIN_API_KEY="..."          # LangSmith
export LANGSMITH_TRACING="true"
export LANGCHAIN_PROJECT="General Purpose Email Agent"
```

## Optional (web / polling)
```bash
export POLL_SECONDS="30"
export WEB_HOST="0.0.0.0"
export WEB_PORT="5001"
export STATE_PATH="state/processed_message_ids.jsonl"
```
# agentic-email-assistant
