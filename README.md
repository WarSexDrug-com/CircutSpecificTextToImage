# CricutGen

Turn a text prompt into a layered, cut-ready SVG using OpenAI image generation.

## Run locally

1. Install Python 3.11 or newer.
2. Create and activate a virtual environment, then install dependencies:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and set `OPENAI_API_KEY` to an API key with image generation access. Image generation is billed by OpenAI.
4. Start the app from this project folder:

   ```powershell
   uvicorn app.main:app --reload
   ```

5. Open http://127.0.0.1:8000.

To run it again later from the project folder, activate `.venv` and run `uvicorn app.main:app --reload`. On the deployed Hostinger VPS, start it with `sudo systemctl start cricutgen`; see [HOSTINGER_DEPLOYMENT.md](HOSTINGER_DEPLOYMENT.md).

Generated SVGs and previews are saved in `app/output/`.


For reusable Cricut design guidance, see the project skill at .agents/skills/cricut-layer-art/SKILL.md.
