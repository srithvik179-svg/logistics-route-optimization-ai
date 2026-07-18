from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ApplicationState(BaseModel):
    dataset_loaded: bool = False
    validation_passed: bool = False
    repository_ready: bool = False
    application_ready: bool = False
    last_load_time: Optional[str] = None
    repository_health: str = "DEGRADED"  # "HEALTHY" | "WARNING" | "DEGRADED"

class StateManager:
    """Manages application-wide loading, validation, and repository ready states."""
    
    def __init__(self):
        self._state = ApplicationState()
        
    def get_state(self) -> ApplicationState:
        """Returns the current application state copy."""
        return self._state
        
    def update_state(
        self,
        dataset_loaded: Optional[bool] = None,
        validation_passed: Optional[bool] = None,
        repository_ready: Optional[bool] = None,
        repository_health: Optional[str] = None
    ) -> ApplicationState:
        """Atomically updates state flags and derives overall application readiness."""
        if dataset_loaded is not None:
            self._state.dataset_loaded = dataset_loaded
            if dataset_loaded:
                self._state.last_load_time = datetime.now().isoformat()
                
        if validation_passed is not None:
            self._state.validation_passed = validation_passed
            
        if repository_ready is not None:
            self._state.repository_ready = repository_ready
            
        if repository_health is not None:
            self._state.repository_health = repository_health

        # Compute general application readiness
        self._state.application_ready = (
            self._state.dataset_loaded and 
            self._state.validation_passed and 
            self._state.repository_ready
        )
        
        return self._state

# Singleton instance for platform-wide reuse
state_manager = StateManager()
