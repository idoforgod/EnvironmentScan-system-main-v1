"""
Entity Extractor - Simple NER for Environmental Scanning

Extracts named entities (organizations, technologies, concepts) from text.
Used for Stage 4 deduplication (entity matching).
"""

import re
from typing import List, Set


class EntityExtractor:
    """Simple rule-based entity extractor for technical/policy documents."""

    # Common organization patterns
    ORGANIZATIONS = {
        # Tech companies
        'OpenAI', 'Google', 'Microsoft', 'Meta', 'Amazon', 'Apple', 'Tesla',
        'NVIDIA', 'Intel', 'AMD', 'IBM', 'Oracle', 'Salesforce',

        # Research institutions
        'MIT', 'Stanford', 'Harvard', 'Berkeley', 'CMU', 'Caltech',
        'NIST', 'NASA', 'DARPA', 'NSF',

        # Government agencies
        'EPA', 'FDA', 'FCC', 'DOE', 'DOD', 'HHS', 'USDA',
        'White House', 'Congress', 'Senate',

        # International orgs
        'WHO', 'UN', 'EU', 'WTO', 'IMF', 'World Bank', 'OECD',

        # Universities (patterns)
        'University', 'Institute', 'Laboratory', 'Labs',
    }

    # Technology terms
    TECHNOLOGIES = {
        # AI/ML
        'GPT', 'ChatGPT', 'BERT', 'Transformer', 'LLM', 'Neural Network',
        'Deep Learning', 'Machine Learning', 'Artificial Intelligence', 'AI',

        # Computing
        'Quantum Computing', 'Blockchain', 'Cloud Computing', 'Edge Computing',
        'IoT', 'Internet of Things', '5G', '6G',

        # Biotech
        'CRISPR', 'Gene Editing', 'mRNA', 'Vaccine', 'Biotechnology',

        # Energy
        'Solar', 'Wind', 'Nuclear', 'Fusion', 'Battery', 'Hydrogen',
        'Renewable Energy', 'Carbon Capture',

        # Other
        'Autonomous Vehicle', 'Drone', 'Robot', 'Satellite',
    }

    # Policy/regulation terms
    POLICY_TERMS = {
        'Regulation', 'Executive Order', 'Bill', 'Act', 'Policy',
        'Framework', 'Standard', 'Guideline', 'Directive',
        'Treaty', 'Agreement', 'Protocol',
    }

    @classmethod
    def extract(cls, text: str, max_entities: int = 20) -> List[str]:
        """
        Extract named entities from text.

        Args:
            text: Input text to extract entities from
            max_entities: Maximum number of entities to return

        Returns:
            List of unique entity strings
        """
        if not text:
            return []

        entities: Set[str] = set()

        # 1. Extract known organizations
        for org in cls.ORGANIZATIONS:
            if org.lower() in text.lower():
                entities.add(org)

        # 2. Extract known technologies
        for tech in cls.TECHNOLOGIES:
            if tech.lower() in text.lower():
                entities.add(tech)

        # 3. Extract policy terms
        for term in cls.POLICY_TERMS:
            if term.lower() in text.lower():
                entities.add(term)

        # 4. Extract capitalized phrases (likely proper nouns)
        # Pattern: 2-4 consecutive capitalized words
        capitalized_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b'
        matches = re.findall(capitalized_pattern, text)
        for match in matches:
            # Filter out common words
            if not any(word in match for word in ['The', 'This', 'That', 'These', 'Those']):
                if len(match) > 3:  # At least 4 characters
                    entities.add(match)

        # 5. Extract acronyms (2-6 uppercase letters)
        acronym_pattern = r'\b([A-Z]{2,6})\b'
        matches = re.findall(acronym_pattern, text)
        for match in matches:
            # Filter out common non-acronyms
            if match not in ['AI', 'ML', 'IT', 'US', 'UK']:
                if len(match) >= 3:  # At least 3 letters
                    entities.add(match)

        # 6. Extract version numbers and model names
        # e.g., "GPT-4", "Model-3", "v2.0"
        model_pattern = r'\b([A-Z][a-zA-Z0-9]*-\d+(?:\.\d+)?)\b'
        matches = re.findall(model_pattern, text)
        entities.update(matches)

        # Sort by length (longer = more specific) and return top N
        sorted_entities = sorted(entities, key=len, reverse=True)
        return sorted_entities[:max_entities]

    @classmethod
    def extract_from_signal(cls, signal: dict) -> List[str]:
        """
        Extract entities from a signal dictionary.

        Args:
            signal: Signal dictionary with 'title' and 'content'

        Returns:
            List of unique entities
        """
        # Combine title and abstract for entity extraction
        text_parts = []

        if signal.get('title'):
            text_parts.append(signal['title'])

        if isinstance(signal.get('content'), dict):
            if signal['content'].get('abstract'):
                text_parts.append(signal['content']['abstract'])

        combined_text = ' '.join(text_parts)
        return cls.extract(combined_text)


# Convenience function
def extract_entities(text: str, max_entities: int = 20) -> List[str]:
    """Extract entities from text. Convenience wrapper."""
    return EntityExtractor.extract(text, max_entities)
