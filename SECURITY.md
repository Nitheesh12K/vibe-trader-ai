# Vibe Trading AI — Security & Safety Architecture

## 1. Safety Philosophy: Fail-Closed Protection

Financial trading software requires an uncompromising security baseline. In **Vibe Trading AI**, safety is enforced by **Fail-Closed Design**:

> If any component fails, credentials expire, inputs are malformed, or ambiguous orders are received, the system halts execution rather than proceeding under uncertain assumptions.

---

## 2. Broker Connection Guardrails (Zerodha Kite Connect Free)

### 2.1 The Fail-Closed Live Order Barrier
The platform integrates with **Zerodha Kite Connect Personal (Free)** exclusively for:
1. User identity and profile validation
2. Account binding
3. Margin surveillance

**Live broker order placement is strictly blocked at the API gateway**:
- Endpoint: `POST /api/broker/zerodha/orders`
- Status: **HTTP 403 Forbidden**
- Payload:
  ```json
  {
    "detail": "Live broker order execution is strictly disabled (Fail-Closed Safety Policy). Use Paper Trading Engine."
  }
  ```
- **Audit Logging**: Every invocation of this endpoint writes a warning log into the SQLite `AuditLog` table with UTC timestamp, remote IP, and requested parameters.

### 2.2 Broker Credential Management
- API Keys and Secrets are read exclusively from environment variables (`ZERODHA_API_KEY`, `ZERODHA_API_SECRET`).
- Credentials are **never** logged to disk, serialized in client responses, or transmitted to external AI endpoints.
- If credentials are unset or invalid, the backend falls back safely to simulated demo identity without raising fatal runtime crashes.

---

## 3. Autonomous Execution Guardrails & Risk Controls

### 3.1 Strict Prohibition of Autonomous BUY Orders
- **Zero Autonomous BUYs**: Under no circumstances can AI models, strategies, or background loops autonomously execute a BUY order.
- **Mandatory Human-in-the-Loop**: Every algorithmic candidate is posted as a `BuyProposal` in status `PENDING`. Only explicit human authorization via `POST /api/proposals/{id}/approve` can trigger order execution in the Paper Trading Engine.

### 3.2 Autonomous SELL Permissions (Guarded Exits)
- Autonomous exits are permitted **only for risk mitigation** (Stop Loss, Take Profit, Trailing Stop) on existing open positions.
- Users can disable autonomous exits at any time via the `AutonomousExitPermission` control panel, reverting exits to manual user approval.

### 3.3 Risk Guardian Deterministic Veto
Before any paper order executes, it passes through the `RiskGuardian` service:
1. **Capital Check**: Verifies trade risk does not exceed `max_risk_per_trade_pct` (default 0.5%, or ₹10.00 on ₹2,000 balance).
2. **Open Positions**: Enforces max position concurrency (default 1).
3. **Daily Loss Limit**: Halts all trading if cumulative daily loss exceeds ₹40.00.
4. **Emergency Stop**: Global kill-switch halts all trading operations immediately if activated.

---

## 4. AI Hallucination Defense & Evidence Grounding

1. **Strict Pydantic Encoders**: LLM inference is constrained by typed Pydantic models. Malformed JSON or non-conforming structures are instantly rejected.
2. **Grounded Verification**: The AI output validator checks that all technical claims (e.g., "EMA 9 is above EMA 21") match the actual computed numerical arrays.
3. **Deterministic Fallback**: If local Ollama is offline or generates hallucinated claims, the platform automatically switches to rule-based deterministic rationale.

---

## 5. Tamper-Evident Audit Logging

All system events are logged to the `audit_logs` table in SQLite:
- Proposal creations, approvals, and rejections
- Virtual paper trade entries, exits, slippage, and PnL
- Emergency stop activations and deactivations
- Live broker barrier triggers and blocked order attempts

All audit records include:
- `timestamp`: UTC ISO 8601
- `action`: Categorical event code
- `entity_type` & `entity_id`: Target resource identifier
- `details`: Structured JSON snapshot of context and payload
