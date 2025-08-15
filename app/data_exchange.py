from app.crud import get_hubs, get_projects, get_top_folders, get_folder_tree
from app.models import DXFolderTree, ProjectData, HubData

def build_folder_tree_recursively(token: str, folder_id: str) -> DXFolderTree | None:
    root = get_folder_tree(token, folder_id)
    if not root:
        return None
    # Expand shallow child refs
    expanded_children: list[DXFolderTree] = []
    for child in root.folders:
        if not child.id:
            continue
        sub = build_folder_tree_recursively(token, child.id)
        if sub:
            expanded_children.append(sub)
    root.folders = expanded_children
    return root

def print_tree_from_data(folder_data: DXFolderTree, prefix: str = "", is_last: bool = True):
    """
    Prints a nicely formatted ASCII tree with emojis.
    """
    connector = "└─" if is_last else "├─"
    print(f"{prefix}{connector} 📁 {folder_data.name}")
    child_prefix = f"{prefix}   " if is_last else f"{prefix}│  "

    # Prepare children (items, exchanges, then folders)
    children: list[tuple[str, object]] = []
    children += [("item", it) for it in (folder_data.items or [])]
    children += [("exchange", ex) for ex in (folder_data.exchanges or [])]
    children += [("folder", fd) for fd in (folder_data.folders or [])]

    for i, (kind, obj) in enumerate(children):
        last_child = i == len(children) - 1
        c = "└─" if last_child else "├─"
        if kind == "item":
            print(f"{child_prefix}{c} 📄 {obj.name}")
        elif kind == "exchange":
            print(f"{child_prefix}{c} 🔁 {obj.name}")
        else:
            print_tree_from_data(obj, prefix=child_prefix, is_last=last_child)


def get_all_content_from_all_hubs(token: str) -> dict[str, HubData]:
    full_hierarchy: dict[str, HubData] = {}
    # fetch hubs
    hubs = get_hubs(token)  

    for hub in hubs:
        full_hierarchy[hub.id] = {"name": hub.name, "projects": {}}
        # fetch projects per hub
        projects = get_projects(token, hub.id)

        for project in projects:
            project_data: ProjectData = {"name": project.name, "folder_tree": []}
            full_hierarchy[hub.id]["projects"][project.id] = project_data

            try:
                # Get Top folders
                top_folders = get_top_folders(token, project.id)
                for folder in top_folders:
                    if not folder.id:
                        continue
                    # Expand folder tree -> like folder items subfolder items subfolder etc.
                    tree = build_folder_tree_recursively(token, folder.id)
                    if tree:
                        # Print the fully expanded tree, not the shallow folder ref
                        print_tree_from_data(tree)
                        project_data["folder_tree"].append(tree)
            except Exception:
                # skip if fails.
                continue

    return full_hierarchy