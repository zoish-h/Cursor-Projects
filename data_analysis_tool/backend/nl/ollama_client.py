"""Ollama client: build context from analysis and stream answers."""
import json
from typing import Any, AsyncGenerator, Dict, Optional

import httpx

OLLAMA_BASE = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"


def build_context(analysis: Dict[str, Any], max_sample_rows: int = 5) -> str:
    """Build a text summary of the analysis for the LLM."""
    if not analysis or analysis.get("error"):
        return "No dataset is loaded. Ask the user to upload a file first."
    parts = []
    parts.append(f"Dataset: {analysis.get('row_count', 0)} rows, {analysis.get('column_count', 0)} columns.")
    parts.append(f"Columns: {', '.join(analysis.get('columns', []))}")
    col_types = analysis.get("column_types", {})
    if col_types:
        parts.append("Column types: " + json.dumps(col_types))
    dl = analysis.get("dataset_level", {})
    char = dl.get("characterization", {})
    parts.append(f"Data kind: {char.get('kind', 'unknown')}. Target column: {char.get('target_column') or 'none'}.")
    metrics = dl.get("metrics", {})
    if metrics:
        parts.append("Metrics: " + json.dumps({k: v for k, v in metrics.items() if k != "explanation_type"}))
    parts.append("Explainability: " + "; ".join(analysis.get("explainability", [])))
    profile = analysis.get("data_profile", [])[:10]
    if profile:
        parts.append("Column summaries (sample): " + json.dumps(profile[:5], default=str))
    return "\n".join(parts)


async def stream_ask(
    question: str,
    context: str,
    model: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Stream response from Ollama given question and context."""
    model = model or DEFAULT_MODEL
    payload = {
        "model": model,
        "prompt": f"""You are a helpful data analyst. Use ONLY the following dataset context to answer the user's question. If the context is missing or insufficient, say so briefly. Be concise.

Context:
{context}

User question: {question}

Answer:""",
        "stream": True,
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", f"{OLLAMA_BASE}/api/generate", json=payload) as resp:
                if resp.status_code != 200:
                    yield f"[Ollama error: {resp.status_code}. Is Ollama running? Try: ollama run {model}]"
                    return
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
    except httpx.ConnectError:
        yield "[Ollama is not available. Start it locally (e.g. run 'ollama serve') and pull a model (e.g. 'ollama run llama3.2').]"
    except Exception as e:
        yield f"[Error: {e}]"
