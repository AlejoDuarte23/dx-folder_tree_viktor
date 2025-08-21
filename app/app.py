import json
import viktor as vkt  # type: ignore
from pathlib import Path
from typing import Any
from app.data_exchange import get_all_content_from_all_hubs
from app.models import HubData, serialize_folder


class Parametrization(vkt.Parametrization):
    title = vkt.Text("# Data Exchange - Viktor Integration")
    notes = vkt.Text(
        """## Limitations
- The Data Exchange API retrieves only viewable objects (e.g., IFC, RVT, DWG).
- Files like PDF, XLSX, and DOCX are not retrieved by the API.
- The advantage of using this approach is that fewer requests are made, so it is faster."""
    )

class Controller(vkt.Controller):
    parametrization = Parametrization(width=40)

    @vkt.WebView("Folder Structure", duration_guess=40)
    def print_folder_tree_rest(self, params, **kwargs) -> vkt.WebResult:
        # Fetch typed hierarchy (includes DXFolderTree instances)
        integration = vkt.external.OAuth2Integration("aps-integration-viktor")
        token = integration.get_access_token()
        content = get_all_content_from_all_hubs(token=token)

        # Convert Pydantic models (DXFolderTree) into JSON-serializable dicts

        def serialize_content(hubs: dict[str, HubData]) -> dict[str, Any]:
            out: dict[str, Any] = {}
            for hub_id, hub in hubs.items():
                projects_obj: dict[str, Any] = {}
                for proj_id, proj in hub["projects"].items():
                    projects_obj[proj_id] = {
                        "name": proj["name"],
                        "folder_tree": [
                            serialize_folder(ft) for ft in (proj["folder_tree"] or [])
                        ],
                    }
                out[hub_id] = {"name": hub["name"], "projects": projects_obj}
            return out

        serialized = serialize_content(content)

        # Convert the content to JSON
        json_content = json.dumps(serialized, ensure_ascii=False)

        # Load HTML template and inject JSON
        html = (Path(__file__).parent / "FolderBrowser.html").read_text(
            encoding="utf-8"
        )
        html = html.replace("FOLDER_DATA_PLACEHOLDER", json_content)
        return vkt.WebResult(html=html)
