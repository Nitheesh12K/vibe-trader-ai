# Vibe Trading AI — Testing & Verification Strategy

## 1. Overview

Vibe Trading AI features a comprehensive multi-tier automated test suite covering:
- Mathematical indicator precision (13 causal indicators)
- Rule-based candlestick pattern detection (7 patterns)
- 7 pre-configured dynamic algorithmic strategies
- Local Ollama AI provider & deterministic fallback
- Hallucination defense & schema validation
- Zerodha Kite Connect Fail-Closed live order shield (HTTP 403)
- CSV data provider validation & monotonicity
- Risk Guardian deterministic veto
- Mandatory human-in-the-loop buy approval
- Autonomous exit monitor & trailing stops
- Paper trading lifecycle, fees, slippage, and PnL calculation
- In-sample / out-of-sample data splitting
- Paper trading concurrency, stress testing, and mathematical accounting
- API security, input fuzzing, and SQL/traversal injection defense
- Multi-day chronological paper simulation across 10 trading sessions
- Automated portfolio reconciliation audit (zero balance drift)
- React component rendering, navigation, and state interactions

---

## 2. Test Execution Summary

| Test Suite | Framework | Total Tests | Passed | Failed | Duration |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Backend Test Suite** | `pytest` + `fastapi.testclient` | **152** | **152** | 0 | ~42.8s |
| **Frontend Test Suite** | `vitest` + `@testing-library/react` | **15** | **15** | 0 | ~5.8s |
| **TOTAL AUTOMATED TESTS** | | **167** | **167** | **0** | **100% Pass** |

---

## 3. How to Run the Automated Tests

### 3.1 Backend Pytest Suite (152 Tests)
From the repository root:
```powershell
backend\venv\Scripts\python.exe -m pytest tests/backend/ -v
```

### 3.2 Frontend Vitest Suite (15 Tests)
From the `frontend/` directory:
```bash
cd frontend
npm test -- --run
```

### 3.3 Frontend Production Build & Typecheck Verification
From the `frontend/` directory:
```bash
cd frontend
npx tsc --noEmit
npm run build
```

---

## 4. Test Suite Modules & Coverage Breakdown

### 4.1 Core API Endpoints (`tests/backend/test_api.py` - 5 Tests)
- `test_health_endpoint`: Asserts `GET /api/health` returns status 200, version, and database connectivity.
- `test_market_demo_endpoint`: Validates demo portfolio, market statuses (FOREX, NSE, MCX), and demo AI insight.
- `test_market_instruments_filtering`: Confirms market filter parameter functions across all asset classes.
- `test_ohlc_endpoint`: Validates candlestick data integrity, high $\ge$ low boundaries, and non-empty candles.
- `test_database_tables_exist`: Verifies all core SQLite schema tables are properly created on startup.

### 4.2 Autonomous Workflow Tests (`tests/backend/test_autonomous_workflow.py` - 8 Tests)
- Verifies candidate proposal generation, human BUY authorization gate, Risk Guardian vetoes, idempotency protections, and autonomous exit monitoring.

### 4.3 Backtesting Engine Tests (`tests/backend/test_backtesting_engine.py` - 5 Tests)
- Tests dynamic strategy dispatch across `STRATEGY_CATALOG`, fee and slippage calculation, in-sample vs out-of-sample data partitioning, and chronological look-ahead prevention.

### 4.4 Phase 2 CRUD Tests (`tests/backend/test_phase2_crud.py` - 8 Tests)
- Validates SQLite persistence and CRUD lifecycles for watchlist instruments, paper trades, journal entries, and user settings.

### 4.5 Step 3 End-to-End Verification (`tests/backend/test_step3_e2e_verification.py` - 17 Tests)
- Tests 17 end-to-end execution paths including normal trade flow, daily loss breach, emergency stop, position limits, custom CSV import, and trailing stop exits.

### 4.6 Step 4 Agent Execution Optimization (`tests/backend/test_step4_agent_optimization.py` - 14 Tests)
- Proves single-call AI synthesis, zero duplicate background inferences, deterministic agent fleet status reporting, and sub-100ms latency.

### 4.7 Step 5 Algorithm Validation & Robustness (`tests/backend/test_step5_algorithm_validation.py` - 30 Tests)
- Validates mathematical integrity across all 7 strategies individually, chronological execution without future data leakage, deterministic reproducibility down to bitwise precision, and parameter boundary testing.

### 4.8 Step 6 Paper Trading Stress Test (`tests/backend/test_step6_paper_trading_stress.py` - 22 Tests)
- Stress-tests concurrency, partial fills, broker failures, database crash recovery, exposure limits, and mathematical accounting correctness.

### 4.9 Step 7 Security & Production Audit (`tests/backend/test_step7_security_audit.py` - 22 Tests)
- Fuzzing against SQL injection, directory traversal, CSV formula injection, AI prompt injection, unauthorized approvals, and strict fail-closed enforcement of `POST /api/broker/zerodha/orders` (`HTTP 403`).

### 4.10 Step 8 Multi-Day Paper Trading Simulation (`tests/backend/test_step8_multiday_paper_trading.py` - 8 Tests)
- Ingests validated historical NSE datasets (`RELIANCE`, `TATASTEEL`), executes 10 sequential chronological trading sessions, exercises adverse conditions (stale data, gaps, daily loss limit, crash recovery), and runs final automated portfolio reconciliation.

### 4.11 Technical Indicators & Patterns (`tests/backend/test_technical_analysis.py` - 4 Tests)
- Validates mathematical formulas for 13 technical indicators, 7 candlestick patterns, and support/resistance cluster calculations.

### 4.12 Vibe Intelligence Core (`tests/backend/test_vibe_intelligence_core.py` - 9 Tests)
- Tests the 8 individual agent responsibilities, memory recall, strategy adaptation lifecycles, and outcome evaluation attribution.

### 4.13 Frontend UI Suite (`frontend/src/App.test.tsx` - 15 Tests)
- Validates terminal layout rendering, sidebar tab navigation, demo mode badges, health status indicators, chart controls, and modal dialogs.
