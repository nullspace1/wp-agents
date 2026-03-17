from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


class ParameterTemplate:    
    def __init__(self, name : str, description : str, type : type, required : bool = True):
        self.name = name
        self.description = description
        self.type = type
        self.required = required
        
    def validate(self, value : Any) -> bool:
        return isinstance(value, self.type)
