from db import database
import strawberry
from datetime import datetime
from typing import Optional
from strawberry.tools import merge_types
from schema_db_management import DbManagementMutation

# ------------- TYPES ------------- #


@strawberry.type
class Tag:
    id: int
    key: str
    value: str
    created_at: datetime


async def fetch_tags(target_type: str, target_id: int) -> list[Tag]:
    query = """
    SELECT t.* FROM tags t
    JOIN tag_assignments ta ON ta.tag_id = t.id
    WHERE ta.target_type = :target_type AND ta.target_id = :target_id
    """
    results = await database.fetch_all(
        query, {"target_type": target_type, "target_id": target_id}
    )
    return [Tag(**r) for r in results]


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
    async def insights(self) -> list["Insight"]:
        query = "SELECT * FROM insights WHERE workflow_id = :id"
        results = await database.fetch_all(query, {"id": self.id})
        return [Insight(**r) for r in results]

    @strawberry.field
    async def tags(self) -> list[Tag]:
        return await fetch_tags("workflow", self.id)


@strawberry.type
class Execution:
    id: int
    name: str
    created_at: datetime
    workflow_id: int

    @strawberry.field
    async def insights(self) -> list["Insight"]:
        query = "SELECT * FROM insights WHERE execution_id = :id"
        results = await database.fetch_all(query, {"id": self.id})
        return [Insight(**r) for r in results]

    @strawberry.field
    async def tags(self) -> list[Tag]:
        return await fetch_tags("execution", self.id)

    @strawberry.field
    async def workflow(self) -> Workflow | None:
        query = "SELECT * FROM workflows WHERE id = :id"
        row = await database.fetch_one(query, {"id": self.workflow_id})
        return Workflow(**row) if row else None


@strawberry.type
class Model:
    id: int
    name: str
    model_version: str
    created_at: datetime
    execution_id: int

    @strawberry.field
    async def tags(self) -> list[Tag]:
        return await fetch_tags("model", self.id)

    @strawberry.field
    async def insights(self) -> list["Insight"]:
        query = "SELECT * FROM insights WHERE model_id = :id"
        results = await database.fetch_all(query, {"id": self.id})
        return [Insight(**r) for r in results]

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


@strawberry.type
class Insight:
    id: int
    name: str
    data: str
    created_at: datetime
    workflow_id: int | None
    execution_id: int | None
    model_id: int | None

    @strawberry.field
    async def tags(self) -> list[Tag]:
        return await fetch_tags("insight", self.id)

    @strawberry.field
    async def model(self) -> Model | None:
        if self.model_id is None:
            return None
        query = "SELECT * FROM models WHERE id = :id"
        row = await database.fetch_one(query, {"id": self.model_id})
        return Model(**row) if row else None

    @strawberry.field
    async def execution(self) -> Execution | None:
        if self.execution_id is None:
            return None
        query = "SELECT * FROM executions WHERE id = :id"
        row = await database.fetch_one(query, {"id": self.execution_id})
        return Execution(**row) if row else None

    @strawberry.field
    async def workflow(self) -> Workflow | None:
        if self.workflow_id is None:
            return None
        query = "SELECT * FROM workflows WHERE id = :id"
        row = await database.fetch_one(query, {"id": self.workflow_id})
        return Workflow(**row) if row else None


# ------------- INPUTS ------------- #


@strawberry.input
class WorkflowInput:
    name: str


@strawberry.input
class ExecutionInput:
    name: str
    workflow_id: int


@strawberry.input
class InsightInput:
    name: str
    data: str
    workflow_id: int | None = None
    execution_id: int | None = None
    model_id: int | None = None


@strawberry.input
class ModelInput:
    name: str
    model_version: str
    execution_id: int


@strawberry.input
class TagInput:
    key: str
    value: str


@strawberry.input
class TagAssignmentInput:
    tag_id: int
    target_type: str
    target_id: int


# ------------- QUERIES ------------- #


@strawberry.type
class Query:
    @strawberry.field
    async def get_workflow(self, id: int) -> Workflow | None:
        query = "SELECT * FROM workflows WHERE id = :id"
        row = await database.fetch_one(query, {"id": id})
        return Workflow(**row) if row else None

    @strawberry.field
    async def list_workflows(
        self, tag_key: Optional[str] = None, tag_value: Optional[str] = None
    ) -> list[Workflow]:
        if tag_key and tag_value:
            query = """
            SELECT w.* FROM workflows w
            JOIN tag_assignments ta ON ta.target_type = 'workflow' AND ta.target_id = w.id
            JOIN tags t ON t.id = ta.tag_id
            WHERE t.key = :tag_key AND t.value = :tag_value
            ORDER BY w.created_at DESC
            """
            rows = await database.fetch_all(
                query, {"tag_key": tag_key, "tag_value": tag_value}
            )
        else:
            query = "SELECT * FROM workflows ORDER BY created_at DESC"
            rows = await database.fetch_all(query)
        return [Workflow(**r) for r in rows]

    @strawberry.field
    async def list_executions(
        self, tag_key: Optional[str] = None, tag_value: Optional[str] = None
    ) -> list[Execution]:
        if tag_key and tag_value:
            query = """
            SELECT e.* FROM executions e
            JOIN tag_assignments ta ON ta.target_type = 'execution' AND ta.target_id = e.id
            JOIN tags t ON t.id = ta.tag_id
            WHERE t.key = :tag_key AND t.value = :tag_value
            ORDER BY e.created_at DESC
            """
            rows = await database.fetch_all(
                query, {"tag_key": tag_key, "tag_value": tag_value}
            )
        else:
            query = "SELECT * FROM executions ORDER BY created_at DESC"
            rows = await database.fetch_all(query)
        return [Execution(**r) for r in rows]

    @strawberry.field
    async def list_insights(
        self, tag_key: Optional[str] = None, tag_value: Optional[str] = None
    ) -> list[Insight]:
        if tag_key and tag_value:
            query = """
            SELECT i.* FROM insights i
            JOIN tag_assignments ta ON ta.target_type = 'insight' AND ta.target_id = i.id
            JOIN tags t ON t.id = ta.tag_id
            WHERE t.key = :tag_key AND t.value = :tag_value
            ORDER BY i.created_at DESC
            """
            rows = await database.fetch_all(
                query, {"tag_key": tag_key, "tag_value": tag_value}
            )
        else:
            query = "SELECT * FROM insights ORDER BY created_at DESC"
            rows = await database.fetch_all(query)
        return [Insight(**r) for r in rows]

    @strawberry.field
    async def list_models(
        self,
        tag_key: Optional[str] = None,
        tag_value: Optional[str] = None,
        model_version: Optional[str] = None,
    ) -> list[Model]:
        conditions = []
        parameters = {}

        if tag_key and tag_value:
            conditions.append("""
                m.id IN (
                    SELECT ta.target_id FROM tag_assignments ta
                    JOIN tags t ON t.id = ta.tag_id
                    WHERE ta.target_type = 'model' AND t.key = :tag_key AND t.value = :tag_value
                )
            """)
            parameters["tag_key"] = tag_key
            parameters["tag_value"] = tag_value

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
    async def create_insight(self, input: InsightInput) -> Insight:
        query = """
        INSERT INTO insights (name, data, workflow_id, execution_id, model_id)
        VALUES (:name, :data, :workflow_id, :execution_id, :model_id)
        RETURNING *
        """
        row = await database.fetch_one(query, input.__dict__)
        return Insight(**row)

    @strawberry.mutation
    async def create_model(self, input: ModelInput) -> Model:
        query = """
        INSERT INTO models (name, model_version, execution_id)
        VALUES (:name, :model_version, :execution_id)
        RETURNING *
        """
        row = await database.fetch_one(query, input.__dict__)
        return Model(**row)

    @strawberry.mutation
    async def create_tag(self, input: TagInput) -> Tag:
        query = "INSERT INTO tags (key, value) VALUES (:key, :value) ON CONFLICT DO NOTHING RETURNING *"
        row = await database.fetch_one(query, input.__dict__)
        if row:
            return Tag(**row)
        row = await database.fetch_one(
            "SELECT * FROM tags WHERE key = :key AND value = :value", input.__dict__
        )
        return Tag(**row)

mutations = merge_types("Mutation", (Mutation, DbManagementMutation))
schema = strawberry.Schema(Query, mutation=mutations)
