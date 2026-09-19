# Fear-Free Family Truth Companion

> **Tagline:** *Understand your loan. Involve your family. Decide with confidence.*

A consent-first financial clarity platform focused initially on Indian home loans. The application empowers borrowers to interpret complex loan offers in plain language, uncover hidden and conditional charges, evaluate loan website security through server-side request forgery (SSRF) protected scanners, simulate repayment scenarios, and selectively share reports with trusted family members.

---

## 1. Core Principles & Truth Guarantees

- **Zero Sales Pressure:** The platform never sells mortgages, ranks sponsored financial products, or refers users to lenders for referral commissions.
- **No Guaranteed Safety Claims:** The application never declares that a loan, website, or lender is "100% safe" or "guaranteed legitimate".
- **Local AI Inference:** Document analysis and clause explanations are executed locally using Ollama (`qwen2.5:7b`). No customer data is sent to external paid AI APIs.
- **Deterministic Math:** All financial calculations (reducing balance EMI, amortization, rate shifts) run in Python using `Decimal`, never through LLM hallucinations.
- **Exact Quote Verification:** Every supporting quote is programmatically matched against verbatim source text.
- **Consent-First Family Circle:** Report sharing is explicit, revocable, and defaults to all fields being private. Unshared fields and raw documents are redacted on the backend before data leaves the server.

---

## 2. Architecture & Technology Stack

```
fear-free-companion/
├── frontend/               # Next.js 14 App Router, TypeScript, Tailwind CSS, TanStack Query, Recharts, Lucide
│   ├── app/                # Dashboard, Analyze, Check-Link, Calculator, Family Circle, Reports, Privacy
│   ├── components/         # Reusable UI cards, EvidenceModal, ShareDialog, QuestionPanel, Charts
│   ├── lib/                # API client with same-origin proxy, Indian currency formatting
│   └── types/              # Strict TypeScript interfaces matching backend models
├── backend/                # Python 3.11+ FastAPI application
│   ├── app/
│   │   ├── main.py         # FastAPI entrypoint, lifespan, CORS, rate limiting, error sanitization
│   │   ├── api/v1/         # Modular routers (auth, documents, analyses, url_checks, jobs, calculations, family, reports, privacy)
│   │   ├── core/           # Argon2id auth, opaque sessions, CSRF protection, structured logging
│   │   ├── db/             # PyMongo AsyncMongoClient with automatic index assurance
│   │   ├── schemas/        # Pydantic v2 schemas for all requests, responses, and terms
│   │   ├── services/       # OCR, SSRF fetcher, rule engines, Ollama client, PDF exporter
│   │   └── workers/        # MongoDB-backed background queue worker with atomic leases
│   └── tests/              # Pytest suite (calculations, SSRF, auth, redaction, quote matching)
├── fixtures/               # Synthetic test documents (PDF, DOCX) and website JSON mocks
├── infra/                  # Docker Compose, Dockerfiles, and Ollama setup scripts
├── .env.example
└── README.md
```

---

## 3. Realistic Hardware & Software Requirements

- **Operating System:** Windows 10/11, macOS, or Linux
- **Python:** 3.11 or 3.12+ (Python 3.13 tested)
- **Node.js:** v18, v20, or v22+ with `npm`
- **Tesseract OCR:** Optional for local development; packaged inside Docker container for scanned image OCR.
- **Ollama:** Required for local LLM inference.
  - *Hardware Consideration for `qwen2.5:7b`:* Minimum 8 GB RAM (16 GB recommended) or 6 GB+ VRAM on Apple Silicon or NVIDIA GPU.
  - *Offline Fallback:* If Ollama is not installed or offline, the platform automatically runs in deterministic rules mode and displays *"AI explanation unavailable"*.

---

## 4. Environment Configuration

Copy `.env.example` to `.env` in the project root:

```bash
cp .env.example .env
```

Key environment variables:
| Variable | Description | Default |
| :--- | :--- | :--- |
| `APP_ENV` | Environment (`development`, `production`, `test`) | `development` |
| `APP_BASE_URL` | Frontend origin for CORS and invitation links | `http://localhost:3000` |
| `MONGODB_URI` | MongoDB connection URI | `mongodb://localhost:27017` |
| `MONGODB_DATABASE` | Database name | `fear_free_companion` |
| `OLLAMA_BASE_URL` | Local Ollama endpoint | `http://localhost:11434` |
| `OLLAMA_MODEL` | Local LLM model identifier | `qwen2.5:7b` |
| `UPLOAD_DIRECTORY` | Private isolated storage for uploaded files | `./data/uploads` |
| `COOKIE_SECURE` | Set `true` in production with HTTPS | `false` |
| `CSRF_SECRET` | Secret key for CSRF token generation (min 32 chars) | `(see .env.example)` |
| `SMTP_HOST` | Mail host for invitation delivery | `localhost` |

---

## 5. Local Setup & Installation

### Step 1: Clone and Set Up Python Virtual Environment
```bash
cd fear-free-companion
python -m venv venv

# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install --upgrade pip
pip install -r backend/requirements.txt
```

### Step 2: Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### Step 3: Start MongoDB
Ensure MongoDB is running locally on port `27017`:
```bash
# If using local MongoDB service
mongod --dbpath ./data/db
```
*(Or use Docker Compose as described in Section 6).*

### Step 4: Configure Local Ollama & Download Model
1. Install Ollama from [ollama.com](https://ollama.com).
2. Start the Ollama server:
   ```bash
   ollama serve
   ```
3. In a separate terminal, pull the configured model:
   ```bash
   ollama pull qwen2.5:7b
   ```
   *(The backend also works seamlessly if Ollama is paused; deterministic extraction and fee rules remain fully operational).*

### Step 5: Start the Backend & Worker
In the `backend` directory with virtual environment activated:
```bash
# Terminal 1: Backend API
cd backend
uvicorn app.main:app --reload --port 8000
```

```bash
# Terminal 2: Background Job Worker (Optional if embedded worker is active)
cd backend
python -m app.workers.run_worker
```

### Step 6: Start the Frontend
In the `frontend` directory:
```bash
cd frontend
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 6. Deployment with Docker Compose

To launch the full stack (Frontend, Backend, Worker, MongoDB, Ollama, and Mailpit) via Docker:

```bash
cd infra
docker compose up -d
```

### Pull Ollama Model in Docker:
```bash
# Execute the model-pull helper
docker compose exec ollama ollama pull qwen2.5:7b
```

### Access Services:
- **Frontend Dashboard:** [http://localhost:3000](http://localhost:3000)
- **FastAPI OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Mailpit Email Testing Web UI:** [http://localhost:8025](http://localhost:8025)

---

## 7. Verifying Service Readiness & Health

Check the unauthenticated health endpoints:
```bash
# Liveness
curl http://localhost:8000/api/v1/health/live
# {"status":"alive"}

# Readiness (Discloses dependency states without leaking network internals)
curl http://localhost:8000/api/v1/health/ready
# {"status":"ready","database":"available","local_llm":"available"}
```

---

## 8. Running Automated Tests

### Backend Unit & Integration Tests:
```bash
cd backend
pytest -v
```
All 16 test suites verify:
- Exact reducing-balance EMI calculations and zero-interest loans
- Financed fees vs upfront fees vs disbursement deductions
- Missing values remaining `not_found` rather than defaulting to zero
- Conflicting interest rate detection
- Verbatim quote validation against extracted document text
- Magic byte validation rejecting renamed executables
- SSRF protections (blocking loopback, private RFC1918, cloud metadata `169.254.169.254`, non-standard ports)
- Official regulatory source corroboration and domain unverified warnings
- Argon2id password hashing and session token SHA-256 storage
- CSRF token validation and rate limiting
- Consent-first backend redaction of unshared amounts and quotes

---

## 9. Loading Synthetic Demo Data

Synthetic loan documents and website JSON fixtures are pre-packaged in `fixtures/`:
1. **Standard Home Loan (`1_standard_home_loan.pdf`):** ₹40,00,000 sanctioned amount, 8.5% p.a., 240 months, 0.5% upfront fee.
2. **Additional Charges Loan (`2_additional_charges_loan.docx`):** Administrative fee, technical valuation charge, bundled insurance policy, and penal bounce fees.
3. **Conflicting Terms Loan (`3_conflicting_terms_loan.pdf`):** Section 2 specifies 8.75% while Section 8 states 9.25%.
4. **Scanned Degraded Document (`4_scanned_degraded_document.pdf`):** Faded scan demonstrating OCR quality disclosures.
5. **Suspicious Website Fixture (`5_suspicious_website.json`):** Advance fee demand, "100% guaranteed approval without CIBIL", and password solicitation.
6. **Incomplete Website Fixture (`6_incomplete_website.json`):** Unverified regulatory registry status.

You can load these fixtures directly from the **Analyze Document** and **Check Loan Link** pages with one click.

---

## 10. Data Deletion & Privacy Workflows

Users maintain sovereign control over their records:
- **Individual Documents:** Deleting an uploaded document immediately wipes the private file from disk, deletes text chunks from MongoDB, and cascades to delete associated analyses and family shares.
- **Account Deletion:** Navigate to **Privacy & Settings** -> **Delete My Account & All Data**. This permanently revokes active sessions, deletes all owned files, purges database records, and invalidates all family sharing links.

---

## 11. Implemented Integrations vs. Intentional Limitations

### Fully Implemented:
- **FastAPI Backend & Next.js App Router Frontend** with complete bidirectional REST integration.
- **SSRF Hardening:** DNS address resolution, RFC 1918 / cloud metadata blocking, port restriction (80/443), redirect limits (max 3), and SNI verification to prevent DNS rebinding.
- **Argon2id Authentication & CSRF Protection** with HttpOnly SameSite session cookies.
- **Decimal Calculation Engine:** EMI, total outflow, net disbursement, +1% / +2% rate sensitivity scenarios, and complete amortization schedule.
- **Consent-First Redaction:** Backend strips unpermitted fields before returning JSON or PDF exports.
- **Server-Side PDF Export:** Styled PDF generation with ReportLab.
- **Report-Scoped Q&A:** Answers questions strictly bounded by accessible evidence.

### Intentionally Limited & Documented:
- **Official Source Scope:** Registry corroboration is currently configured for Scheduled Commercial Banks and major Public HFCs in India. Unlisted entities show *"Entity match uncertain"* or *"Not checked"* rather than inventing verification.
- **Floating Rate Resets:** Rate scenario comparisons hold tenure constant and explicitly disclose this assumption, as actual lender reset policies vary.
- **Password-Protected PDFs:** The platform does not attempt to break PDF passwords, providing clear instructions for borrowers to save an unlocked copy before uploading.

---

## 12. Security & Production-Hardening Checklist

Prior to production deployment:
1. Set `APP_ENV=production`.
2. Set `COOKIE_SECURE=true` and terminate TLS at your reverse proxy (e.g. NGINX or AWS ALB).
3. Generate a cryptographically random `CSRF_SECRET` (at least 32 characters).
4. Do not publish MongoDB or Ollama ports publicly to the internet.
5. Mount persistent storage volumes with filesystem-level encryption (e.g., LUKS or AWS EBS encryption).
6. Configure SMTP credentials for transactional invitation emails.
