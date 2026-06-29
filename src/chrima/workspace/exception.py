from uuid import UUID


class WorkspaceNotFoundException(Exception):
    def __init__(self, workspace_id: UUID):
        super().__init__("Workspace not found")
        self.workspace_id = workspace_id
