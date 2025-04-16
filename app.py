from fastapi import FastAPI
from db import connect, disconnect
from strawberry.fastapi import GraphQLRouter
from schema_simple import schema as schema_simple
from schema_full import schema as schema_full
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_headers=["*"], allow_origins=["*"], allow_methods=["*"]
)

@app.on_event("startup")
async def startup():
    await connect()


@app.on_event("shutdown")
async def shutdown():
    await disconnect()


gql_router = GraphQLRouter(schema_simple)
app.include_router(gql_router, prefix="/graphql")
# gql_router = GraphQLRouter(schema_full)
# app.include_router(gql_router, prefix="/graphql_full")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
