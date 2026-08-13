from abc import ABC
from abc import abstractmethod

class BaseAgent(ABC):

    @abstractmethod
    async def execute(
        self,
        task: str,
    ):
        """
        Execute the benchmark task.
        """
        pass