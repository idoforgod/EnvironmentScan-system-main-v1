"""
Local LLM Classifier
Uses free open-source LLM for signal classification (no API costs)
"""

from typing import Dict, Any, List
import json


class LocalLLMClassifier:
    """
    Free classification using local open-source LLM

    Options:
    1. Ollama (easiest) - Run LLMs locally
    2. HuggingFace Transformers - Python library
    3. LM Studio - GUI application

    No API costs, runs on your machine
    """

    def __init__(self, model_type: str = "ollama"):
        """
        Initialize local LLM classifier

        Args:
            model_type: "ollama", "transformers", or "lmstudio"
        """
        self.model_type = model_type

        if model_type == "ollama":
            self._init_ollama()
        elif model_type == "transformers":
            self._init_transformers()
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

    def _init_ollama(self):
        """
        Initialize Ollama (recommended)

        Installation:
            1. Install Ollama: https://ollama.ai
            2. Run: ollama pull llama3.1:8b
            3. Done!
        """
        try:
            import requests
            self.ollama_url = "http://localhost:11434/api/generate"

            # Test connection
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code != 200:
                raise ConnectionError("Ollama not running. Start with: ollama serve")

            print("[INFO] Ollama connected successfully")

        except ImportError:
            print("[ERROR] Install requests: pip install requests")
            raise
        except Exception as e:
            print(f"[ERROR] Ollama not available: {e}")
            print("[HELP] Install Ollama from https://ollama.ai")
            raise

    def _init_transformers(self):
        """
        Initialize HuggingFace Transformers

        Installation:
            pip install transformers torch
        """
        try:
            from transformers import pipeline

            # Load a lightweight classification model
            self.classifier = pipeline(
                "text-classification",
                model="facebook/bart-large-mnli"  # Zero-shot classification
            )

            print("[INFO] Transformers model loaded")

        except ImportError:
            print("[ERROR] Install transformers: pip install transformers torch")
            raise

    def classify_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a signal using local LLM

        Args:
            signal: Signal with title and abstract

        Returns:
            Classification result
        """
        if self.model_type == "ollama":
            return self._classify_with_ollama(signal)
        elif self.model_type == "transformers":
            return self._classify_with_transformers(signal)

    def _classify_with_ollama(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify using Ollama (Llama 3.1)

        Free, local, no API costs
        """
        import requests

        # Build prompt
        prompt = f"""Classify this research paper into ONE STEEPs category.

Title: {signal['title']}
Abstract: {signal['content']['abstract'][:500]}

Categories:
- S (Social): Demographics, culture, society
- T (Technological): AI, robotics, innovation
- E (Economic): Markets, finance, economy
- E (Environmental): Climate, ecology, energy
- P (Political): Policy, regulation, governance
- s (spiritual): Ethics, values, meaning

Respond ONLY with valid JSON:
{{
  "category": "S|T|E|P|s",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}
"""

        # Call Ollama
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": "llama3.1:8b",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                text = result.get('response', '{}')

                # Parse JSON response
                try:
                    classification = json.loads(text)
                    return {
                        "category": classification.get("category", "T"),
                        "confidence": classification.get("confidence", 0.7),
                        "reasoning": classification.get("reasoning", ""),
                        "method": "ollama_llama3.1",
                        "cost": 0.0  # Free!
                    }
                except json.JSONDecodeError:
                    # Fallback: parse text manually
                    return self._parse_text_response(text)
            else:
                raise Exception(f"Ollama error: {response.status_code}")

        except Exception as e:
            print(f"[ERROR] Ollama classification failed: {e}")
            # Fallback to preliminary category
            return {
                "category": signal['preliminary_category'],
                "confidence": 0.6,
                "reasoning": "Ollama failed, using preliminary",
                "method": "fallback",
                "cost": 0.0
            }

    def _classify_with_transformers(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify using HuggingFace Transformers

        Free, local, no API costs
        """
        # Categories for zero-shot classification
        categories = [
            "Social demographics culture",
            "Technological AI robotics",
            "Economic markets finance",
            "Environmental climate ecology",
            "Political policy regulation",
            "spiritual ethics values"
        ]

        # Combine title and abstract
        text = f"{signal['title']} {signal['content']['abstract'][:300]}"

        try:
            # Zero-shot classification
            result = self.classifier(text, categories)

            # Map to STEEPs
            label_map = {
                "Social demographics culture": "S",
                "Technological AI robotics": "T",
                "Economic markets finance": "E",
                "Environmental climate ecology": "E",
                "Political policy regulation": "P",
                "spiritual ethics values": "s"
            }

            top_label = result['labels'][0]
            category = label_map.get(top_label, "T")
            confidence = result['scores'][0]

            return {
                "category": category,
                "confidence": float(confidence),
                "reasoning": f"Matched: {top_label}",
                "method": "transformers_bart",
                "cost": 0.0  # Free!
            }

        except Exception as e:
            print(f"[ERROR] Transformers classification failed: {e}")
            return {
                "category": signal['preliminary_category'],
                "confidence": 0.6,
                "reasoning": "Transformers failed, using preliminary",
                "method": "fallback",
                "cost": 0.0
            }

    def _parse_text_response(self, text: str) -> Dict[str, Any]:
        """Parse non-JSON text response"""
        # Try to extract category from text
        category = "T"  # Default

        if "S" in text or "Social" in text:
            category = "S"
        elif "T" in text or "Technological" in text:
            category = "T"
        elif "E" in text or "Economic" in text or "Environmental" in text:
            category = "E"
        elif "P" in text or "Political" in text:
            category = "P"
        elif "s" in text or "spiritual" in text:
            category = "s"

        return {
            "category": category,
            "confidence": 0.7,
            "reasoning": text[:200],
            "method": "text_parsing",
            "cost": 0.0
        }

    def classify_batch(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Classify multiple signals

        Args:
            signals: List of signals to classify

        Returns:
            List of classification results
        """
        results = []

        for i, signal in enumerate(signals):
            if (i + 1) % 10 == 0:
                print(f"[PROGRESS] Classified {i+1}/{len(signals)} signals...")

            result = self.classify_signal(signal)
            results.append(result)

        return results


# Usage example
if __name__ == "__main__":
    # Test with a sample signal
    test_signal = {
        "title": "AI Ethics in Healthcare Decision Making",
        "content": {
            "abstract": "This paper discusses the ethical implications of AI systems in healthcare..."
        },
        "preliminary_category": "T"
    }

    # Option 1: Ollama (recommended)
    try:
        classifier = LocalLLMClassifier(model_type="ollama")
        result = classifier.classify_signal(test_signal)
        print("\nOllama Result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Ollama not available: {e}")

    # Option 2: Transformers (backup)
    try:
        classifier = LocalLLMClassifier(model_type="transformers")
        result = classifier.classify_signal(test_signal)
        print("\nTransformers Result:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Transformers not available: {e}")
