# 🧩 Ability: Store Project on Odoo (Microservice)

**Technical ID:** `StoreProjectOnOdoo` (formerly Donna)

This Azure Function serves as a specific **ability** (skill) within the larger AI Assistant ecosystem. Its sole purpose is to execute the "storage" of a project into the Odoo ERP system, handling all the necessary data transformation and API handshakes.

---

## 🤝 Role in AI Teammate Ecosystem
Your AI Assistant (Teammate) calls this microservice when it decides a project needs to be created.
*   **Trigger:** JSON payload from the AI Assistant (or Logic App).
*   **Action:** Stores the project, tags, and files in Odoo.
*   **Output:** Returns the Odoo Task ID to the Assistant.

---

## 🚀 Mission
To provide a reliable, intelligent API endpoint for storing project requests in Odoo. It acts as the "Odoo Connector" skill.

---

## 🧠 Core Capabilities

### 1. **Intelligent Triage & Classification**
Donna analyzes incoming emails and attachments to determine the nature of the request:
*   **Interface Projects**: Logistics data mapping, Excel conversions, innovative interfaces.
*   **Automation Projects**: Scripts, API integrations, workflows, scheduled tasks.
*   **Strategy Selection**: Automatically decides whether to process based on email text, PDF content (using OCR/Vision), or Excel structural analysis.

### 2. **Smart Extraction (OpenAI Integrated)**
Using advanced LLMs (GPT-4o), Donna extracts critical metadata:
*   **Client Identification**: (e.g., Bleckman, Umicore).
*   **Flow Type**: (e.g., "Import Release", "Packing List Interface").
*   **Technical Specs**: Suggests naming conventions for Logic Apps and Azure Functions (`la-dkm-client-flow`, `func-dkm-client`).
*   **Keywords & Priority**: Detects urgency and relevant search terms.

### 3. **Structured Odoo Task Creation**
Donna talks directly to the Odoo ERP via XML-RPC:
*   **Project Routing**: Places task in the correct Odoo Project ("Interface" or "Automation").
*   **Dynamic Tagging**: Applies strict tags for quick filtering:
    *   `INTERFACE` or `AUTOMATION`
    *   Subsidiary: `VanPoppel`, `Vermaas`, or defaults to `DKM`.
*   **Rich HTML Descriptions**: format descriptions with tables containing:
    *   Email Metadata (Sender, Time).
    *   Data Flow Diagram (Input → Process → Output).
    *   Technical Setup placehodlers.

### 4. **Automated Setup**
*   **Standard Sub-Tasks**: Instantly creates a "Definition of Done" checklist (e.g., "Create Logic App", "Test", "Deploy").
*   **Attachment Handling**: Decodes and uploads email attachments (PDF/Excel) directly to the Odoo task.

---

## 🛠️ Workflow Architecture

```mermaid
graph TD
    A[Incoming Email via Logic App] -->|JSON Payload| B(Donna Azure Function)
    
    subgraph "Donna Brain 🧠"
        B --> C{Attachment Analyzer}
        C -->|PDFs| D[PDF Processor (Assistants API)]
        C -->|Excel/None| E[Text Processor (GPT-4o)]
        
        D & E --> F[Context Builder]
        F --> G[Project Classifier]
    end
    
    subgraph "Execution ⚙️"
        G -->|Interface| H[Interface Handler]
        G -->|Automation| I[Automation Handler]
        
        H & I --> J[Odoo Project Service]
    end
    
    subgraph "Odoo ERP 📦"
        J --> K[Create Main Task]
        J --> L[Set Tags & Priority]
        J --> M[Create Sub-Tasks]
        J --> N[Upload Attachments]
    end
```

---

## 📂 Project Structure

```
Donna/
├── __init__.py          # Azure Function Entry Point
├── config.py            # Credentials & Configuration
├── core/                # Brain & Routing Logic
│   ├── brain.py         # The Orchestrator
│   └── router.py        # Handler Selection
├── ai/                  # Intelligence Layer
│   ├── prompts.py       # Centralized Prompt Management
│   └── text_processor.py
├── openai_api/          # OpenAI Wrappers
│   ├── custom_call.py   # Text Chat
│   └── custom_call_with_pdf.py # Assistants API
├── handlers/            # Business Logic
│   ├── interface_handler.py
│   └── automation_handler.py
├── odoo/                # Odoo Integration
│   ├── client.py        # XML-RPC Client
│   └── project_service.py # CRUD Operations
└── schema/              # Data Models
    ├── email_payload.py
    └── odoo_fields.py
```

---

## 🔍 Example Output

**Task:** `Bleckman – Interface for Packing Lists`  
**Project:** `Interface`  
**Tags:** `INTERFACE`, `DKM`

**Description:**
> **Develop a new interface for Bleckman's packing lists...**
>
> **Technical Setup**
> *   Logic App: `la-dkm-bleckman-interface`
> *   Function: `func-dkm-bleckman`
>
> **Data Flow**
> *   Input: Email (PDF/Excel)
> *   Output: Custom XML
>
> **Sub-Tasks**
> *   [ ] Create Logic App
> *   [ ] Create Azure Function
>   ...

---

## 🔐 Security & Tech Stack
*   **Language**: Python 3.10+
*   **Host**: Azure Functions (Consumption Plan)
*   **AI**: OpenAI GPT-4o, OpenAI Assistants API
*   **Secrets**: Azure Key Vault (Managed Identity)
*   **Integration**: Odoo XML-RPC
