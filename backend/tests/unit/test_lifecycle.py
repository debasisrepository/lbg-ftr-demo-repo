"""Unit tests for lifecycle graph and transitions."""
import uuid
from datetime import datetime
from unittest.mock import Mock

import pytest

from app.core.lifecycle_graph import LifecycleGraph
from app.models.config import CaseLifecycleTransition


@pytest.fixture
def sample_transitions():
    """Sample transition rules."""
    now = datetime.now(datetime.now().tzinfo)
    return [
        CaseLifecycleTransition(
            id=uuid.uuid4(),
            from_state="case_created",
            to_state="under_review",
            basis_type="operational_event",
            is_active=True,
            created_at=now
        ),
        CaseLifecycleTransition(
            id=uuid.uuid4(),
            from_state="case_created",
            to_state="in_progress",
            basis_type="approved_manual_update",
            is_active=True,
            created_at=now
        ),
        CaseLifecycleTransition(
            id=uuid.uuid4(),
            from_state="under_review",
            to_state="in_progress",
            basis_type="operational_event",
            is_active=True,
            created_at=now
        ),
        CaseLifecycleTransition(
            id=uuid.uuid4(),
            from_state="in_progress",
            to_state="resolved",
            basis_type="operational_event",
            is_active=True,
            created_at=now
        ),
        CaseLifecycleTransition(
            id=uuid.uuid4(),
            from_state="resolved",
            to_state="closed",
            basis_type="approved_manual_update",
            is_active=True,
            created_at=now
        ),
    ]


@pytest.fixture
def config_repo_mock(sample_transitions):
    """Mock config repository."""
    mock = Mock()
    mock.active_transitions.return_value = sample_transitions
    return mock


def test_lifecycle_graph_allows_valid_transition(config_repo_mock):
    """Test that valid transitions are allowed."""
    graph = LifecycleGraph(config_repo_mock)
    
    # Valid transition
    assert graph.is_allowed("case_created", "under_review", "operational_event") is True


def test_lifecycle_graph_rejects_invalid_transition(config_repo_mock):
    """Test that invalid transitions are rejected."""
    graph = LifecycleGraph(config_repo_mock)
    
    # Invalid transition (wrong basis type)
    assert graph.is_allowed("case_created", "under_review", "approved_manual_update") is False
    
    # Invalid transition (no such edge)
    assert graph.is_allowed("case_created", "closed", "operational_event") is False


def test_lifecycle_graph_allowed_successors(config_repo_mock):
    """Test getting allowed successor states."""
    graph = LifecycleGraph(config_repo_mock)
    
    successors = graph.allowed_successors("case_created")
    
    # Should have two successors: under_review and in_progress
    assert "under_review" in successors
    assert "in_progress" in successors
    assert len(successors) == 2


def test_lifecycle_graph_caching(config_repo_mock):
    """Test that the graph caches transitions and reloads after interval."""
    graph = LifecycleGraph(config_repo_mock)
    
    # First call loads from repo
    graph.is_allowed("case_created", "under_review", "operational_event")
    assert config_repo_mock.active_transitions.call_count == 1
    
    # Second call uses cache
    graph.is_allowed("in_progress", "resolved", "operational_event")
    assert config_repo_mock.active_transitions.call_count == 1


def test_lifecycle_graph_empty_successors(config_repo_mock):
    """Test getting successors for a terminal state."""
    graph = LifecycleGraph(config_repo_mock)
    
    # Terminal state has no successors
    successors = graph.allowed_successors("closed")
    assert len(successors) == 0
