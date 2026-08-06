# IntelliView Orchestrator — Intern Task Assignment
### Project: AI-Powered Interview System | Total Interns: 127

---

## 📌 Section A: Bugs Fixed (What Stabilized the System)

These are the **real bugs we fixed** during this session to make the system runnable:

| # | Bug | Root Cause | Fix Applied |
|---|-----|-----------|-------------|
| 1 | **Worker heartbeat 429 Too Many Requests** | No rate-limit exception for internal worker routes | Added worker whitelist to rate limiter |
| 2 | **POST /start-interview → 401 Unauthorized** | `API_TOKEN` env var was blank in Docker Compose (no default) | Added `${API_TOKEN:-dev-token-change-me}` fallback in `docker-compose.yml` |
| 3 | **Bearer token rejected even when correct** | `security.py` only decoded JWT; plain static tokens were rejected | Added fallback: if JWT decode fails, compare against `API_TOKEN` |
| 4 | **Interview page completely unclickable** | Invisible `position: absolute; inset: 0` overlay in `page.jsx` had no `relative` parent, stretching to cover the entire viewport | Added `relative overflow-hidden` to the parent container in `interview/page.jsx` |
| 5 | **POST /start-interview → 500 ForeignKeyViolation** | `interview_sessions.candidate_id` FK required candidate to exist first; UI never created one | Auto-create placeholder candidate in `session_manager.create_session()` if not found |
| 6 | **GET /scheduling-status → 500 AttributeError** | `LoadBalancer` class was missing `get_load_status()` method | Implemented `get_load_status()` in `orchestrator/load_balancer.py` |
| 7 | **Worker entrypoint crash on startup** | Thread exception in heartbeat loop due to missing exception handling | Investigated and traced thread crash |

---

## 🚀 Section B: Feature Roadmap (What to Build Next)

Below are **32 feature tasks** organized into teams. Each task is self-contained with clear deliverables.

---

## 👥 TEAM 1 — Authentication & Security (10 Interns)
> Lead: Assign a senior intern as team lead

### Task 1.1 — JWT Login Page (3 interns)
**Interns:** 1, 2, 3

**Goal:** Build a proper login system so users must authenticate before accessing the dashboard.

**What to do:**
- Create a `/login` page in `frontend/src/app/login/`
- Add a form with Email + Password fields
- On submit, call `POST /auth/login` and store the returned JWT token in `localStorage`
- Redirect to dashboard on success
- Show error message on failure

**Backend:** Create `POST /auth/login` endpoint in `orchestrator/routers/auth.py` that validates credentials against the `users` table and returns a JWT.

**Files to modify:**
- `frontend/src/app/login/page.jsx` (NEW)
- `orchestrator/routers/auth.py` (NEW)
- `orchestrator/security.py` (MODIFY — wire JWT generation)

**Definition of Done:** User can log in with email/password, gets redirected to dashboard, and all API calls use the JWT.

---

### Task 1.2 — Role-Based Access Control (2 interns)
**Interns:** 4, 5

**Goal:** Different users should see different parts of the system (Admin, HR, Interviewer, Viewer).

**What to do:**
- Add a `role` field to the `User` model in `database/models.py`
- Implement `require_role(["admin", "hr"])` dependency in `orchestrator/security.py`
- In the frontend sidebar, hide menu items based on user role
- Admin sees everything; HR sees candidates/sessions; Viewer is read-only

**Files to modify:**
- `database/models.py`
- `orchestrator/security.py`
- `frontend/src/components/Sidebar.jsx`

**Definition of Done:** Admin and HR accounts see different menus; unauthorized routes return 403.

---

### Task 1.3 — User Management Page (3 interns)
**Interns:** 6, 7, 8

**Goal:** Admins need to create/edit/delete user accounts from a UI.

**What to do:**
- Create `frontend/src/app/users/page.jsx` with a table of all users
- Add Create User modal (name, email, password, role)
- Add Edit and Delete buttons
- Wire to backend CRUD endpoints: `GET/POST/PUT/DELETE /users`

**Files to create:**
- `frontend/src/app/users/page.jsx`
- `routers/users.py`

**Definition of Done:** Admin can create a new HR user from the UI, who can then log in.

---

### Task 1.4 — Audit Log Viewer (2 interns)
**Interns:** 9, 10

**Goal:** Show a log of all important actions (who started what interview, who changed settings).

**What to do:**
- Create `database/models.py` → `AuditLog` table (user, action, timestamp, details JSON)
- Write a middleware in `orchestrator/main.py` that logs every non-GET API call to this table
- Create `frontend/src/app/audit/page.jsx` showing a filterable table of audit events

**Definition of Done:** Every time an interview starts, it shows up in the audit log with the user's email and timestamp.

---

## 👥 TEAM 2 — Candidate Management (12 Interns)

### Task 2.1 — Candidate Registration Form (3 interns)
**Interns:** 11, 12, 13

**Goal:** HR should be able to register candidates before scheduling an interview.

**What to do:**
- Create `frontend/src/app/candidates/new/page.jsx` with fields: Name, Email, Phone, Position Applied For, Resume Upload
- Wire to `POST /candidates` endpoint
- Add client-side validation (email format, required fields)

**Definition of Done:** HR fills the form and candidate appears in the Candidates list page.

---

### Task 2.2 — Resume Parser Integration (3 interns)
**Interns:** 14, 15, 16

**Goal:** When HR uploads a resume PDF, automatically extract skills and experience.

**What to do:**
- In `cv_service/`, build a `/parse-resume` endpoint that accepts a PDF file
- Use `pdfminer` or `pypdf2` to extract text
- Use regex or a simple NLP approach to extract: Skills list, Education, Work experience years
- Store extracted data in `Candidate.resume_text` and `Candidate.skills` JSON fields
- Show parsed skills as tags on the candidate profile page

**Files to modify:**
- `cv_service/main.py`
- `frontend/src/app/candidates/[id]/page.jsx`

**Definition of Done:** Upload a PDF resume → Skills are automatically populated.

---

### Task 2.3 — Candidate Profile Page (2 interns)
**Interns:** 17, 18

**Goal:** A detailed page showing a candidate's full profile, interview history, and scores.

**What to do:**
- Create `frontend/src/app/candidates/[id]/page.jsx`
- Show: Name, Email, Skills (as tags), Resume text, Interview history table
- Interview history table: session_id, date, status, score, risk level
- Add a "Schedule Interview" button that navigates to `/interview` with this candidate pre-filled

**Definition of Done:** Clicking a candidate in the list opens their full profile.

---

### Task 2.4 — Bulk Candidate Import (2 interns)
**Interns:** 19, 20

**Goal:** Import 50+ candidates at once via CSV upload.

**What to do:**
- Create a "Import CSV" button on the Candidates page
- Accept CSV with columns: name, email, position, phone
- Validate each row and show errors for invalid rows
- Create backend `POST /candidates/bulk` that batch-inserts validated rows

**Definition of Done:** Upload a 50-row CSV → 50 candidates appear in the list.

---

### Task 2.5 — Candidate Search & Filtering (2 interns)
**Interns:** 21, 22

**Goal:** HR should be able to search and filter the candidates list.

**What to do:**
- Add search bar (searches name + email)
- Add filter dropdowns: Position, Date Range, Skills
- Wire to backend `GET /candidates?search=&position=&skill=`
- Add pagination (20 candidates per page)

**Definition of Done:** Searching "John" shows only candidates whose name contains "John".

---

## 👥 TEAM 3 — Interview Engine (15 Interns)

### Task 3.1 — Question Bank Management UI (3 interns)
**Interns:** 23, 24, 25

**Goal:** HR should be able to add/edit/delete interview questions through a UI.

**What to do:**
- Create `frontend/src/app/questions/page.jsx` with table of all questions
- Add Create Question modal: Text, Category, Difficulty (Easy/Medium/Hard), Tags
- Edit and Delete buttons
- Wire to backend CRUD: `GET/POST/PUT/DELETE /questions`

**Definition of Done:** HR can add a new Python question and it appears in the question bank.

---

### Task 3.2 — Interview Templates (3 interns)
**Interns:** 26, 27, 28

**Goal:** Create reusable interview templates (e.g., "Python Dev - 45 min", "Data Science - 60 min").

**What to do:**
- Create `frontend/src/app/templates/page.jsx` to manage templates
- Template fields: Name, Duration, Question Count, Category distribution (40% technical, 30% behavioral, 30% situational)
- When starting an interview, allow selecting a template
- Backend: `GET/POST/PUT/DELETE /templates`

**Definition of Done:** Select "Python Dev" template → interview uses 60% Python questions.

---

### Task 3.3 — Real-Time Interview Q&A UI (4 interns)
**Interns:** 29, 30, 31, 32

**Goal:** During a live interview, display AI-generated questions and capture candidate answers.

**What to do:**
- Add a Q&A panel to `frontend/src/app/interview/page.jsx`
- Show the current question prominently
- Add a text area for the interviewer to type the candidate's answer
- "Next Question" button calls `POST /interviews/ask-question`
- "Submit Answer" button calls `POST /interviews/submit-answer`
- Show score feedback after each answer

**Definition of Done:** Interviewer can ask questions and record answers during a live session.

---

### Task 3.4 — Interview Scheduling System (3 interns)
**Interns:** 33, 34, 35

**Goal:** Schedule interviews in advance with calendar integration.

**What to do:**
- Create `frontend/src/app/schedule/page.jsx` with a calendar view
- Allow HR to pick a candidate, date/time, and interviewer
- Create `InterviewSchedule` model in DB: candidate_id, scheduled_at, interviewer_id, status
- Add email notification (using `smtplib`) to candidate when scheduled
- Show upcoming scheduled interviews on the dashboard

**Definition of Done:** Schedule an interview for tomorrow → candidate receives a confirmation email.

---

### Task 3.5 — Interview Replay / Recording (2 interns)
**Interns:** 36, 37

**Goal:** Store and replay interview sessions for review.

**What to do:**
- Save audio chunks to disk/object storage during interview
- Create a playback UI in the session report page
- Add a waveform visualizer using `wavesurfer.js`
- Allow download of the full recording

**Definition of Done:** After an interview ends, HR can click "Replay" and hear the full recording.

---

## 👥 TEAM 4 — AI & Analytics (15 Interns)

### Task 4.1 — LLM Question Generator (3 interns)
**Interns:** 38, 39, 40

**Goal:** Generate interview questions dynamically using Gemini AI based on the job description.

**What to do:**
- In `workers/evaluation_pipeline.py`, add `generate_questions(job_description, count=10)` function
- Call Gemini API with the job description and ask it to generate relevant technical questions
- Store generated questions in the question bank with `source: "AI"` tag
- In the UI, add a "Generate Questions with AI" button on the templates page

**Definition of Done:** Paste a Python developer job description → get 10 relevant interview questions.

---

### Task 4.2 — Answer Scoring with LLM (3 interns)
**Interns:** 41, 42, 43

**Goal:** Use AI to automatically score candidate answers instead of hardcoded scoring.

**What to do:**
- In `workers/evaluation_pipeline.py`, implement `score_answer(question, answer)` using Gemini
- Score on 0-10 scale with reasoning: technical accuracy, clarity, depth
- Return structured JSON: `{score: 7.5, reasoning: "...", strengths: [...], gaps: [...]}`
- Store in `InterviewSession.feedback_generated`

**Definition of Done:** Submit a candidate answer → get an AI-generated score with explanation.

---

### Task 4.3 — Bias Detection Module (2 interns)
**Interns:** 44, 45

**Goal:** Detect if any generated questions contain biased or EEOC-prohibited topics.

**What to do:**
- Expand `config.py`'s `BANNED_TOPICS` list with more keywords
- In `workers/evaluation_pipeline.py`, add `check_for_bias(question_text)` function
- If bias detected, flag the question and alert the interviewer
- Add a bias warning banner in the interview UI

**Definition of Done:** Question "How many children do you have?" triggers a bias warning.

---

### Task 4.4 — Sentiment Analysis on Answers (2 interns)
**Interns:** 46, 47

**Goal:** Analyze the sentiment and confidence of candidate's spoken answers.

**What to do:**
- In `workers/audio_pipeline.py`, add sentiment scoring after transcription
- Use a sentiment model (HuggingFace transformers) to classify: Confident/Neutral/Nervous
- Show a sentiment timeline chart in the session report
- Store sentiment scores in `InterviewSession.audio_analysis`

**Definition of Done:** After interview, report shows "Candidate was confident 70% of the time".

---

### Task 4.5 — Analytics Dashboard (3 interns)
**Interns:** 48, 49, 50

**Goal:** A rich analytics page showing hiring trends, pass rates, and performance stats.

**What to do:**
- Enhance `frontend/src/app/analytics/page.jsx`
- Charts to add (using Chart.js or Recharts):
  - Interview pass rate over time (line chart)
  - Score distribution by position (bar chart)
  - Risk score distribution (pie chart)
  - Average interview duration by month
  - Top performing candidates (leaderboard)
- Wire to `GET /analytics` endpoint which aggregates DB data

**Definition of Done:** Analytics page shows 5 charts with real data from the database.

---

### Task 4.6 — AI Interview Summary Report (2 interns)
**Interns:** 51, 52

**Goal:** After an interview, generate a comprehensive AI-written summary report.

**What to do:**
- In `workers/evaluation_pipeline.py`, add `generate_summary_report(session_data)` using Gemini
- Report includes: Overall rating, Key strengths, Areas for improvement, Hire recommendation (Yes/No/Maybe), Comparison to other candidates
- Display report in `frontend/src/app/review/page.jsx`
- Add "Export to PDF" button

**Definition of Done:** Click "Generate Report" on a completed session → get a 1-page AI summary.

---

## 👥 TEAM 5 — Infrastructure & DevOps (12 Interns)

### Task 5.1 — Environment Setup Script (2 interns)
**Interns:** 53, 54

**Goal:** One-command setup for new developers joining the project.

**What to do:**
- Create `setup.sh` / `setup.ps1` script that:
  - Checks for Docker, Docker Compose, Node.js
  - Copies `.env.example` to `.env`
  - Runs `docker-compose up -d`
  - Seeds demo data
  - Opens browser to `http://localhost:3000`
- Create `.env.example` with all required variables documented

**Definition of Done:** New intern can run `./setup.sh` and have the whole system running in 5 minutes.

---

### Task 5.2 — GitHub CI/CD Pipeline (3 interns)
**Interns:** 55, 56, 57

**Goal:** Automatically test and deploy code on every pull request.

**What to do:**
- Create `.github/workflows/ci.yml`:
  - On every PR: run Python tests (`pytest`), run frontend linting (`eslint`)
  - On merge to main: build Docker images and push to Docker Hub
- Create `.github/workflows/cd.yml`:
  - SSH into deployment server and run `docker-compose pull && docker-compose up -d`
- Add branch protection rules (PR requires CI to pass)

**Definition of Done:** Create a PR → CI runs automatically → merge → system auto-deploys.

---

### Task 5.3 — Monitoring & Alerting (3 interns)
**Interns:** 58, 59, 60

**Goal:** Get alerts when the system goes down or performs poorly.

**What to do:**
- Configure Grafana dashboards for:
  - API response times (p50, p95, p99)
  - Error rate (4xx, 5xx)
  - Worker queue depth
  - Memory and CPU usage
- Set up Grafana alerts: email when error rate > 5%, queue depth > 50
- Add an `/status` public page showing system health (green/yellow/red)

**Definition of Done:** Kill the worker container → receive an email alert within 2 minutes.

---

### Task 5.4 — Database Migrations (2 interns)
**Interns:** 61, 62

**Goal:** Manage database schema changes safely using Alembic migrations.

**What to do:**
- Initialize Alembic in the project: `alembic init alembic/`
- Create initial migration from current models
- Add migration for each new table added by other teams
- Create `migrate.sh` script that runs `alembic upgrade head`
- Document migration workflow in `CONTRIBUTING.md`

**Definition of Done:** Adding a new column can be done via an Alembic migration without data loss.

---

### Task 5.5 — Docker Optimization (2 interns)
**Interns:** 63, 64

**Goal:** Reduce Docker image sizes and build times.

**What to do:**
- Audit all Dockerfiles for unnecessary layers
- Use multi-stage builds where not already done
- Add `.dockerignore` files to exclude `node_modules`, `.git`, `__pycache__`
- Use `docker buildx` for cross-platform builds (AMD64 + ARM64)
- Target: reduce fastapi image from current size to <500MB

**Definition of Done:** `docker images` shows FastAPI image < 500MB.

---

## 👥 TEAM 6 — Frontend & UX (15 Interns)

### Task 6.1 — Dark/Light Mode Toggle (2 interns)
**Interns:** 65, 66

**Goal:** Allow users to switch between dark and light theme.

**What to do:**
- Add theme toggle button to the Topbar
- Store preference in `localStorage`
- Create CSS variables for all colors (--bg-primary, --text-primary, etc.)
- Apply theme class to `<body>` tag
- Ensure all pages respect the theme

**Definition of Done:** Click toggle → entire UI switches theme; preference persists on page refresh.

---

### Task 6.2 — Responsive Mobile Design (3 interns)
**Interns:** 67, 68, 69

**Goal:** Make the dashboard usable on tablets and mobile phones.

**What to do:**
- Audit all pages for mobile breakpoints
- Convert fixed sidebar to a collapsible drawer on mobile
- Make all tables horizontally scrollable on small screens
- Test on 375px (iPhone SE), 768px (iPad), 1024px (desktop)
- Fix any broken layouts found during testing

**Definition of Done:** Dashboard is fully usable on a phone without horizontal scrolling.

---

### Task 6.3 — Real-Time Notifications (3 interns)
**Interns:** 70, 71, 72

**Goal:** Show toast notifications when system events happen (interview completed, worker down).

**What to do:**
- Connect to the existing WebSocket at `/monitoring/ws/metrics`
- On session status change → show toast: "Interview for John Doe completed ✓"
- On worker going unhealthy → show warning toast
- Use a notification library like `react-hot-toast`
- Add a notification bell icon in the Topbar with unread count

**Definition of Done:** Complete an interview → see a green toast notification appear automatically.

---

### Task 6.4 — Onboarding Tour (2 interns)
**Interns:** 73, 74

**Goal:** Guide new users through the system on first login.

**What to do:**
- Use `intro.js` or `shepherd.js` for guided tour
- Tour steps: Sidebar navigation → Start Interview → View Sessions → Check Analytics
- Show tour automatically on first login (check `localStorage` flag)
- Add "Take Tour" button in Settings page

**Definition of Done:** New user logs in for the first time → tour starts automatically.

---

### Task 6.5 — Settings Page Completion (2 interns)
**Interns:** 75, 76

**Goal:** Make the Settings page fully functional.

**What to do:**
- General Settings: Company name, logo upload, timezone
- Interview Settings: Default template, max interview duration
- Notification Settings: Email for alerts, webhook URL
- API Settings: Regenerate API token, view current token (masked)
- Wire all settings to backend `PUT /settings` endpoint
- Persist to database (create `SystemSettings` table)

**Definition of Done:** Change company name in settings → it appears in the dashboard header.

---

### Task 6.6 — Keyboard Shortcuts (1 intern)
**Interns:** 77

**Goal:** Power users should be able to navigate without a mouse.

**What to do:**
- `Ctrl+K` → Open command palette (search for anything)
- `Ctrl+N` → Start new interview
- `Alt+1-9` → Navigate to sidebar sections
- Show shortcuts in a `/shortcuts` help page
- Show shortcut hints in tooltips

**Definition of Done:** Press `Ctrl+K` → a search box appears allowing navigation to any page.

---

### Task 6.7 — Export & Reporting (2 interns)
**Interns:** 78, 79

**Goal:** Allow exporting data as CSV and PDF from the UI.

**What to do:**
- Add "Export CSV" button to: Sessions list, Candidates list, Analytics page
- Add "Export PDF" for individual session reports
- Use `jsPDF` for PDF generation in browser
- Use backend PDF generation (reportlab) for complex reports

**Definition of Done:** Click "Export CSV" on Sessions page → download a CSV with all sessions.

---

## 👥 TEAM 7 — Video & Audio Processing (10 Interns)

### Task 7.1 — Face Detection Improvement (3 interns)
**Interns:** 80, 81, 82

**Goal:** Make the face detection in `workers/video_pipeline.py` more accurate and faster.

**What to do:**
- Replace current method with MediaPipe Face Detection
- Add liveness detection (detect if looking at camera vs. photo)
- Track eye gaze direction (looking left/right/down)
- Add confidence score to face detection results
- Benchmark: should process 30fps at <100ms per frame

**Definition of Done:** Video analysis correctly detects gaze direction with >90% accuracy.

---

### Task 7.2 — Speech-to-Text Accuracy (2 interns)
**Interns:** 83, 84

**Goal:** Improve transcription accuracy in `workers/audio_pipeline.py`.

**What to do:**
- Compare Whisper model sizes (tiny vs. base vs. small) for accuracy vs. speed tradeoff
- Add noise filtering before transcription (using `noisereduce` library)
- Handle multiple speakers (diarization)
- Add confidence score to transcriptions
- Document performance benchmarks

**Definition of Done:** Transcription accuracy > 95% on test audio files.

---

### Task 7.3 — Emotion Detection from Video (3 interns)
**Interns:** 85, 86, 87

**Goal:** Detect candidate emotions (confident, nervous, happy) from facial expressions.

**What to do:**
- Integrate `deepface` or `fer` library in `workers/video_pipeline.py`
- Detect: Happy, Sad, Angry, Fearful, Surprised, Neutral
- Track emotion over time (sample every 5 seconds)
- Show emotion timeline in the session report
- Store results in `InterviewSession.video_analysis`

**Definition of Done:** After interview, report shows a timeline of detected emotions.

---

### Task 7.4 — Proctoring Features (2 interns)
**Interns:** 88, 89

**Goal:** Detect cheating behaviors during the interview.

**What to do:**
- Tab switch detection (using `document.visibilitychange` event)
- Multiple faces detected alert
- Phone detected in frame (using object detection)
- Ear piece detection (flag for review)
- Log all proctoring events with timestamps to `InterviewSession.video_analysis`

**Definition of Done:** Switch to another tab during interview → event is logged with timestamp.

---

## 👥 TEAM 8 — API & Integrations (10 Interns)

### Task 8.1 — REST API Documentation (2 interns)
**Interns:** 90, 91

**Goal:** Complete and publish API documentation so external systems can integrate.

**What to do:**
- Ensure all FastAPI endpoints have complete docstrings
- Add request/response examples to all endpoints using `openapi_extra`
- Publish interactive Swagger UI at `/docs`
- Create a Postman collection with all endpoints pre-filled
- Write a `API_GUIDE.md` with authentication walkthrough

**Definition of Done:** A developer with no prior knowledge can make a successful API call using only the documentation.

---

### Task 8.2 — Webhook System (2 interns)
**Interns:** 92, 93

**Goal:** Allow external systems (HR software, Slack) to receive real-time notifications via webhook.

**What to do:**
- Create `WebhookSubscription` model: url, events (list), secret_key
- On events like `interview.completed`, `interview.failed`, send HTTP POST to all subscribed URLs
- Include HMAC signature for security
- Add retry logic (3 retries with exponential backoff)
- Create UI to manage webhook subscriptions in Settings

**Definition of Done:** Register a webhook URL → complete an interview → receive the event payload.

---

### Task 8.3 — Slack Integration (2 interns)
**Interns:** 94, 95

**Goal:** Send interview notifications to a Slack channel automatically.

**What to do:**
- Add Slack Webhook URL to Settings
- On interview complete → post message to Slack: "✅ John Doe completed Python Dev interview. Score: 8.2/10. Risk: LOW"
- On high-risk session → post alert: "⚠️ High risk interview detected for Jane Doe"
- Add "Test Slack Connection" button in Settings

**Definition of Done:** Complete a mock interview → see the notification appear in Slack channel.

---

### Task 8.4 — Calendar Integration (2 interns)
**Interns:** 96, 97

**Goal:** Sync scheduled interviews with Google Calendar / Outlook.

**What to do:**
- Use Google Calendar API to create calendar events when interviews are scheduled
- Include meeting link (optional Zoom/Google Meet link)
- Send calendar invites to both candidate and interviewer
- Allow cancelling/rescheduling from the UI

**Definition of Done:** Schedule interview → both candidate and interviewer get calendar invites.

---

### Task 8.5 — ATS Integration (LinkedIn, Workday) (2 interns)
**Interns:** 98, 99

**Goal:** Push interview results back to Applicant Tracking Systems.

**What to do:**
- Research LinkedIn Recruiter API and Workday API
- Create generic `ATSConnector` interface with `push_result(candidate_id, result)` method
- Implement LinkedIn connector (or mock if API unavailable)
- Add ATS configuration to Settings page

**Definition of Done:** Interview result is pushed to the configured ATS automatically.

---

## 👥 TEAM 9 — Testing & Quality (10 Interns)

### Task 9.1 — Unit Test Suite — Backend (3 interns)
**Interns:** 100, 101, 102

**Goal:** Achieve 80%+ test coverage on backend code.

**What to do:**
- Write pytest tests for all router endpoints (use `TestClient`)
- Write tests for `session_manager.py`, `load_balancer.py`, `scheduler.py`
- Use `pytest-asyncio` for async tests
- Mock external dependencies (Redis, PostgreSQL) with `pytest-mock`
- Add coverage report to CI: `pytest --cov=. --cov-report=html`

**Definition of Done:** `pytest` runs with 80%+ coverage; all tests pass in CI.

---

### Task 9.2 — Frontend Integration Tests (2 interns)
**Interns:** 103, 104

**Goal:** Automatically test the frontend UI to catch regressions.

**What to do:**
- Set up Playwright or Cypress for end-to-end testing
- Write tests for: Login flow, Start Interview, View Sessions, Candidate Registration
- Run tests in headless Chrome in CI
- Add visual regression testing (screenshot comparison)

**Definition of Done:** Running `npx playwright test` completes all tests successfully.

---

### Task 9.3 — Load Testing (2 interns)
**Interns:** 105, 106

**Goal:** Know how many concurrent users the system can handle before breaking.

**What to do:**
- Use `locust` to simulate concurrent users
- Test scenarios: 10, 50, 100, 500 concurrent interviews
- Identify bottlenecks (database? Redis? Worker queue?)
- Document results and recommend scaling strategy
- Create `locustfile.py` in the repo

**Definition of Done:** Load test report showing max throughput and bottleneck identification.

---

### Task 9.4 — Security Penetration Testing (3 interns)
**Interns:** 107, 108, 109

**Goal:** Find and fix security vulnerabilities before going to production.

**What to do:**
- Run OWASP ZAP against the running application
- Test for: SQL injection, XSS, CSRF, broken authentication, sensitive data exposure
- Test file upload endpoints for malicious file uploads
- Fix all CRITICAL and HIGH severity findings
- Write a security report with findings and fixes

**Definition of Done:** OWASP ZAP scan shows zero CRITICAL and HIGH vulnerabilities.

---

## 👥 TEAM 10 — Documentation & Training (9 Interns)

### Task 10.1 — Developer Documentation (3 interns)
**Interns:** 110, 111, 112

**Goal:** Any new developer should understand the codebase in 1 hour.

**What to do:**
- Write `ARCHITECTURE.md`: system overview, component diagram, data flow
- Write `CONTRIBUTING.md`: git workflow, coding standards, PR process
- Write `DATABASE.md`: schema diagram, relationships, indexes
- Add inline code comments to all complex functions
- Create architecture diagram using draw.io or Mermaid

**Definition of Done:** New intern can understand the system architecture from the docs alone.

---

### Task 10.2 — HR User Manual (2 interns)
**Interns:** 113, 114

**Goal:** Non-technical HR users need a guide to use the system.

**What to do:**
- Write step-by-step guide: Adding candidates, Scheduling interviews, Reviewing reports
- Include screenshots of every step
- Create a 5-minute video walkthrough (screen recording)
- Host the guide at `/help` in the frontend

**Definition of Done:** An HR user with no technical background can conduct an interview using only the manual.

---

### Task 10.3 — API Reference Site (2 interns)
**Interns:** 115, 116

**Goal:** A beautiful, searchable API documentation website.

**What to do:**
- Use `Mintlify` or `Docusaurus` to generate a documentation site
- Document every API endpoint with examples in multiple languages (Python, JS, curl)
- Auto-sync docs from FastAPI OpenAPI spec
- Deploy to GitHub Pages

**Definition of Done:** API docs site is live and searchable at a public URL.

---

### Task 10.4 — Changelog & Release Notes (2 interns)
**Interns:** 117, 118

**Goal:** Track what changes between versions.

**What to do:**
- Set up `semantic-release` for automated versioning
- Create `CHANGELOG.md` with all previous fixes documented
- Use conventional commits format: `feat:`, `fix:`, `chore:`
- Generate release notes automatically on GitHub

**Definition of Done:** Every merge to main creates a versioned release with auto-generated notes.

---

## 👥 TEAM 11 — Advanced AI Features (9 Interns)

### Task 11.1 — Multi-Language Support (3 interns)
**Interns:** 119, 120, 121

**Goal:** Conduct interviews in Hindi, Spanish, French, and other languages.

**What to do:**
- Add `language` field to interview start request
- Use Whisper's multilingual model for transcription
- Use Gemini's multilingual capabilities for question generation and scoring
- Add language selector in the interview UI
- Test with at least Hindi and Spanish

**Definition of Done:** Start a Hindi interview → questions are asked in Hindi, answers transcribed in Hindi.

---

### Task 11.2 — AI Interview Coach (3 interns)
**Interns:** 122, 123, 124

**Goal:** After a mock interview, give candidates personalized coaching.

**What to do:**
- Create `frontend/src/app/coach/page.jsx` — candidate-facing portal
- After interview, generate a coaching report: "You paused too much when asked about algorithms"
- Provide sample better answers using Gemini
- Track improvement over multiple interviews (score trend chart)

**Definition of Done:** Candidate completes mock interview → receives personalized coaching tips.

---

### Task 11.3 — Interview Difficulty Adaptation (3 interns)
**Interns:** 125, 126, 127

**Goal:** Automatically adjust question difficulty based on candidate performance.

**What to do:**
- In `workers/evaluation_pipeline.py`, track running score during interview
- If score > 8 → next question is Hard
- If score < 5 → next question is Easy
- If score 5-8 → Medium difficulty
- Track difficulty changes in session data
- Show difficulty progression in session report

**Definition of Done:** Candidate answers 3 questions perfectly → 4th question automatically becomes Hard.

---

## 📊 Summary Table

| Team | Focus Area | Interns | Tasks |
|------|-----------|---------|-------|
| Team 1 | Authentication & Security | 10 (1-10) | 4 tasks |
| Team 2 | Candidate Management | 12 (11-22) | 5 tasks |
| Team 3 | Interview Engine | 15 (23-37) | 5 tasks |
| Team 4 | AI & Analytics | 15 (38-52) | 6 tasks |
| Team 5 | Infrastructure & DevOps | 12 (53-64) | 5 tasks |
| Team 6 | Frontend & UX | 15 (65-79) | 7 tasks |
| Team 7 | Video & Audio Processing | 10 (80-89) | 4 tasks |
| Team 8 | API & Integrations | 10 (90-99) | 5 tasks |
| Team 9 | Testing & Quality | 10 (100-109) | 4 tasks |
| Team 10 | Documentation & Training | 9 (110-118) | 4 tasks |
| Team 11 | Advanced AI Features | 9 (119-127) | 3 tasks |
| **TOTAL** | | **127** | **52 tasks** |

---

## ⚠️ Important Rules for All Interns

1. **Never push directly to `main`** — Always create a feature branch and open a Pull Request
2. **Branch naming:** `feature/task-1-1-jwt-login`, `fix/task-5-2-ci-pipeline`
3. **PR requires:** At least 1 code review approval + CI passing
4. **Daily standup:** What did you do? What will you do? Any blockers?
5. **Use environment variables** — Never hardcode secrets, tokens, or passwords
6. **Write tests** for every function you create (minimum 1 unit test)
7. **Document** any new API endpoints you create

---

*Document prepared by: IntelliView Engineering Lead*
*Last updated: August 2026*
