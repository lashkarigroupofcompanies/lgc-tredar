# LGC Trading — Autonomous Multi-Asset Multi-Agent Quant Engine & Hacker Desk

An institutional-grade, multi-agent algorithmic trading and intelligence platform. Built with Python 3.12 (FastAPI), TypeScript, and Vite. Features autonomous paper trading, multi-tier profit harvesting, continuous neural learning, and a dark cyber Hacker Desk workstation.

---

## 🏛️ System Architecture

The platform operates on a decentralized multi-agent hierarchy coordinated through a shared memory bus and an inter-market correlation nexus:

1. **👑 CEO Agent (`agents/ceo_agent`)**:
   - Supreme consensus orchestrator. Synthesizes inputs from analytical, risk, and news agents before approving any trade. Holds final veto authority.
2. **📈 Analytical Agent (`agents/analytical_agent`)**:
   - Multi-timeframe price action analysis, SMC/ICT liquidity sweeps, order blocks, FVG (fair value gaps), Wyckoff spring/upthrust detection, and technical indicator matrices.
3. **🧪 Strategy R&D Agent (`agents/strategy_rnd`)**:
   - Generates, backtests, and mutates strategies based on market regime changes. Performs counterfactual analysis on both taken and rejected trades.
4. **⚡ Execution Agent (`agents/execution_agent`)**:
   - Paper-trading execution engine with simulated slippage, spread, and commissions.
   - **3-Tier Exit Harvesting**:
     - TP1: Partial scaling at $+1.0R$ with Stop Loss moved to Breakeven.
     - TP2: Profit taking at $+2.0R$.
     - Runner: Chandelier / ATR trailing stop for riding multi-day trends.
   - **Early-Cut Defense**: Terminates stagnant or deteriorating setups on bar 1–2 before full SL is hit.
5. **🛡️ Risk Agent (`agents/risk_agent`)**:
   - Autonomous dynamic position sizing, portfolio heat monitoring, streak-based size scaling (cutting size after consecutive losses), and daily drawdown circuit breakers.
6. **🌐 News & Macro Intelligence Agent (`agents/news_agent`)**:
   - Geopolitical event monitoring (GDELT, World Monitor feeds) and news-buffered execution guards to prevent entry ahead of high-impact releases.
7. **🧠 Shared Brain & Neural Memory (`shared_brain`, `agents/evolution_memory`)**:
   - Long-term memory ledger that records win/loss reflections, counterfactual learning, and continuous parameter optimization over thousands of trades.
8. **🤖 Universal LLM Brain (`shared_brain/llm_brain.py`)**:
   - Dynamic multi-provider AI engine supporting 12+ providers:
     - **Google Gemini** (Gemini 2.5 Flash / 2.5 Pro)
     - **Anthropic Claude** (Claude 3.7 Sonnet / 3.5 Sonnet)
     - **OpenAI** (GPT-4.5 Preview / o3-mini / o1 / GPT-4o)
     - **DeepSeek Direct** (DeepSeek-R1 / DeepSeek-V3)
     - **Groq Ultra-Fast LPU** (DeepSeek-R1 Distill / Llama 3.3 70B)
     - **Perplexity AI** (Sonar Deep Research / Sonar Pro)
     - **Together AI**, **OpenRouter**, **NVIDIA NIM**, **Mistral**, **Ollama** (Local 0-cost), and **Custom Endpoints**.
   - Auto-detects provider and latest flagship model from API key prefix.

---

## 🖥️ Hacker Desk User Interface (`ui/`)

- **Overview & Live P&L**: Real-time equity curve, active positions, floating P&L, win rates, and interactive candlestick charts.
- **🎯 Executed Trades Lab**: Open-ended milestone tracker (100 $\rightarrow$ 500 $\rightarrow$ 1,000+ trades) displaying only verified, filled, and closed trades with exit breakdown (TP1, TP2, trailing runner, early cuts).
- **🤖 LLM Configuration**: In-app model switcher with one-click flagship preset chips, custom model name typing, and masked key storage.
- **🛡️ Risk Dashboard & Agent Health**: Live drawdown gauges, VaR (95%), margin utilization, and real-time agent status monitors.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Node.js 18+ & npm

### 1. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the multi-agent backend server
python -B server.py
```
The FastAPI server will start on `http://localhost:8000`.

### 2. Frontend Setup
```bash
# Navigate to UI directory
cd ui

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Open **`http://localhost:5173/desktop.html`** or **`http://localhost:5173`** in your browser.

---

## ⚙️ Configuration

- Copy `.env.example` to `.env` if using custom environment variables.
- Or configure your API keys and models directly inside the Hacker Desk UI under the **`[ 🤖 LLM AI Models & API Keys ]`** tab.

---

## 📜 License
Private and Confidential. All rights reserved.
