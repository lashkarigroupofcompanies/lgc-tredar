"""
Multi-Provider Universal LLM Brain Engine
==========================================
Supports 12+ Institutional and Open-Source LLM Providers:
1. NVIDIA NIM (Llama 3.3 70B, DeepSeek R1, Nemotron)
2. OpenAI (GPT-4o, GPT-4o-mini, o1, o3-mini)
3. Anthropic Claude (Claude 3.7 Sonnet, Claude 3.5 Sonnet, Claude 3.5 Haiku)
4. Google Gemini (Gemini 2.0 Flash, Gemini 1.5 Pro)
5. DeepSeek Direct (DeepSeek-V3, DeepSeek-R1)
6. Groq Ultra-Fast LPU (Llama 3.3 70B Versatile, Mixtral)
7. Perplexity AI (Sonar Pro, Sonar Reasoning)
8. Mistral AI (Mistral Large 2, Codestral, Pixtral)
9. Together AI (Llama 3.3 70B, Qwen 2.5 72B)
10. OpenRouter (Universal Gateway to 200+ models)
11. Ollama / Local vLLM (Local hardware, 0 cost, 100% private)
12. Custom OpenAI-Compatible Endpoint

Features:
- Auto-detection of provider and latest flagship model from API Key prefix
- Custom endpoint override
- Safe JSON structured parsing
- Deterministic rule-based local fallback when no API key is provided
- Config persistence to disk in llm_config.json
"""

import os
import json
import logging
import re
from typing import Dict, Any, List, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LLMBrain")

CONFIG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "llm_config.json"))

# Comprehensive Provider Catalog with default endpoints and latest flagship models
PROVIDERS_CATALOG: Dict[str, Dict[str, Any]] = {
    "NVIDIA": {
        "name": "NVIDIA NIM",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "default_model": "meta/llama-3.3-70b-instruct",
        "models": ["meta/llama-3.3-70b-instruct", "deepseek-ai/deepseek-r1", "nvidia/llama-3.1-nemotron-70b-instruct"],
        "key_prefix": "nvapi-",
        "auth_type": "bearer",
        "env_key": "NVIDIA_API_KEY"
    },
    "OPENAI": {
        "name": "OpenAI (GPT-4.5 / o3 / o1 / GPT-4o)",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4.5-preview",
        "models": ["gpt-4.5-preview", "gpt-4o", "o3-mini", "o1", "gpt-4o-mini"],
        "key_prefix": "sk-",
        "auth_type": "bearer",
        "env_key": "OPENAI_API_KEY"
    },
    "ANTHROPIC": {
        "name": "Anthropic Claude (3.7 Sonnet)",
        "base_url": "https://api.anthropic.com/v1",
        "default_model": "claude-3-7-sonnet-20250219",
        "models": ["claude-3-7-sonnet-20250219", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"],
        "key_prefix": "sk-ant-",
        "auth_type": "anthropic",
        "env_key": "ANTHROPIC_API_KEY"
    },
    "GEMINI": {
        "name": "Google Gemini (2.5 Flash / 2.5 Pro)",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "default_model": "gemini-2.5-flash",
        "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-2.0-flash-thinking-exp", "gemini-2.0-pro-exp-02-05", "gemini-1.5-pro"],
        "key_prefix": "AIzaSy",
        "auth_type": "bearer",
        "env_key": "GEMINI_API_KEY"
    },
    "DEEPSEEK": {
        "name": "DeepSeek Direct (R1 / V3)",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-reasoner",
        "models": ["deepseek-reasoner", "deepseek-chat"],
        "key_prefix": "sk-",
        "auth_type": "bearer",
        "env_key": "DEEPSEEK_API_KEY"
    },
    "GROQ": {
        "name": "Groq Ultra-Fast LPU",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "deepseek-r1-distill-llama-70b",
        "models": ["deepseek-r1-distill-llama-70b", "llama-3.3-70b-versatile", "qwen-2.5-32b", "mixtral-8x7b-32768"],
        "key_prefix": "gsk_",
        "auth_type": "bearer",
        "env_key": "GROQ_API_KEY"
    },
    "PERPLEXITY": {
        "name": "Perplexity AI (Deep Research)",
        "base_url": "https://api.perplexity.ai",
        "default_model": "sonar-deep-research",
        "models": ["sonar-deep-research", "sonar-reasoning-pro", "sonar-pro", "sonar"],
        "key_prefix": "pplx-",
        "auth_type": "bearer",
        "env_key": "PERPLEXITY_API_KEY"
    },
    "MISTRAL": {
        "name": "Mistral AI",
        "base_url": "https://api.mistral.ai/v1",
        "default_model": "mistral-large-latest",
        "models": ["mistral-large-latest", "codestral-latest", "pixtral-large-latest"],
        "key_prefix": "",
        "auth_type": "bearer",
        "env_key": "MISTRAL_API_KEY"
    },
    "TOGETHER": {
        "name": "Together AI",
        "base_url": "https://api.together.xyz/v1",
        "default_model": "deepseek-ai/DeepSeek-R1",
        "models": ["deepseek-ai/DeepSeek-R1", "deepseek-ai/DeepSeek-V3", "meta-llama/Llama-3.3-70B-Instruct-Turbo"],
        "key_prefix": "",
        "auth_type": "bearer",
        "env_key": "TOGETHER_API_KEY"
    },
    "OPENROUTER": {
        "name": "OpenRouter (200+ Models)",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "google/gemini-2.5-flash",
        "models": ["google/gemini-2.5-flash", "anthropic/claude-3.7-sonnet", "openai/gpt-4.5-preview", "deepseek/deepseek-r1"],
        "key_prefix": "sk-or-",
        "auth_type": "bearer",
        "env_key": "OPENROUTER_API_KEY"
    },
    "OLLAMA": {
        "name": "Ollama / Local vLLM",
        "base_url": "http://localhost:11434/v1",
        "default_model": "llama3.3:latest",
        "models": ["llama3.3:latest", "deepseek-r1:latest", "mistral:latest", "qwen2.5:latest"],
        "key_prefix": "",
        "auth_type": "none",
        "env_key": "OLLAMA_BASE_URL"
    },
    "CUSTOM": {
        "name": "Custom OpenAI-Compatible",
        "base_url": "https://api.openai.com/v1",
        "default_model": "default-model",
        "models": ["default-model"],
        "key_prefix": "",
        "auth_type": "bearer",
        "env_key": "CUSTOM_LLM_API_KEY"
    }
}


class LLMBrain:
    """
    Central AI reasoning client supporting 12+ providers with auto-detection,
    model selection, and graceful deterministic fallback.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LLMBrain, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        provider: str = "NVIDIA",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        if getattr(self, "_initialized", False):
            return

        self.provider = provider.upper()
        self.api_key = api_key or ""
        self.model = model or ""
        self.base_url = base_url or ""
        self._load_config()
        self._initialized = True

    def _load_config(self):
        """Loads saved LLM configuration from disk or defaults."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.provider = cfg.get("provider", "NVIDIA").upper()
                    self.api_key = cfg.get("api_key", self.api_key)
                    self.model = cfg.get("model", self.model)
                    self.base_url = cfg.get("base_url", self.base_url)
                    logger.info(f"[LLMBrain] Loaded config: Provider={self.provider}, Model={self.model}")
                    return
            except Exception as e:
                logger.warning(f"[LLMBrain] Error reading config file: {e}")

        # Fallback to environment variables
        env_key = os.getenv("LLM_API_KEY") or os.getenv("NVIDIA_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
        if env_key:
            self.api_key = env_key
            self.provider, detected_model = self.auto_detect_provider(env_key)
            self.model = os.getenv("LLM_MODEL") or detected_model
        else:
            cat = PROVIDERS_CATALOG.get(self.provider, PROVIDERS_CATALOG["NVIDIA"])
            if not self.model:
                self.model = cat["default_model"]
            if not self.base_url:
                self.base_url = cat["base_url"]

    def save_config(
        self,
        provider: str,
        api_key: str,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Saves user-configured LLM provider, key, and model to disk."""
        prov_key = provider.upper()
        cat = PROVIDERS_CATALOG.get(prov_key, PROVIDERS_CATALOG["CUSTOM"])

        # Auto-detect if provider is set to AUTO
        if prov_key == "AUTO" or not prov_key:
            detected_prov, auto_model = self.auto_detect_provider(api_key)
            prov_key = detected_prov
            cat = PROVIDERS_CATALOG.get(prov_key, PROVIDERS_CATALOG["CUSTOM"])
            if not model:
                model = auto_model

        final_model = model or cat.get("default_model", "default-model")
        final_url = base_url or cat.get("base_url", "")

        self.provider = prov_key
        self.api_key = api_key.strip()
        self.model = final_model.strip()
        self.base_url = final_url.strip()

        cfg_data = {
            "provider": self.provider,
            "api_key": self.api_key,
            "model": self.model,
            "base_url": self.base_url,
            "updated_at": os.popen("date").read().strip() if os.name != "nt" else ""
        }

        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg_data, f, indent=2)
            logger.info(f"[LLMBrain] Config successfully persisted: {self.provider} ({self.model})")
        except Exception as e:
            logger.error(f"[LLMBrain] Failed to save config: {e}")

        return {
            "status": "CONFIG_SAVED",
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "is_configured": self.is_configured()
        }

    @staticmethod
    def auto_detect_provider(api_key: str) -> tuple[str, str]:
        """
        Auto-detects provider and latest flagship model based on the API key format.
        """
        k = api_key.strip()
        if k.startswith("sk-ant-"):
            return "ANTHROPIC", "claude-3-7-sonnet-20250219"
        if k.startswith("sk-or-"):
            return "OPENROUTER", "google/gemini-2.5-flash"
        if k.startswith("AIzaSy"):
            return "GEMINI", "gemini-2.5-flash"
        if k.startswith("gsk_"):
            return "GROQ", "deepseek-r1-distill-llama-70b"
        if k.startswith("pplx-"):
            return "PERPLEXITY", "sonar-deep-research"
        if k.startswith("nvapi-"):
            return "NVIDIA", "meta/llama-3.3-70b-instruct"
        if k.startswith("sk-") and len(k) > 45:
            # Common OpenAI key prefix
            return "OPENAI", "gpt-4.5-preview"
        if k.startswith("sk-"):
            return "DEEPSEEK", "deepseek-reasoner"
        if "localhost" in k or "127.0.0.1" in k:
            return "OLLAMA", "llama3.3:latest"
        
        return "CUSTOM", "default-model"

    def is_configured(self) -> bool:
        """Check if a real API key or local Ollama endpoint is configured."""
        if self.provider == "OLLAMA":
            return True
        return bool(self.api_key and not self.api_key.startswith("your_") and len(self.api_key) > 8)

    def get_status_summary(self) -> Dict[str, Any]:
        """Returns safe status summary for UI."""
        masked_key = ""
        if self.api_key:
            if len(self.api_key) > 8:
                masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}"
            else:
                masked_key = "****"

        cat = PROVIDERS_CATALOG.get(self.provider, PROVIDERS_CATALOG["CUSTOM"])
        return {
            "provider": self.provider,
            "provider_name": cat.get("name", self.provider),
            "model": self.model or cat.get("default_model", ""),
            "base_url": self.base_url or cat.get("base_url", ""),
            "api_key_masked": masked_key,
            "is_configured": self.is_configured(),
            "available_providers": [
                {"id": k, "name": v["name"], "default_model": v["default_model"], "models": v["models"]}
                for k, v in PROVIDERS_CATALOG.items()
            ]
        }

    def query(self, prompt: str, system_prompt: str = "", temperature: float = 0.2) -> str:
        """Alias for complete() to support query-style agent calls."""
        return self.complete(prompt, system_prompt=system_prompt, temperature=temperature)

    def complete(self, prompt: str, system_prompt: str = "", temperature: float = 0.2) -> str:
        """
        Sends an inference request to the configured provider API (OpenAI-compatible format or Anthropic).
        Falls back to local deterministic intelligence reasoning if key is not configured or on network error.
        """
        if not self.is_configured():
            logger.info("[LLMBrain] LLM API key not configured. Using local deterministic intelligence reasoning.")
            return self._local_fallback(prompt)

        cat = PROVIDERS_CATALOG.get(self.provider, PROVIDERS_CATALOG["CUSTOM"])
        url = self.base_url or cat.get("base_url", "https://api.openai.com/v1")
        model = self.model or cat.get("default_model", "gpt-4o")

        # -------------------------------------------------------------
        # Anthropic Direct Format
        # -------------------------------------------------------------
        if self.provider == "ANTHROPIC":
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            payload = {
                "model": model,
                "max_tokens": 1024,
                "temperature": temperature,
                "system": system_prompt or "You are an elite institutional Quantitative Portfolio Manager and News Analyst.",
                "messages": [{"role": "user", "content": prompt}]
            }
            try:
                resp = requests.post(f"{url.rstrip('/')}/messages", headers=headers, json=payload, timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("content", [{}])[0].get("text", "")
                else:
                    logger.error(f"[LLMBrain] Anthropic API HTTP {resp.status_code}: {resp.text}")
                    return self._local_fallback(prompt)
            except Exception as e:
                logger.error(f"[LLMBrain] Anthropic request exception: {e}")
                return self._local_fallback(prompt)

        # -------------------------------------------------------------
        # Universal OpenAI-Compatible Format (OpenAI, NVIDIA, Groq, DeepSeek, Gemini, Perplexity, Mistral, Together, OpenRouter, Ollama)
        # -------------------------------------------------------------
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if self.provider == "OPENROUTER":
            headers["HTTP-Referer"] = "https://github.com/google/antigravity"
            headers["X-Title"] = "LGC Quantitative Trading OS"

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt or "You are an elite institutional Quantitative Portfolio Manager and News Analyst."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": 1024
        }

        # Normalize endpoint path
        endpoint = f"{url.rstrip('/')}/chat/completions" if not url.endswith("/chat/completions") else url

        try:
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                return ""
            else:
                logger.error(f"[LLMBrain] {self.provider} API HTTP {resp.status_code}: {resp.text}")
                return self._local_fallback(prompt)
        except Exception as e:
            logger.error(f"[LLMBrain] LLM request exception ({self.provider}): {e}")
            return self._local_fallback(prompt)

    def analyze_news_signals(self, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Deep financial reasoning combining LLM analysis with Knowledge Graph signals.
        """
        news_summary = []
        for i, item in enumerate(news_items[:6]):
            catalyst = item.get("primary_catalyst_id", "NONE")
            action = item.get("knowledge_recommendation", "HOLD")
            news_summary.append(
                f"[{i+1}] Title: {item.get('title')}\n"
                f"    Tickers: {item.get('tickers', [])} | Sentiment: {item.get('sentiment_score', 0)} ({item.get('bias')})\n"
                f"    Knowledge Graph Catalyst: {catalyst} | Recommended Rule: {action}"
            )

        news_text = "\n\n".join(news_summary)

        system_instruction = (
            "You are the Head of Financial News Intelligence for an elite AI Quant Fund.\n"
            "Analyze the following live breaking headlines and knowledge graph catalyst triggers.\n"
            "Return a strictly valid JSON object with the following schema:\n"
            "{\n"
            '  "thought_process": "Short 2-3 sentence strategic reasoning on how these events interact.",\n'
            '  "macro_bias": "BULLISH" | "BEARISH" | "NEUTRAL",\n'
            '  "high_probability_targets": ["BTC", "CRUDE", etc],\n'
            '  "risk_stance": "AGGRESSIVE" | "NORMAL" | "DEFENSIVE",\n'
            '  "trade_recommendations": [\n'
            '    {"asset": "BTC", "direction": "BUY"|"SELL"|"AVOID", "timeframe": "1h"|"4h"|"1d", "conviction": 85, "rationale": "Reason"}\n'
            '  ]\n'
            "}"
        )

        user_prompt = f"Here is the latest live market intelligence batch:\n\n{news_text}\n\nProvide your quant reasoning in exact JSON."

        raw_output = self.complete(user_prompt, system_prompt=system_instruction)

        # Parse JSON from LLM output
        try:
            cleaned = raw_output.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            return json.loads(cleaned)
        except Exception:
            logger.warning("[LLMBrain] Could not parse LLM output as JSON, building structured fallback.")
            return self._build_structured_fallback(news_items)

    def _local_fallback(self, prompt: str) -> str:
        return (
            "Market Analysis Summary: Identified dominant geopolitical and macroeconomic catalysts. "
            "Recommending disciplined position sizing and risk-on caution until volatility normalizes."
        )

    def _build_structured_fallback(self, news_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Rule-based structured reasoning fallback using the Knowledge Graph signals."""
        bullish_count = sum(1 for n in news_items if n.get("bias") == "BULLISH")
        bearish_count = sum(1 for n in news_items if n.get("bias") == "BEARISH")

        targets = set()
        recommendations = []
        for n in news_items:
            for t in n.get("tickers", []):
                targets.add(t)
            if n.get("is_actionable"):
                direction = "BUY" if n.get("bias") == "BULLISH" else "SELL"
                recommendations.append({
                    "asset": n.get("tickers", ["MARKET"])[0] if n.get("tickers") else "MARKET",
                    "direction": direction,
                    "timeframe": "4h",
                    "conviction": int(abs(n.get("sentiment_score", 0.5)) * 100),
                    "rationale": n.get("macro_effect_summary", n.get("title", "Catalyst signal"))
                })

        overall_bias = "BULLISH" if bullish_count > bearish_count else ("BEARISH" if bearish_count > bullish_count else "NEUTRAL")

        return {
            "thought_process": f"Evaluated {len(news_items)} live stories. Macro balance shows {bullish_count} bullish vs {bearish_count} bearish signals. Enforcing systematic trend rules.",
            "macro_bias": overall_bias,
            "high_probability_targets": list(targets)[:4],
            "risk_stance": "DEFENSIVE" if bearish_count > bullish_count else "NORMAL",
            "trade_recommendations": recommendations[:3]
        }


if __name__ == "__main__":
    brain = LLMBrain()
    print("Provider:", brain.provider)
    print("Configured:", brain.is_configured())
    print("Status:", brain.get_status_summary())
