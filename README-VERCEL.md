# NyaySahay — Vercel package

This package is a Vercel-compatible conversion of the original Streamlit prototype:
- Static browser UI: `index.html`
- FastAPI serverless API: `api/index.py`
- Existing legal engine, document processor, drafter and indexed legal database retained.

## Deploy
1. Extract this ZIP and push the contents of this folder to a GitHub repository.
2. Import that repository in Vercel. Keep the project root at the repository root.
3. Vercel should detect the Python function in `api/index.py`; deploy with the included `vercel.json`.
4. After deployment, open the site and test `/api/health`.

## Important
- This is a lightweight Vercel conversion, not the original Streamlit interface. It provides chat, evidence fact extraction, and API endpoints for legal document drafts.
- Configure provider keys as Vercel Environment Variables if you adapt the UI/API to use server-side secrets. Do not commit API keys.
- Vercel serverless functions have execution, memory, and request-size limits. Large PDFs, OCR-heavy scans, or sustained workloads may need dedicated backend hosting.
- The legal knowledge base is loaded from `legal_kb/legal_database.json`; original source PDFs are not bundled because runtime retrieval uses the indexed JSON.
- Review all generated legal content and current legal provisions before submission or filing.
