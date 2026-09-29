from abc import ABC, abstractmethod
from typing import Any


class ComputerSurface(ABC):

    @abstractmethod
    async def start(self) -> None:
        """Start the computer-control session."""
        pass

    @abstractmethod
    async def navigate(self, target: str) -> None:
        """Navigate to an application or URL."""
        pass

    @abstractmethod
    async def observe(self) -> dict[str, Any]:
        """Return a structured observation of the current UI."""
        pass

    @abstractmethod
    async def click(self, target: dict[str, Any]) -> None:
        """Click a UI control."""
        pass

    @abstractmethod
    async def type_text(
        self,
        target: dict[str, Any],
        value: str
    ) -> None:
        """Enter text into a UI control."""
        pass

    @abstractmethod
    async def screenshot(self, path: str) -> None:
        """Capture the current screen."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the computer-control session."""
        pass