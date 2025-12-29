# LMS Multi-Agent System using Google Agent Development Kit (ADK)

This project implements a **secure, multi-agent AI assistant** for managing a **Learning Management System (LMS)** using **Google's Agent Development Kit (ADK)**.

The system features three specialized AI agents that work together to handle user and course management tasks while enforcing **strict security, privacy, and identity verification** protocols.

## System Overview

### Agents Architecture

```
User Query
       ↓
LMS Coordinator Agent (root_agent)
   ├── Delegates to → User Manager Agent
   │       Handles: User registration, listing, activation/deactivation
   └── Delegates to → Course Manager Agent
           Handles: Course creation, listing, updates
```

- **LMS Coordinator Agent** (`root_agent`)  
  Acts as the main entry point. Analyzes user requests, enforces security policies, verifies identity when needed, and delegates tasks to the appropriate specialist agent.

- **User Manager Agent** (`user_manager_agent`)  
  Responsible for secure user account operations:  
  - Register new users  
  - List all users  
  - Activate/deactivate accounts  
  Includes built-in safeguards: never deletes users, requires authorization checks.

- **Course Manager Agent** (`course_manager_agent`)  
  Manages courses with strict validation:  
  - Create new courses (requires verified instructor ID)  
  - List all courses  
  - Update course details  
  Refuses to create courses without a confirmed instructor user ID.

## Key Features

- **Security-First Design**  
  All agents enforce identity verification before handling sensitive operations (user data, course assignments).
- **Privacy Protection**  
  Personal information (emails, IDs) is never disclosed without proper authorization.
- **Tool Integration**  
  Uses custom `FunctionTool`s to securely call a real LMS backend API over HTTPS with certificate verification.
- **Local LLM Support**  
  Designed to work with locally hosted models via LiteLLM (e.g., Ollama, LM Studio).
- **Modular & Extensible**  
  Easy to add new agents (e.g., Enrollment Agent, Grade Manager) in the future.

## Prerequisites

- Python 3.10+
- Google ADK:  
  ```bash
  pip install google-adk
  ```
- LiteLLM (for local model support):  
  ```bash
  pip install litellm
  ```
- A running local LLM server (e.g., Ollama, LM Studio) or cloud API access
- Access to an LMS backend API (with self-signed cert support)

## Setup

1. Clone or create your project folder:
   ```
   lms_agent/
   ├── agent.py              # Paste the provided code here
   ├── lms.crt               # Your LMS API SSL certificate
   ├── .env                  # Environment variables
   └── requirements.txt
   ```

2. Create `.env` file:
   ```env
   # LLM Configuration
   MODEL_NAME=qwen2.5:7b-instruct          # or your preferred local model
   ENDPOINT_URL=http://localhost:1234/v1    # Ollama/LM Studio endpoint
   PUBLICAI_API_KEY=no-key-needed          # LiteLLM placeholder for local models

   # LMS API Configuration
   LMS_API_URL=https://localhost:7054/api/ # Your LMS backend base URL
   ```

3. Place your LMS SSL certificate as `lms.crt` in the project root.

## Running the Agent

From the parent directory:

- **Interactive Web UI** (recommended):
  ```bash
  adk web
  ```
  Open the browser URL → Select the agent → Start chatting.

- **Command Line**:
  ```bash
  adk run lms_agent
  ```

### Example Queries

- "List all users in the system" → (Requires admin verification)
- "Register a new instructor named John Doe, email john@university.edu, department Computer Science"
- "Create a new course titled 'Introduction to Python' with description 'Beginner-friendly programming course' and assign instructor with email jane@university.edu"
- "Deactivate user with ID 123"

> The agents will ask for verification (name/email/role) before performing sensitive actions.

## Security Notes

- All API calls use certificate-pinned HTTPS (`verify=lms.crt`).
- Agents refuse sensitive operations without proper requester identity verification.
- No user deletion allowed — only deactivation.
- Instructor IDs are never guessed or exposed.

## Customization & Extensions

- Add new tools (e.g., enroll student, upload content).
- Integrate authentication (e.g., session-based user login).
- Deploy to cloud (Render, Railway, Cloud Run) for team access.
- Connect to production LMS with proper certificates.

This system demonstrates a real-world, production-ready pattern for building **secure enterprise AI agents** using ADK.

Perfect for universities, corporate training platforms, or any organization needing an intelligent, policy-compliant LMS assistant.