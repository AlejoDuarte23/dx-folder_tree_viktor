from typing import Optional
import httpx
from app.models import DXHub, DXProject, DXFolderTree, DXItem, DXExchange
from app.queries import (
    execute_graphql_query,
    execute_graphql_query_async,
    GET_HUBS,
    GET_PROJECTS,
    GET_TOP_FOLDERS,
    GET_FOLDER_CONTENT,
)

# Parsers
def parse_hubs(data: dict) -> list[DXHub]:
    arr = data.get("hubs", {}).get("results", []) or []
    return [DXHub.model_validate(x) for x in arr]

def parse_projects(data: dict) -> list[DXProject]:
    arr = data.get("projects", {}).get("results", []) or []
    return [DXProject.model_validate(x) for x in arr]

def parse_top_folders(data: dict) -> list[DXFolderTree]:
    # Reuse DXFolderTree for refs (id+name only)
    arr = data.get("project", {}).get("folders", {}).get("results", []) or []
    return [DXFolderTree.model_validate(x) for x in arr]

def parse_folder_tree(data: dict) -> Optional[DXFolderTree]:
    raw = data.get("folder") or {}
    if not raw:
        return None
    # folders have subfolder thus is recursive 
    def _build(node: dict) -> DXFolderTree:
        items = [DXItem.model_validate(i) for i in (node.get("items", {}).get("results", []) or [])]
        exchanges = [DXExchange.model_validate(e) for e in (node.get("exchanges", {}).get("results", []) or [])]
        subfolders_raw = node.get("folders", {}).get("results", []) or []
        # Create shallow child nodes (id+name); caller can expand recursively
        subfolders = [DXFolderTree.model_validate({"id": sf.get("id"), "name": sf.get("name")}) for sf in subfolders_raw]
        return DXFolderTree(
            id=node.get("id"),
            name=node.get("name"),
            items=items,
            exchanges=exchanges,
            folders=subfolders,
        )

    return _build(raw)

def get_hubs(token: str) -> list[DXHub]:
    return parse_hubs(execute_graphql_query(GET_HUBS, token))

def get_projects(token: str, hub_id: str) -> list[DXProject]:
    return parse_projects(execute_graphql_query(GET_PROJECTS, token, {"hubId": hub_id}))

def get_top_folders(token: str, project_id: str) -> list[DXFolderTree]:
    return parse_top_folders(execute_graphql_query(GET_TOP_FOLDERS, token, {"projectId": project_id}))

def get_folder_tree(token: str, folder_id: str) -> DXFolderTree | None:
    return parse_folder_tree(execute_graphql_query(GET_FOLDER_CONTENT, token, {"folderId": folder_id}))


# Async counterparts used by orchestrator
async def get_hubs_async(token: str, *, client: httpx.AsyncClient | None = None) -> list[DXHub]:
    data = await execute_graphql_query_async(GET_HUBS, token, client=client)
    return parse_hubs(data)


async def get_projects_async(
    token: str, hub_id: str, *, client: httpx.AsyncClient | None = None
) -> list[DXProject]:
    data = await execute_graphql_query_async(
        GET_PROJECTS, token, {"hubId": hub_id}, client=client
    )
    return parse_projects(data)


async def get_top_folders_async(
    token: str, project_id: str, *, client: httpx.AsyncClient | None = None
) -> list[DXFolderTree]:
    data = await execute_graphql_query_async(
        GET_TOP_FOLDERS, token, {"projectId": project_id}, client=client
    )
    return parse_top_folders(data)


async def get_folder_tree_async(
    token: str, folder_id: str, *, client: httpx.AsyncClient | None = None
) -> DXFolderTree | None:
    data = await execute_graphql_query_async(
        GET_FOLDER_CONTENT, token, {"folderId": folder_id}, client=client
    )
    return parse_folder_tree(data)
