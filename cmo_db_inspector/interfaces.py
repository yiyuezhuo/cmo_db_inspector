
from typing import Protocol

class DbPathProvider(Protocol):
    def get_db_path(self, data) -> str:
        ...
    def get_init_db_path(self) -> str:
        ...
    def get_db_inputs(self) -> set:
        ...
