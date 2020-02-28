from abc import ABC, abstractmethod


class ABCPlotting(ABC):
    """
    Abstract method to plot solver result.
    """

    @abstractmethod
    def stack(self, node: str):
        pass

    @abstractmethod
    def exchanges_map(self, t: int, limit: int):
        pass