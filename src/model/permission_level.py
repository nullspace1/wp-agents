"""Permission level management for resources."""

from src.model.enums import OperationType
from src.model.resource_types import PermissionsDict


class PermissionLevel:
    
    def __init__(self, 
                 get : bool, 
                 post : bool, 
                 patch : bool, 
                 delete : bool):
        self.permissions = {
            OperationType.GET: get,
            OperationType.POST: post,
            OperationType.PATCH: patch,
            OperationType.DELETE: delete}
    
    def verify(self, operation : OperationType) -> bool:
        return self.permissions[operation]
    
    def get_permissions(self) -> PermissionsDict:
        return {
            "get": self.permissions[OperationType.GET],
            "post": self.permissions[OperationType.POST],
            "patch": self.permissions[OperationType.PATCH],
            "delete": self.permissions[OperationType.DELETE]
        }
