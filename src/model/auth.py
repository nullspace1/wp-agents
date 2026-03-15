import uuid

from model.enums import OperationType

type AuthenticationKey = str | dict[str, str]

class KeySet:
    def __init__(self, get : AuthenticationKey | None = None, post : AuthenticationKey | None = None, patch : AuthenticationKey | None = None, delete : AuthenticationKey | None = None):
        self.keys : dict[OperationType, AuthenticationKey | None] = {
            OperationType.GET: get,
            OperationType.POST: post,
            OperationType.PATCH: patch,
            OperationType.DELETE: delete,
        }
    
    def get(self, operation : OperationType) -> AuthenticationKey | None:
        return self.keys.get(operation)

def generate_auth_key() -> AuthenticationKey:
    return str(uuid.uuid4())
