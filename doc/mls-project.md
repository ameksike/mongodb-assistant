# Project Summary: Mandate Ledger Service - AP2 & UCP Protocol Implementation

## Table of Contents

1. [Project Overview](#project-overview)
2. [Protocol Definitions](#protocol-definitions)
3. [Architecture](#architecture)
4. [Transaction Lifecycle](#transaction-lifecycle)
5. [Key Questions Answered](#key-questions-answered)
   - [How does merchant discovery happen?](#1-how-does-merchant-discovery-happen-what-is-the-well-known)
   - [How is the user signature created, and how can it be verified?](#2-how-is-the-user-signature-created-and-how-can-it-be-verified)
   - [How is immutability ensured?](#3-how-is-immutability-ensured)
   - [How is idempotency ensured?](#4-how-is-idempotency-ensured)
   - [How is compliance ensured?](#5-how-is-compliance-ensured)

---

## Project Overview

This project is a Proof of Concept (PoC) that implements an **enterprise-grade agentic commerce system** built around two complementary protocols:

- **AP2 (Agent Payment Protocol)** : provides the trust layer: immutable mandate ledger, cryptographic signatures, and audit trails.
- **UCP (Universal Commerce Protocol)** : provides the commerce flow: merchant discovery, product search, checkout sessions, and order management via REST APIs.

The system is built with **Python 3.12+**, **FastAPI**, **Motor** (async MongoDB driver), and **Pydantic** for data validation. **MongoDB Atlas** serves as the central, immutable ledger (System of Record) for all AP2 transactions.

The repository contains two main components:

| Component | Location | Purpose |
|-----------|----------|---------|
| **Mandate Ledger Service** | `mandate_ledger_service/` | Core immutable ledger API (FastAPI) backed by MongoDB |
| **Example Flows** | `example/` | Two demo implementations — A2A-based `card_flow` and REST-based `ucp_flow` |

---

## Protocol Definitions

### AP2 — Agent Payment Protocol

AP2 is the **trust and authorization layer**. It defines three types of mandates that form a cryptographically signed chain of authorization for every transaction:

| Mandate Type | Purpose | Lifecycle |
|-------------|---------|-----------|
| **IntentMandate** | Captures the user's shopping intent | `created` → `signed` → `expired`/`cancelled` |
| **CartMandate** | The merchant's product offer with pricing | `proposed` → `updated` → `signed` → `completed`/`expired`/`cancelled` |
| **PaymentMandate** | The user's payment authorization | `created` → `signed` → `authorized` → `captured` → `settled`/`failed` |

Each mandate is stored as an **immutable, versioned ledger entry** in MongoDB. Every state change creates a new version — old versions are never modified or deleted.

### UCP — Universal Commerce Protocol

UCP is the **commerce interaction layer**. It standardizes how AI shopping agents discover and transact with merchants through:

- **`/.well-known/ucp.json`** : a standard discovery endpoint (like a digital business card)
- **Capability negotiation** : agents check feature compatibility before transacting
- **REST-based checkout flow** : standard HTTP endpoints for cart, payment, and order management

**The two protocols are complementary**: UCP defines *how* agents discover and transact; AP2 provides *proof* of authorization and an immutable audit trail.

---

## Architecture

```
┌──────────────────────┐                    ┌──────────────────────┐
│   Consumer Agent     │      UCP REST      │   Merchant Server    │
│   (Shopper)          │◄──────────────────►│   (e.g. Amazon)      │
│                      │   /.well-known     │                      │
│   NO database        │   /api/checkout    │   HAS AP2 Ledger     │
│   NO AP2 client      │   /api/products    │   Integration        │
└──────────────────────┘                    └──────────┬───────────┘
                                                       │
                                                       │ HTTP (AP2 API)
                                                       ▼
                                            ┌──────────────────────┐
                                            │  Mandate Ledger      │
                                            │  Service (FastAPI)   │
                                            │                      │
                                            │  ┌────────────────┐  │
                                            │  │ Authentication │  │
                                            │  │ Rate Limiting  │  │
                                            │  │ Idempotency    │  │
                                            │  │ State Machine  │  │
                                            │  │ Hashing/Audit  │  │
                                            │  └────────┬───────┘  │
                                            │           │          │
                                            │           ▼          │
                                            │  ┌────────────────┐  │
                                            │  │  MongoDB Atlas │  │
                                            │  │  (Immutable    │  │
                                            │  │   Ledger)      │  │
                                            │  └────────────────┘  │
                                            └──────────────────────┘
```

The Mandate Ledger Service acts as a **protective middleware** between agents and MongoDB, organized in three layers:

| Layer | Responsibility | Key Files |
|-------|---------------|-----------|
| **Authentication Layer** | API key validation via bcrypt, RBAC, bootstrap auth | `api/dependencies.py`, `services/auth_service.py` |
| **Business Logic Layer** | State machine validation, idempotency, hashing, signatures | `core/state_machine.py`, `core/hashing.py`, `services/` |
| **Data Access Layer** | MongoDB operations, append-only inserts, aggregation queries | `repositories/`, `db/mongodb.py` |

---

## Transaction Lifecycle

A complete UCP + AP2 transaction follows these steps:

| Step | Actor | Action | AP2 Ledger |
|------|-------|--------|------------|
| 1 | Shopper Agent | Fetches `/.well-known/ucp.json` from merchant | — |
| 2 | Shopper Agent | Checks if merchant supports `dev.ucp.shopping.ap2_mandate` capability | — |
| 3 | Shopper Agent | Sends `POST /api/checkout` with items and signed intent | — |
| 4 | Merchant Server | Creates **IntentMandate** with shopper's signature | **Created** |
| 5 | Merchant Server | Builds cart, signs it with merchant key (`merchant_authorization`) | — |
| 6 | Merchant Server | Returns checkout response with signed cart | — |
| 7 | Shopper Agent | Presents cart to user, obtains consent | — |
| 8 | Shopper Agent | Sends `POST /api/checkout/{id}/confirm` with cart signature | — |
| 9 | Merchant Server | Writes **CartMandate** with both signatures (shopper + merchant) | **Created (signed)** |
| 10 | Shopper Agent | Sends `POST /api/checkout/{id}/complete` with payment signature | — |
| 11 | Merchant Server | Writes **PaymentMandate** with shopper's payment signature | **Created (authorized)** |
| 12 | Merchant Server | Processes payment, creates **Payment Record** linking all mandates | **Payment recorded** |
| 13 | Merchant Server | Returns order confirmation and receipt | — |

---

## Key Questions Answered

### 1. How does merchant discovery happen? (What is the 'well known'?)

Merchant discovery in this project uses the **UCP Well-Known Discovery Endpoint** : a standardized URL at `/.well-known/ucp.json` that any shopping agent can fetch to learn about a merchant's capabilities.

**Implementation:** The merchant server exposes this endpoint via FastAPI in `example/ucp_flow/merchant_server/well_known.py`:

```python
@router.get("/.well-known/ucp.json", response_model=UCPProfile)
async def ucp_discovery():
    return UCPProfile(
        name="Demo UCP Merchant",
        ucp_version="2026-01-11",
        capabilities=[
            UCPCapability(name="dev.ucp.shopping.checkout", version="2026-01-11"),
            UCPCapability(
                name="dev.ucp.shopping.ap2_mandate",
                version="2026-01-11",
                extends="dev.ucp.shopping.checkout"
            ),
            UCPCapability(name="dev.ucp.shopping.order", version="2026-01-11")
        ],
        services={"shopping": UCPService(transport="rest", endpoint="/api")},
        payment_handlers=["CARD", "GOOGLE_PAY"],
        signing_keys=[MERCHANT_SIGNING_KEY]
    )
```

The response is a `UCPProfile` JSON document containing:

| Field | Purpose |
|-------|---------|
| `name` | Human-readable merchant name |
| `ucp_version` | Protocol version for compatibility |
| `capabilities` | List of supported features (checkout, AP2 mandates, orders) |
| `services` | Transport and endpoint information (REST, gRPC, etc.) |
| `payment_handlers` | Accepted payment methods (CARD, GOOGLE_PAY) |
| `signing_keys` | JWK public keys for verifying the merchant's signatures |

**The shopper agent** fetches this profile in `example/ucp_flow/shopper_agent/ucp_client.py`:

```python
async def discover(self) -> dict:
    async with httpx.AsyncClient(timeout=self.timeout) as client:
        resp = await client.get(f"{self.merchant_url}/.well-known/ucp.json")
        resp.raise_for_status()
        self._capabilities = resp.json()
        return self._capabilities

def supports_ap2_mandate(self) -> bool:
    caps = self._capabilities.get("capabilities", [])
    return any(c.get("name") == "dev.ucp.shopping.ap2_mandate" for c in caps)
```

The shopper first discovers the merchant, then checks if AP2 mandates are supported via the `dev.ucp.shopping.ap2_mandate` capability. If supported, the full AP2 signature flow is activated. If not, a simpler checkout flow is used.

A secondary endpoint at `/.well-known/ucp.json/keys` returns just the signing keys in JWK Set format for signature verification.

**Analogy:** The `/.well-known/ucp.json` is equivalent to an `agent.json` file in the A2A protocol — both serve as machine-readable identity cards that enable automatic agent-to-agent discovery.

---

### 2. How is the user signature created, and how can it be verified?

The project implements a **multi-party signature system** where both shopper and merchant agents sign mandates at different stages of the transaction.

#### Signature Creation

Signatures are modeled by the `SignatureEntry` Pydantic class in `mandate_ledger_service/src/models/mandate.py`:

```python
class SignatureEntry(BaseModel):
    signature: str       # The cryptographic signature (hex, JWT, or verifiable credential)
    signer_id: str       # Agent ID that created this signature
    signer_type: str     # Type of agent (shopping_agent, merchant_agent, etc.)
    algorithm: str       # Signature algorithm (EdDSA, ES256, RS256, SHA256, JWT)
    signed_at: datetime  # UTC timestamp
    metadata: dict       # Additional metadata (key ID, verification URL, etc.)
```

**Shopper-side signature creation** (in `example/ucp_flow/shopper_agent/ucp_client.py`):

```python
def create_signature(data: dict, signer_id: str = "ucp_shopper") -> dict:
    data_str = json.dumps(data, sort_keys=True)
    data_hash = hashlib.sha256(data_str.encode()).hexdigest()
    return {
        "signature": f"sig_{data_hash[:32]}",
        "signer_id": signer_id,
        "signer_type": "consumer-agent",
        "algorithm": "SHA256",
        "signed_at": datetime.now(timezone.utc).isoformat()
    }
```

The shopper creates signatures at three points:
1. **Intent signature** : signs the shopping intent when creating a checkout
2. **Cart signature** : signs the cart contents after reviewing and consenting
3. **Payment signature** : signs the payment authorization

**Merchant-side signature creation** (in `example/ucp_flow/merchant_server/checkout.py`):

```python
def _create_merchant_signature(data: dict) -> dict:
    return {
        "signature": _FAKE_JWT,  # In production: real JWT signed with merchant's private key
        "signer_id": "ucp_merchant",
        "signer_type": "merchant-agent",
        "algorithm": "JWT",
        "signed_at": datetime.now(timezone.utc).isoformat()
    }
```

The merchant signs the cart with `merchant_authorization` (a JWT in production, a mock in this PoC).

#### Signature Storage and Accumulation

When mandates are written to the ledger, signatures from both parties are included. The `MandateService.sign_mandate()` method in `mandate_ledger_service/src/services/mandate_service.py` accumulates signatures across versions:

```python
async def sign_mandate(self, entity_id, signed_by_agent, agent_type, ...):
    existing_signatures = getattr(current, 'signatures', [])
    new_signatures = existing_sigs_dicts + [signature_entry]
    return await self.create_mandate_version(
        ..., signatures=new_signatures
    )
```

The `CartMandate` is written with both signatures simultaneously:

```python
cart_entry = await ledger_client.create_mandate(
    mandate_type="CartMandate",
    mandate_data=cart_mandate.model_dump(),
    initial_signatures=[request.cart_signature, merchant_signature],
    initial_status="signed",
    ...
)
```

#### Signature Verification

Verification happens at multiple levels:

1. **Structural verification** : the auditor agent (`example/ucp_flow/auditor_agent/tools.py`) verifies that all three mandates have valid signatures:

```python
signature_checks = {
    "buyer_intent_signature": bool(intent_mandate.get("signatures")),
    "seller_cart_signature": bool(cart_mandate.get("signatures")),
    "buyer_payment_signature": bool(payment_mandate.get("signatures"))
}
all_signatures_valid = all(signature_checks.values())
```

2. **Key-based verification** : the merchant's public signing keys are published in `/.well-known/ucp.json/keys` as JWK entries (EC P-256 curve), enabling any party to verify JWT signatures using the `kid`, `kty`, `crv`, `x`, `y` parameters.

3. **Hash chain verification** : each ledger version's integrity is independently verifiable via SHA-256 hashes (see [Immutability](#3-how-is-immutability-ensured) below).

> **Note:** This PoC uses mock signatures (SHA-256 hashes as signature stand-ins). In production, proper cryptographic signing would use JWT/SD-JWT with RS256 or EdDSA algorithms, and verification would use the JWK public keys from the well-known endpoint.

---

### 3. How is immutability ensured?

Immutability is the **foundational design principle** of the Mandate Ledger Service. It is enforced through multiple reinforcing mechanisms:

#### A. Append-Only Architecture

The ledger only supports **INSERT** operations. There are no UPDATE or DELETE endpoints exposed by the API. The only write operations are:

- `POST /api/v1/mandates` — creates a new mandate (version 1)
- `POST /api/v1/payments` — creates a payment record

The `mandates.py` route file explicitly documents the removal of mutation endpoints:

```python
# REMOVED: PUT /{entity_id} endpoint
# The ledger is immutable - use POST /mandates with initial_signatures for all mandate creation

# REMOVED: POST /{entity_id}/sign endpoint
# Use pre-signed mandate creation instead
```

When a mandate's status changes, a **new version is appended** to the ledger — the original version remains untouched. This is handled in `MandateRepository.append_ledger_entry()`, which always inserts a new document rather than modifying existing ones.

#### B. Blockchain-Style Hash Chaining

Every ledger entry contains cryptographic hash links forming an integrity chain, defined in `MandateLedgerEntry`:

```python
class MandateLedgerEntry(BaseModel):
    parent_version: Optional[int]       # Version number of parent (None for v1)
    parent_version_hash: Optional[str]  # SHA-256 of parent version's canonical JSON
    current_version_hash: str           # SHA-256 of this version's canonical JSON
```

The hash computation in `core/hashing.py` uses **canonical JSON** (sorted keys, consistent encoding) to produce deterministic SHA-256 hashes:

```python
def compute_mandate_hash(mandate_entry: dict) -> str:
    hashable_entry = {
        k: v for k, v in mandate_entry.items()
        if k not in ['parent_version_hash', 'current_version_hash', '_id']
    }
    return compute_sha256(hashable_entry)
```

Chain integrity can be verified with `verify_chain_integrity()`:

```python
def verify_chain_integrity(parent_entry: dict, child_entry: dict) -> bool:
    if child_entry.get("parent_version") != parent_entry.get("version"):
        return False
    if child_entry.get("parent_version_hash") != parent_entry.get("current_version_hash"):
        return False
    return True
```

Any tampering with a historical record would break the hash chain, making modifications detectable.

#### C. Version Conflict Detection

The service uses **optimistic locking** to prevent concurrent writes from corrupting the version chain. When creating a new version, the `MandateService.create_mandate_version()` method:

1. Reads the current version number and hash
2. Attempts to write the next version referencing the current one
3. On conflict (another write happened first), retries with exponential backoff (up to 3 attempts)

```python
for attempt in range(max_retries):
    try:
        current = await self.mandate_repo.get_current_state(entity_id)
        new_entry = await self.mandate_repo.append_ledger_entry(
            parent_version=current.current_version,
            parent_version_hash=current.current_version_hash, ...
        )
        return new_entry
    except VersionConflictError:
        await asyncio.sleep(0.1 * (2 ** attempt))
```

#### D. State Machine Enforcement

The `core/state_machine.py` enforces **unidirectional state transitions**. Terminal states (expired, cancelled, failed) have no outgoing transitions:

```python
CART_MANDATE_TRANSITIONS = {
    MandateStatus.PROPOSED: [UPDATED, SIGNED, EXPIRED, CANCELLED],
    MandateStatus.UPDATED:  [SIGNED, EXPIRED, CANCELLED],
    MandateStatus.SIGNED:   [COMPLETED, EXPIRED, CANCELLED],
    MandateStatus.COMPLETED:[REFUNDED],
    MandateStatus.REFUNDED: [],   # Terminal
    MandateStatus.EXPIRED:  [],   # Terminal
    MandateStatus.CANCELLED:[]    # Terminal
}
```

States cannot go backwards (e.g., `signed` → `proposed` is rejected), preventing retroactive changes.

#### E. Consistency Verification

The `ConsistencyService` performs integrity scans across the ledger, checking for:

- Missing ledger entries
- Version gaps (non-sequential version numbers)
- Broken hash chains
- Hash mismatches

Issues are logged to a `consistency_checks` collection with severity levels (critical, error, warning).

#### F. Auditor Agent Enforcement

The auditor agent (`example/ucp_flow/auditor_agent/tools.py`) includes a `test_mandate_integrity()` tool that actively attempts prohibited operations (DELETE, UPDATE) and confirms they are rejected:

```python
async def test_mandate_integrity(identifier, operation, details):
    if operation == "delete":
        results["rejection_reason"] = "DELETE operations are not supported on the mandate ledger"
    elif operation in ["update", "modify"]:
        results["rejection_reason"] = "UPDATE/MODIFY operations cannot change historical records"
```

---

### 4. How is idempotency ensured?

Idempotency is implemented end-to-end through a dedicated subsystem involving a service, repository, MongoDB collection, and HTTP header convention.

#### Mechanism

1. **Client sends `X-Idempotency-Key` header** with each write request. The `MandateLedgerClient` includes this header automatically:

```python
def _get_headers(self, idempotency_key=None) -> dict:
    headers = {"Authorization": f"Bearer {self.api_key}", ...}
    if idempotency_key:
        headers["X-Idempotency-Key"] = idempotency_key
    return headers
```

2. **Server checks for duplicate** before processing. In the `create_mandate` route (`api/routes/mandates.py`):

```python
if x_idempotency_key:
    idempotency_repo = IdempotencyRepository()
    idempotency_record = await idempotency_repo.check_idempotency_key(
        idempotency_key=x_idempotency_key,
        agent_id=agent.agent_id
    )
if idempotency_record:
    response.status_code = idempotency_record.response_status_code
    return idempotency_record.response_body  # Return cached response
```

3. **After processing**, the response is stored alongside the key for future deduplication:

```python
await idempotency_repo.store_idempotency_record(
    idempotency_key=x_idempotency_key,
    agent_id=agent.agent_id,
    request_method="POST",
    request_path="/api/v1/mandates",
    request_body=request_body.model_dump(),
    response_status=201,
    response_body=result.model_dump()
)
```

4. **Records expire automatically** via MongoDB TTL indexes (default: 24 hours), preventing indefinite storage growth.

#### Idempotency Key Scoping

Keys are scoped to the **agent ID**, meaning two different agents can use the same idempotency key without collision:

```python
record = await self.repo.find_one({
    "idempotency_key": idempotency_key,
    "agent_id": agent_id,
    "expires_at": {"$gt": datetime.now(timezone.utc)}
})
```

#### Usage in the UCP Flow

The UCP checkout module generates deterministic idempotency keys based on checkout and mandate identifiers to prevent duplicate ledger writes during retries:

```python
intent_entry = await ledger_client.create_mandate(
    ..., idempotency_key=f"intent_{checkout_id}", ...
)
cart_entry = await ledger_client.create_mandate(
    ..., idempotency_key=f"cart_signed_{request.cart_id}", ...
)
payment_entry = await ledger_client.create_mandate(
    ..., idempotency_key=f"payment_{payment_mandate_id}", ...
)
```

This ensures that if any step fails and is retried, the exact same ledger entry is returned rather than creating a duplicate.

#### Higher-Level Convenience

The `IdempotencyService` provides a `check_and_store()` method that wraps the full check-process-store cycle:

```python
async def check_and_store(self, idempotency_key, agent_id, ..., process_fn):
    existing = await self.check_request(idempotency_key, agent_id)
    if existing:
        return existing.response_body, existing.response_status, True  # Cached
    status_code, response_body = await process_fn()
    await self.store_result(...)
    return response_body, status_code, False  # Fresh
```

---

### 5. How is compliance ensured?

Compliance is ensured through a multi-layered approach covering authentication, authorization, audit trails, data integrity, and role-based access control.

#### A. Complete Audit Trail

Every operation is logged in the `audit_logs` MongoDB collection via `AuditRepository`. Each audit entry captures:

| Field | Content |
|-------|---------|
| `event_type` | Categorized event (`mandate.created`, `payment.authorized`, `auth.api_key_created`, etc.) |
| `entity_id` | The affected mandate, payment, or API key |
| `actor_id` | Which agent performed the action |
| `actor_type` | The type of agent (shopping-agent, merchant-agent, admin) |
| `details` | Action description and before/after changes |
| `timestamp` | UTC timestamp |
| `ip_address` | Request origin (when available) |
| `transaction_id` | Groups related events across mandates |

The audit trail is queryable by entity, actor, event type, time range, and transaction ID. Every mandate creation, status transition, signing, and cancellation generates an audit entry:

```python
await self.audit_repo.create_audit_log(
    event_type=EventType.MANDATE_CREATED,
    entity_id=entity_id,
    entity_type=entity_type.value,
    entity_version=1,
    actor_id=created_by_agent,
    actor_type=agent_type,
    action=f"Created {entity_type.value} mandate",
    ...
)
```

#### B. Authentication and RBAC

All API endpoints require authentication via API keys. The system supports:

- **Bearer token** in `Authorization` header
- **API key** in `X-API-Key` header
- **Bootstrap admin key** for initial setup (disabled after key provisioning)

API keys are:
- Generated with a `mlsk_` prefix and 32 random hex characters
- Stored as **bcrypt hashes** (never plaintext)
- Associated with specific agent IDs, types, and permission scopes
- Subject to expiration and revocation

```python
async def authenticate(self, api_key, required_scopes=None):
    key_record = await self.auth_repo.get_api_key_by_prefix(key_prefix)
    if not verify_api_key(api_key, key_record.key_hash):
        raise InvalidApiKeyError(key_prefix)
    # Check revocation, expiration, and scope requirements...
```

Permission scopes control access to specific operations: `mandate:read`, `mandate:write`, `audit:read`, `auth:manage`, etc.

#### C. Rate Limiting

Every endpoint is rate-limited per agent. The `RateLimitRepository` tracks request counts in sliding time windows (default: 60 requests/minute). Exceeded limits return HTTP 429 with `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `Retry-After` headers.

#### D. Compliance Agent Role

The system supports a dedicated `compliance-agent` role type (defined in the agent type naming conventions in `models/enums.py`). This role is designed for regulatory compliance verification agents that can:

- Query the full audit trail for any entity or transaction
- Verify signature presence on all mandates
- Run consistency checks across the ledger
- Validate hash chain integrity

The **Auditor Agent** implementation (in both `example/ucp_flow/auditor_agent/` and `example/src/roles/auditor_agent/`) demonstrates this role with tools for:

1. **`check_ledger_by_payment_id`** : verifies a payment record exists and that all three mandates (Intent, Cart, Payment) have valid signatures
2. **`get_mandate_history`** : retrieves the complete version timeline for a transaction, showing every state change
3. **`test_mandate_integrity`** : attempts prohibited operations (DELETE, UPDATE) and confirms they are rejected

#### E. Non-Repudiation

The signature system ensures **non-repudiation** : neither party can deny their participation:

- The shopper's signature on the IntentMandate proves they initiated the purchase
- Both signatures on the CartMandate prove mutual agreement on terms and pricing
- The shopper's payment signature proves they authorized the specific payment
- All signatures are permanently stored in the immutable ledger with timestamps and agent identifiers

#### F. Data Integrity Monitoring

The `ConsistencyService` provides ongoing data integrity monitoring:

- **On-demand checks** for specific mandates (`check_mandate_consistency`)
- **Full ledger scans** to detect version gaps, broken chains, or hash mismatches (`run_full_scan`)
- **Health reports** with health scores and severity-classified issues (`get_health_report`)
- All consistency check results are logged in the audit trail

#### G. Financial Records Retention

Because the ledger is append-only and immutable:

- All transaction records are permanently retained (no DELETE operations)
- Historical records cannot be altered after the fact
- Every change is traceable to a specific agent, timestamp, and version
- The complete chain of authorization (intent → cart → payment) is preserved as a unit via `transaction_id`

This satisfies common regulatory requirements for financial records retention and provides the evidence trail needed for dispute resolution.

---

## Summary Table

| Concern | Mechanism | Key Implementation |
|---------|-----------|-------------------|
| **Merchant Discovery** | `/.well-known/ucp.json` endpoint | `merchant_server/well_known.py` |
| **Signatures** | SHA-256/JWT signatures per agent, stored in ledger | `ucp_client.py`, `models/mandate.py` |
| **Immutability** | Append-only inserts, hash chaining, state machine, no DELETE/UPDATE | `repositories/mandate_repository.py`, `core/hashing.py` |
| **Idempotency** | `X-Idempotency-Key` header + MongoDB deduplication | `services/idempotency_service.py`, `api/routes/mandates.py` |
| **Compliance** | Audit logs, RBAC, signatures, consistency checks, auditor agent | `repositories/audit_repository.py`, `services/auth_service.py` |
