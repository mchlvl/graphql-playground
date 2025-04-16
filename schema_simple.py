from db import database
import strawberry
from datetime import datetime
from typing import Optional
from strawberry.tools import merge_types
from schema_db_management import DbManagementMutation

# ------------- TYPES ------------- #


@strawberry.type
class Workflow:
    id: int
    name: str
    created_at: datetime

    @strawberry.field
    async def executions(self) -> list["Execution"]:
        query = "SELECT * FROM executions WHERE workflow_id = :id"
        results = await database.fetch_all(query, {"id": self.id})
        return [Execution(**r) for r in results]

    @strawberry.field
    async def models(self) -> list["Model"]:
        query = """
        SELECT m.* FROM models m
        JOIN executions e ON m.execution_id = e.id
        WHERE e.workflow_id = :workflow_id
        """
        rows = await database.fetch_all(query, {"workflow_id": self.id})
        return [Model(**r) for r in rows]

    @strawberry.field
    async def model_count(self) -> int:
        query = """
        SELECT COUNT(*) FROM models m
        JOIN executions e ON m.execution_id = e.id
        WHERE e.workflow_id = :workflow_id
        """
        row = await database.fetch_one(query, {"workflow_id": self.id})
        return row[0] if row else 0


@strawberry.type
class Execution:
    id: int
    name: str
    created_at: datetime
    workflow_id: int

    @strawberry.field
    async def workflow(self) -> Workflow | None:
        query = "SELECT * FROM workflows WHERE id = :id"
        row = await database.fetch_one(query, {"id": self.workflow_id})
        return Workflow(**row) if row else None

    @strawberry.field
    async def models(self) -> list["Model"]:
        query = "SELECT * FROM models WHERE execution_id = :execution_id"
        rows = await database.fetch_all(query, {"execution_id": self.id})
        return [Model(**r) for r in rows]

    @strawberry.field
    async def model_count(self) -> int:
        query = "SELECT COUNT(*) FROM models WHERE execution_id = :execution_id"
        row = await database.fetch_one(query, {"execution_id": self.id})
        return row[0] if row else 0

@strawberry.type
class Model:
    id: int
    name: str
    model_version: str
    created_at: datetime
    execution_id: int

    @strawberry.field
    async def execution(self) -> Execution | None:
        query = "SELECT * FROM executions WHERE id = :id"
        row = await database.fetch_one(query, {"id": self.execution_id})
        return Execution(**row) if row else None

    @strawberry.field
    async def workflow(self) -> Workflow | None:
        query = """
        SELECT w.* FROM workflows w
        JOIN executions e ON e.workflow_id = w.id
        WHERE e.id = :execution_id
        """
        row = await database.fetch_one(query, {"execution_id": self.execution_id})
        return Workflow(**row) if row else None


@strawberry.input
class WorkflowInput:
    name: str


@strawberry.input
class ExecutionInput:
    name: str
    workflow_id: int


@strawberry.input
class ModelInput:
    name: str
    model_version: str
    execution_id: int


@strawberry.type
class Query:
    @strawberry.field
    async def get_workflow(self, id: int) -> Workflow | None:
        query = "SELECT * FROM workflows WHERE id = :id"
        row = await database.fetch_one(query, {"id": id})
        return Workflow(**row) if row else None

    @strawberry.field
    async def list_workflows(self) -> list[Workflow]:
        query = "SELECT * FROM workflows ORDER BY created_at DESC"
        rows = await database.fetch_all(query)
        return [Workflow(**r) for r in rows]

    @strawberry.field
    async def list_executions(self) -> list[Execution]:
        query = "SELECT * FROM executions ORDER BY created_at DESC"
        rows = await database.fetch_all(query)
        return [Execution(**r) for r in rows]

    @strawberry.field
    async def list_models(self, model_version: Optional[str] = None) -> list[Model]:
        conditions = []
        parameters = {}
        if model_version:
            conditions.append("m.model_version = :model_version")
            parameters["model_version"] = model_version

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT m.* FROM models m {where_clause} ORDER BY m.created_at DESC"
        rows = await database.fetch_all(query, parameters)
        return [Model(**r) for r in rows]


# ------------- MUTATIONS ------------- #


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def create_workflow(self, input: WorkflowInput) -> Workflow:
        query = "INSERT INTO workflows (name) VALUES (:name) RETURNING *"
        row = await database.fetch_one(query, input.__dict__)
        return Workflow(**row)

    @strawberry.mutation
    async def create_execution(self, input: ExecutionInput) -> Execution:
        query = "INSERT INTO executions (name, workflow_id) VALUES (:name, :workflow_id) RETURNING *"
        row = await database.fetch_one(query, input.__dict__)
        return Execution(**row)

    @strawberry.mutation
    async def create_model(self, input: ModelInput) -> Model:
        query = """
        INSERT INTO models (name, model_version, execution_id)
        VALUES (:name, :model_version, :execution_id)
        RETURNING *
        """
        row = await database.fetch_one(query, input.__dict__)
        return Model(**row)


mutations = merge_types("Mutation", (Mutation, DbManagementMutation))
schema = strawberry.Schema(Query, mutation=mutations)
