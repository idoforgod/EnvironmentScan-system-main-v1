"""
Pytest configuration and shared fixtures
"""
import pytest
import json
import os
import shutil
from datetime import datetime
from pathlib import Path


@pytest.fixture
def project_root():
    """Return project root directory"""
    return Path(__file__).parent.parent / "env-scanning"


@pytest.fixture
def date_str():
    """Current date string in YYYY-MM-DD format"""
    return datetime.now().strftime('%Y-%m-%d')


@pytest.fixture
def sample_raw_scan():
    """Sample raw scan data with realistic structure"""
    return {
        "scan_metadata": {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "parallelization": "agent_swarm_multiprocessing",
            "execution_mode": "parallel",
            "agents_used": ["arxiv", "blog", "policy", "patent"],
            "total_items": 5,
            "total_sources_scanned": 4
        },
        "items": [
            {
                "id": "arxiv:2026.12345",
                "title": "Novel Quantum Computing Breakthrough in Error Correction",
                "abstract": "We present a new approach to quantum error correction that reduces error rates by 50%...",
                "source": {
                    "type": "arxiv",
                    "url": "https://arxiv.org/abs/2026.12345",
                    "name": "arXiv",
                    "date": "2026-01-29"
                },
                "metadata": {
                    "authors": ["Zhang, L.", "Kim, S."],
                    "categories": ["quant-ph", "cs.ET"],
                    "citations": 0
                }
            },
            {
                "id": "blog:ai-trends-01",
                "title": "AI Adoption Accelerating in Healthcare Sector",
                "abstract": "New survey shows 67% of hospitals now use AI-powered diagnostics...",
                "source": {
                    "type": "blog",
                    "url": "https://techblog.com/ai-healthcare-2026",
                    "name": "TechBlog",
                    "date": "2026-01-28"
                },
                "metadata": {
                    "author": "Johnson, M.",
                    "tags": ["AI", "healthcare", "adoption"]
                }
            },
            {
                "id": "policy:fed-reg-2026-5432",
                "title": "New Federal Regulations on AI Safety Standards",
                "abstract": "The Department of Commerce announces new mandatory AI safety testing requirements...",
                "source": {
                    "type": "policy",
                    "url": "https://federalregister.gov/2026-5432",
                    "name": "Federal Register",
                    "date": "2026-01-27"
                },
                "metadata": {
                    "agency": "Department of Commerce",
                    "regulation_type": "Final Rule"
                }
            },
            {
                "id": "patent:us-2026-0012345",
                "title": "Carbon Capture Using Advanced Nanomaterials",
                "abstract": "A novel method for CO2 capture using graphene-based nanomaterials...",
                "source": {
                    "type": "patent",
                    "url": "https://patents.google.com/patent/US2026012345",
                    "name": "USPTO",
                    "date": "2026-01-26"
                },
                "metadata": {
                    "inventors": ["Park, J.", "Chen, W."],
                    "assignee": "CleanTech Innovations Inc."
                }
            },
            {
                "id": "arxiv:2026.67890",
                "title": "Climate Tipping Points: Updated Models and Predictions",
                "abstract": "We present updated climate models incorporating latest Arctic ice data...",
                "source": {
                    "type": "arxiv",
                    "url": "https://arxiv.org/abs/2026.67890",
                    "name": "arXiv",
                    "date": "2026-01-29"
                },
                "metadata": {
                    "authors": ["Silva, A.", "Nguyen, T."],
                    "categories": ["physics.ao-ph", "eess.SP"],
                    "citations": 2
                }
            }
        ]
    }


@pytest.fixture
def sample_classified_signals():
    """Sample classified signals with STEEPs categories"""
    return {
        "classification_metadata": {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "total_signals": 5,
            "classification_confidence_avg": 0.87,
            "model_used": "claude-sonnet-4.5"
        },
        "signals": [
            {
                "id": "arxiv:2026.12345",
                "category": "T",
                "confidence": 0.95,
                "keywords": ["quantum computing", "error correction", "breakthrough"],
                "significance_score": 8.5
            },
            {
                "id": "blog:ai-trends-01",
                "category": "S",
                "confidence": 0.82,
                "keywords": ["AI adoption", "healthcare", "diagnostics"],
                "significance_score": 7.2
            },
            {
                "id": "policy:fed-reg-2026-5432",
                "category": "P",
                "confidence": 0.91,
                "keywords": ["AI regulation", "safety standards", "federal"],
                "significance_score": 8.8
            },
            {
                "id": "patent:us-2026-0012345",
                "category": "E",
                "confidence": 0.88,
                "keywords": ["carbon capture", "climate tech", "nanomaterials"],
                "significance_score": 8.0
            },
            {
                "id": "arxiv:2026.67890",
                "category": "E",
                "confidence": 0.90,
                "keywords": ["climate change", "tipping points", "arctic"],
                "significance_score": 9.1
            }
        ]
    }


@pytest.fixture
def sample_priority_ranked():
    """Sample priority-ranked analysis"""
    return {
        "analysis_metadata": {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "total_signals": 5,
            "high_priority": 2,
            "medium_priority": 2,
            "low_priority": 1
        },
        "ranked_signals": [
            {
                "id": "arxiv:2026.67890",
                "priority": "high",
                "priority_score": 9.1,
                "impact_analysis": {
                    "urgency": 0.92,
                    "magnitude": 0.88,
                    "cross_domain_impact": ["E", "P", "S"]
                }
            },
            {
                "id": "policy:fed-reg-2026-5432",
                "priority": "high",
                "priority_score": 8.8,
                "impact_analysis": {
                    "urgency": 0.85,
                    "magnitude": 0.90,
                    "cross_domain_impact": ["P", "T", "E"]
                }
            },
            {
                "id": "arxiv:2026.12345",
                "priority": "medium",
                "priority_score": 8.5,
                "impact_analysis": {
                    "urgency": 0.75,
                    "magnitude": 0.95,
                    "cross_domain_impact": ["T", "E"]
                }
            },
            {
                "id": "patent:us-2026-0012345",
                "priority": "medium",
                "priority_score": 8.0,
                "impact_analysis": {
                    "urgency": 0.70,
                    "magnitude": 0.85,
                    "cross_domain_impact": ["E", "T"]
                }
            },
            {
                "id": "blog:ai-trends-01",
                "priority": "low",
                "priority_score": 7.2,
                "impact_analysis": {
                    "urgency": 0.65,
                    "magnitude": 0.75,
                    "cross_domain_impact": ["S", "T"]
                }
            }
        ]
    }


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment before all tests"""
    # Create necessary test directories
    test_dirs = [
        "tests/fixtures",
        "tests/e2e",
        "tests/unit",
        "tests/integration"
    ]
    for dir_path in test_dirs:
        os.makedirs(dir_path, exist_ok=True)

    yield

    # Cleanup can be added here if needed
    # Note: We don't clean up by default to allow inspection


@pytest.fixture
def temp_workflow_dir(tmp_path, project_root):
    """Create temporary workflow directory for tests"""
    # Create workflow structure
    workflow_dirs = [
        "raw",
        "filtered",
        "structured",
        "analysis",
        "reports/daily",
        "reports/archive/2026/01",
        "signals",
        "context",
        "logs"
    ]

    for dir_name in workflow_dirs:
        (tmp_path / dir_name).mkdir(parents=True, exist_ok=True)

    return tmp_path


@pytest.fixture
def mock_workflow_status():
    """Mock workflow status for testing"""
    return {
        "workflow_id": f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "status": "in_progress",
        "current_phase": 1,
        "current_step": "1.2",
        "completed_steps": ["1.1"],
        "started_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }


# Performance benchmark helpers
@pytest.fixture
def performance_targets():
    """Expected performance targets from requirements"""
    return {
        "phase1_time": 60,  # Phase 1 should complete in < 60 seconds
        "phase2_time": 40,  # Phase 2 should complete in < 40 seconds
        "phase3_time": 35,  # Phase 3 should complete in < 35 seconds
        "dedup_accuracy": 0.95,  # Deduplication > 95% accuracy
        "classification_accuracy": 0.90,  # Classification > 90% accuracy
        "filter_rate_min": 0.30,  # Filter rate between 30-90%
        "filter_rate_max": 0.90
    }


# Markers
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests (< 5 seconds)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (< 30 seconds)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (< 60 seconds)"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer than 1 minute"
    )
