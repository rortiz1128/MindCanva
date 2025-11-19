# MindCanvas Teacher Actions API

FastAPI-powered backend for **MindCanvas**, enabling a GPT to retrieve information and take actions outside ChatGPT via **Actions** (OpenAPI-described HTTPS endpoints). It includes 7 teacher-focused endpoints:

- `POST /create-lesson-plan`
- `POST /generate-quiz`
- `POST /grade-with-rubric`
- `POST /map-objectives-to-standards`
- `POST /schedule-parent-conference`
- `POST /track-student-progress`
- `POST /analyze-exit-tickets`

> **OpenAPI spec:** served automatically at `GET /openapi.json` (use this URL to import into your GPT Action).  
> **Interactive docs:** `GET /docs` (Swagger UI).


---

## ✨ Features
- Clean **FastAPI** implementation with **Pydantic v2** models
- Simple **API Key** auth via `X-API-Key` header
- Ready for **Render** one-click deployment (free tier)
- Copy/paste **curl** examples to verify quickly
- Structured responses tailored for teacher workflows

---

## 📁 Project Structure
```
mindcanvas-api/
├─ main.py
├─ requirements.txt
├─ README.md
└─ .env.example
```

---

## ⚙️ Requirements
- Python 3.11+
- pip
- (Optional) `curl` and `jq` for quick testing

---

## 🚀 Local Development

1) **Clone & enter** the project
```bash
git clone https://github.com/rortiz1128/mindcanvas-api.git
cd mindcanvas-api
```

2) **Create a virtual environment (optional but recommended)**
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

3) **Install dependencies**
```bash
pip install -r requirements.txt
```

4) **Configure environment**
```bash
cp .env.example .env
# edit .env and set:
# API_KEY=your-long-random-secret
```

5) **Run the API**
```bash
uvicorn main:app --reload --port 8000
```

6) **Open the docs**
- Swagger UI: http://127.0.0.1:8000/docs  
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json

---

## 🔐 Authentication

All protected endpoints require the header:
```
X-API-Key: <your-secret>
```

Set this value on Render (or your host) as an environment variable `API_KEY`.


---

## 🧪 Quick Tests

Health check:
```bash
curl -sS http://127.0.0.1:8000/ | jq
```

Generate a quiz:
```bash
API_KEY=your-long-random-secret
curl -sS -X POST http://127.0.0.1:8000/generate-quiz \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"topic":"Photosynthesis","question_types":["mcq","short_answer"],"num_questions":3}'
```

Create a lesson plan:
```bash
curl -sS -X POST http://127.0.0.1:8000/create-lesson-plan \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"subject":"ELA","grade_level":"5","standards":["CCSS.ELA-LITERACY.RL.5.2"],"duration_minutes":60,"learning_objectives":["Determine theme from details"],"differentiation":true}'
```

---

## 🌐 Deploy to Render (Option A)

> Free, simple hosting with auto-HTTPS and auto-deploys from GitHub

1) **Push to GitHub**
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-user>/mindcanvas-api.git
git push -u origin main
```

2) **Create a Web Service** on Render
- Render dashboard → **New +** → **Web Service**
- Connect GitHub repo `mindcanvas-api`

3) **Service settings**
- **Name:** `mindcanvas-api` (or any)
- **Branch:** `main`
- **Build Command:**
  ```
  pip install -r requirements.txt
  ```
- **Start Command:**
  ```
  uvicorn main:app --host 0.0.0.0 --port $PORT
  ```

4) **Environment Variable**
- Key: `API_KEY`
- Value: `your-long-random-secret`

5) **Deploy**
- Wait until status is **Live**
- Copy the Render base URL (e.g., `https://mindcanvas-api.onrender.com`)

6) **Smoke test**
```bash
curl -sS https://mindcanvas-api.onrender.com/ | jq
API_KEY=your-long-random-secret
curl -sS -X POST https://mindcanvas-api.onrender.com/generate-quiz \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"topic":"Photosynthesis","question_types":["mcq","short_answer"],"num_questions":3}'
```

7) **Import into your GPT (Actions)**
- In the GPT Builder → **Actions → Add Action → Import from URL**
- Import:
  ```
  https://mindcanvas-api.onrender.com/openapi.json
  ```
- **Authentication:** API Key  
  - Key location: Header  
  - Header name: `X-API-Key`  
  - Value: (same as on Render)

> **Important:** Do **not** use your GPT page URL as `servers.url`. The base must be your deployed API (the Render URL).


---

## 🧩 Endpoints (Summary)

### `POST /create-lesson-plan`
Input: subject, grade_level, standards[], duration_minutes, learning_objectives[], differentiation  
Output: structured lesson plan (meta, sequence, assessment, differentiation)

### `POST /generate-quiz`
Input: topic, question_types[], num_questions, difficulty, include_rationales  
Output: questions[], answer_key[]

### `POST /grade-with-rubric`
Input: rubric[], student_response, max_total_points?  
Output: total_points, per-criterion details, feedback

### `POST /map-objectives-to-standards`
Input: frameworks[], objectives[]  
Output: suggested mappings with confidence

### `POST /schedule-parent-conference`
Input: student_name, guardians[], preferred_modalities[], teacher_availability_blocks[], language  
Output: time proposals + invite draft

### `POST /track-student-progress`
Input: student_id, entries[], rollup_window  
Output: mastery rollups per standard

### `POST /analyze-exit-tickets`
Input: prompt, responses[], num_groups, return_exemplars_per_group  
Output: groups, misconceptions


---

## 🛡️ Security Notes
- Use strong, rotated API keys. Store only in environment variables.
- Free-tier hosting may sleep on idle (first call after idle may be slower).
- Add CORS rules if you call the API directly from browsers (FastAPI’s `CORSMiddleware`).

---

## 🧱 (Optional) Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build & run:
```bash
docker build -t mindcanvas-api .
docker run -p 8000:8000 -e API_KEY=your-long-random-secret mindcanvas-api
```

---

## ❓ Troubleshooting
- **401 Unauthorized** → Missing or wrong `X-API-Key` header.
- **Import fails in GPT** → Use `https://<your-host>/openapi.json` (JSON), not `/docs` (HTML).
- **“Could not find a valid URL in servers”** → Ensure your OpenAPI reports an absolute `https://` base; FastAPI on Render does.
- **CORS errors in browser** → Add `CORSMiddleware` in `main.py` and allow your frontend origin.

---

## 📄 License
MIT (or your preferred license). Update this section as needed.

---

## 📝 Changelog
- **v1.0.0** — Initial release with 7 endpoints, API key auth, Render deploy guide.
