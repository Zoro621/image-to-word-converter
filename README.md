# DocuVision: Agentic Document Intelligence Platform (Phase 2)

DocuVision is a modern, multi-agent AI system that intelligently extracts structured text from unstructured images (handwritten notes, complex diagrams, and printed forms). Unlike traditional static OCR tools, DocuVision operates as a **PIDAL Agent** (Perceive → Interpret → Decide → Act → Learn), dynamically adjusting its extraction strategy based on the input content and its own historical performance.

## 🌟 Key Features

* **5-Layer Agentic Pipeline**:
  * **Perception Agent**: Analyzes image quality, content type (handwritten vs printed), language script, and detects sensitive elements like faces, signatures, or ID card features.
  * **Decision Agent**: Evaluates perception heuristics to apply an Ethics Gate (halting for user consent), Legal Gate (copyright warnings), and dynamically routes the task to the best vision model.
  * **Action Agent**: Strips privacy-compromising EXIF data, executes the vision model inference, validates the output confidence, and runs heuristic retry logic on failure.
  * **Memory System**: A persistent memory module (`agent_memory.json`) that logs model performance and agent heuristics across sessions.
  * **Learning Agent**: Blends user feedback (thumbs up/down) with confidence scores to adjust the decision routing dynamically for future requests.
* **Modern Frontend (Next.js)**:
  * Sleek glassmorphism design with a fully interactive **Three.js** particle field background.
  * Live **Agent Pipeline Visualizer** to see exactly what the AI is thinking at each stage.
  * Built with Tailwind CSS, Framer Motion, and Lucide React.
* **Ethics by Design**:
  * Mandatory user consent barriers for PII (Personally Identifiable Information).
  * Bias disclosures shown when non-Latin scripts are detected.
  * Local, in-memory processing: zero image persistence to disk.

## 🛠️ Tech Stack

**Frontend:**
* Next.js (App Router)
* React Three Fiber (3D Background)
* Framer Motion (Animations)
* Tailwind CSS

**Backend:**
* FastAPI (Python)
* Pillow (Image Processing / EXIF stripping)
* OpenCV (Haar Cascades for privacy detection)
* `python-docx` (Word Document Generation)
* HuggingFace Inference API (`Qwen3-VL-8B`)
* OpenAI API (`GPT-4-Vision`)

## 🚀 How to Run

### 1. Configure Secrets
Create a `.streamlit/secrets.toml` file in the root directory (the backend will read it at startup):
```toml
# HuggingFace token (for Qwen3-VL model)
HF_TOKEN = "your_hf_token_here"

# OpenAI API key (for GPT-4 Vision model)
OPENAI_API_KEY = "your_openai_api_key_here"
```
*(Note: OpenAI is optional. If left blank, the agent will only use Qwen).*

### 2. Start the Backend (FastAPI)
```bash
# In the project root directory
pip install -r requirements.txt
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Start the Frontend (Next.js)
```bash
# In a new terminal
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the app.

## 🧠 System Methodology & Limitations
For a deep dive into the architectural reasoning, ethical considerations, and known limitations of the system, please refer to the `docuvision_agentic_methodology.md` file located in the root.
