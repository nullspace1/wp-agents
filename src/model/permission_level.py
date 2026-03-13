"""Permission level management for resources."""

from model.enums import OperationType


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
    
    def get_permissions(self) -> list[str]:
        return [op.value for op, allowed in self.permissions.items() if allowed]
