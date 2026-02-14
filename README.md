# AutoCount Intelligent Automation Agent (AIAA)

> **A secure, on-premise AI Chatbot that turns AutoCount Accounting into a conversational partner.**

The **AIAA** is a ChatOps solution designed to interact directly with the **AutoCount Accounting API** via **Telegram**. Unlike standard "Help Bots," this agent is capable of executing real business logic—retrieving live financial data, checking stock levels, and monitoring sales performance—processed securely on your local server.

---

## 📖 Executive Summary

**The Problem:** Managers and sales staff often need quick answers ("Who owes us money?", "Do we have stock of Item X?") while on the move. Accessing this data usually requires logging into an ERP system via a laptop or requesting reports from admin staff.

**The Solution:** An AI-powered agent running locally on the company server. It acts as a bridge between **Telegram** and **AutoCount**, allowing authorized users to query enterprise data using natural language or simple buttons.

**Key Benefits:**
* **Zero Data Leakage:** The AI model (DeepSeek/Llama) and database reside entirely on-premise. No financial data is sent to third-party AI clouds.
* **Instant Access:** Reduces data retrieval time from minutes to seconds.
* **Zero Infrastructure Cost:** Utilizes existing hardware and the free Telegram API (Long Polling) without needing VPNs or static IPs.

---

## 🏗 Architecture

The system operates on a **Unified On-Premise Model**.

```mermaid
graph TD
    User[User (Mobile Telegram)] <-->|Encrypted Chat| TG[Telegram Cloud]
    TG <-->|Long Polling| Bot[Python Bot Service]
    
    subgraph "On-Premise Server (Localhost)"
        Bot -->|Intent Parsing| AI[Ollama (DeepSeek-R1)]
        AI -->|JSON Logic| Bot
        Bot -->|HTTP Requests| API[AutoCount / Freely WebAPI]
        API <-->|SQL Query| DB[(AutoCount SQL DB)]
    end

Tech StackInterface: Telegram MessengerBackend: Python 3.11+AI Engine: Ollama running deepseek-r1:8b (Local Inference)ERP Integration: AutoCount Accounting V2 via Freely WebAPILibraries: python-telegram-bot, ollama, requests, pandas✨ Features1. 📊 Intelligent Sales DashboardDaily Snapshots: Instantly check "Sales Today" or "Sales Yesterday".Performance Tracking: Automatically calculates revenue vs. the previous day.Comparison Logic: Ask "Compare sales for 29 Jan vs 12 Aug" to get a side-by-side analysis.2. 📉 Debtor ManagementTop Debtors: fast retrieval of the top 5 customers with outstanding balances.Customer Lookup: Search for specific customer profiles (Credit Limit, Balance, Contact Info) by name or account code.Command: "Info on debtor Green"3. 📦 Inventory IntelligenceStock Check: Real-time query of item quantity, price, and cost.Catalog Browsing: List available stock items with live quantities.Command: "Check stock for Apple"4. 🧠 Natural Language UnderstandingThe bot doesn't just rely on buttons. It uses a Local LLM to parse natural human intent.User: "Who owes us the most money right now?" -> Bot: Executes list_top_debtors.🚀 Installation & SetupPrerequisitesWindows Server/PC with AutoCount Accounting installed.Freely WebAPI Plugin configured and running (default port 8015).Python 3.11+ installed.Ollama installed for local AI.Step 1: Clone & ConfigureClone the repository and install dependencies:Bashgit clone [https://github.com/your-username/AIAA-Agent.git](https://github.com/your-username/AIAA-Agent.git)
cd AIAA-Agent
pip install -r requirements.txt
Step 2: Environment VariablesCreate a .env file in the AIAA_Core directory:Code snippet# API Configuration
API_BASE_URL=http://localhost:8015
API_USER=ADMIN
API_PASSWORD=your_password
API_TOKEN=your_freely_api_token

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# AI Configuration
OLLAMA_MODEL=deepseek-r1:8b
Step 3: Setup AI ModelEnsure Ollama is running and pull the required model:Bashollama pull deepseek-r1:8b
Step 4: Run the AgentBashpython bot_main.py
You should see logs indicating successful login to AutoCount and connection to Telegram.🤖 Usage GuideOnce the bot is running, open it in Telegram and click Start. You can interact via the Menu Buttons or Text.IntentExample QueryActionCheck Stock"Do we have stock for iPhone?"Returns Qty, Price, Cost, and Item Group.Check Debtor"Details for customer Green"Returns Balance, Credit Limit, and Contact Info.Top Debtors"Who owes us money?"Lists top 5 overdue accounts.Sales Stats"How are sales today?"Returns revenue count and daily comparison.Compare Sales"Compare sales 2026/01/29 vs 2025/08/12"Returns a side-by-side revenue comparison.🗺 Roadmap[x] Phase 1: Connectivity - Basic API connection (Sales, Stock, Debtor).[x] Phase 2: AI Integration - Natural Language Processing with DeepSeek.[ ] Phase 3: Transaction Creation - Ability to generate Invoices/DOs via chat.[ ] Phase 4: Notifications - Proactive alerts for low stock or high overdue debt.[ ] Phase 5: Full API Coverage - Support for every function in the AutoCount API documentation.
