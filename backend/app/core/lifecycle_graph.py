"""Lifecycle graph for validating case state transitions."""
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, Set, Tuple

from app.repositories.config_repository import ConfigRepository


class LifecycleGraph:
    """
    Validates case lifecycle transitions against allowed edges.
    
    Loads allowed transitions from case_lifecycle_transitions table
    and caches them for 60 seconds to avoid repeated database queries.
    """
    
    def __init__(self, config_repo: ConfigRepository):
        self.config_repo = config_repo
        self._graph: Dict[Tuple[str, str, str], bool] = {}
        self._last_loaded: datetime | None = None
        self._lock = Lock()
        self._reload_interval = timedelta(seconds=60)
    
    def is_allowed(self, from_state: str, to_state: str, basis_type: str) -> bool:
        """
        Check if a transition is allowed.
        
        Args:
            from_state: Current lifecycle state
            to_state: Target lifecycle state
            basis_type: Type of basis (operational_event, approved_manual_update, etc.)
        
        Returns:
            True if the transition is allowed, False otherwise
        """
        self._refresh_if_needed()
        
        # Check the graph
        key = (from_state, to_state, basis_type)
        return self._graph.get(key, False)
    
    def allowed_successors(self, from_state: str) -> Set[str]:
        """
        Get all allowed successor states from a given state.
        
        Args:
            from_state: Current lifecycle state
        
        Returns:
            Set of allowed successor states
        """
        self._refresh_if_needed()
        
        successors = set()
        for (f, t, _) in self._graph.keys():
            if f == from_state and self._graph[(f, t, _)]:
                successors.add(t)
        
        return successors
    
    def _refresh_if_needed(self) -> None:
        """Refresh the graph if the reload interval has passed."""
        now = datetime.now(datetime.now().tzinfo)
        
        # Double-checked locking pattern
        if self._last_loaded is None or (now - self._last_loaded) >= self._reload_interval:
            with self._lock:
                # Check again inside the lock
                if self._last_loaded is None or (now - self._last_loaded) >= self._reload_interval:
                    self._reload()
    
    def _reload(self) -> None:
        """Reload transitions from the database."""
        transitions = self.config_repo.active_transitions()
        
        # Build the graph
        new_graph = {}
        for transition in transitions:
            key = (transition.from_state, transition.to_state, transition.basis_type)
            new_graph[key] = transition.is_active
        
        self._graph = new_graph
        self._last_loaded = datetime.now(datetime.now().tzinfo)
