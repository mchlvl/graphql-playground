from db import database
import strawberry

@strawberry.type
class DbManagementMutation:
    @strawberry.mutation
    async def clear_all_data(self) -> bool:
        await database.execute(
            "TRUNCATE TABLE tag_assignments, tags, models, insights, executions, workflows CASCADE"
        )
        return True

    @strawberry.mutation
    async def populate_sample_data(self) -> bool:
        wf = await database.fetch_one(
            "INSERT INTO workflows (name) VALUES ('Boring WF') RETURNING *"
        )
        ex = await database.fetch_one(
            "INSERT INTO executions (name, workflow_id) VALUES ('Run 1', :wf_id) RETURNING *",
            {"wf_id": wf["id"]},
        )
        ex2 = await database.fetch_one(
            "INSERT INTO executions (name, workflow_id) VALUES ('Run 2', :wf_id) RETURNING *",
            {"wf_id": wf["id"]},
        )
        ins = await database.fetch_one(
            "INSERT INTO insights (name, data, execution_id) VALUES ('QA', 'Looks good', :ex_id) RETURNING *",
            {"ex_id": ex["id"]},
        )
        model = await database.fetch_one(
            "INSERT INTO models (name, model_version, execution_id) VALUES ('TinyModel', 'v1.2', :ex_id) RETURNING *",
            {"ex_id": ex["id"]},
        )
        model2 = await database.fetch_one(
            "INSERT INTO models (name, model_version, execution_id) VALUES ('TinyModel', 'v2.2', :ex_id) RETURNING *",
            {"ex_id": ex["id"]},
        )
        tag = await database.fetch_one(
            "INSERT INTO tags (key, value) VALUES ('modelType', 'BAM') RETURNING *"
        )
        await database.execute_many(
            "INSERT INTO tag_assignments (tag_id, target_type, target_id) VALUES (:tag_id, :type, :id)",
            [
                {"tag_id": tag["id"], "type": "workflow", "id": wf["id"]},
                {"tag_id": tag["id"], "type": "execution", "id": ex["id"]},
                {"tag_id": tag["id"], "type": "execution", "id": ex2["id"]},
                {"tag_id": tag["id"], "type": "insight", "id": ins["id"]},
                {"tag_id": tag["id"], "type": "model", "id": model["id"]},
                {"tag_id": tag["id"], "type": "model", "id": model2["id"]},
            ],
        )
        return True

    @strawberry.mutation
    async def drop_all_tables(self) -> bool:
        try:
            await database.execute("DROP SCHEMA public CASCADE;")
            await database.execute("CREATE SCHEMA public;")
            return True
        except Exception as e:
            print(f"Error dropping tables: {e}")
            return False

    @strawberry.mutation
    async def create_all_tables(self) -> bool:
        query = """
        CREATE TABLE workflows (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        _ = await database.fetch_one(query)
        query = """
        CREATE TABLE executions (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            workflow_id INT REFERENCES workflows(id) ON DELETE CASCADE
        )
        """
        _ = await database.fetch_one(query)
        query = """
        CREATE TABLE models (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            model_version VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            execution_id INTEGER REFERENCES executions(id) ON DELETE SET NULL
        )
        """
        _ = await database.fetch_one(query)
        query = """
        CREATE TABLE insights (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            execution_id INT REFERENCES executions(id) ON DELETE SET NULL,
            workflow_id INT REFERENCES workflows(id) ON DELETE SET NULL,
            model_id INT REFERENCES models(id) ON DELETE SET NULL
        )
        """
        _ = await database.fetch_one(query)
        query = """
        CREATE TYPE tag_target_type AS ENUM ('workflow', 'execution', 'insight', 'model')
        """
        _ = await database.fetch_one(query)
        query = """
        CREATE TABLE tags (
            id SERIAL PRIMARY KEY,
            key VARCHAR(100) NOT NULL,
            value TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(key, value)  -- avoid duplicates like (env, prod)
        )
        """
        _ = await database.fetch_one(query)
        query = """
        CREATE TABLE tag_assignments (
            id SERIAL PRIMARY KEY,
            tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
            target_type tag_target_type NOT NULL,
            target_id INTEGER NOT NULL
        )
        """
        _ = await database.fetch_one(query)
        return True
