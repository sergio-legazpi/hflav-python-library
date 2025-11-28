import json
from gitlab import Gitlab, GitlabGetError

from hflav_zenodo.exceptions.source_exceptions import (
    NoSchemaFoundInsideGitlabRepository,
    NoVersionTagFound,
)
from hflav_zenodo.logger import get_logger
from hflav_zenodo.source.source_gitlab_interface import SourceGitlabInterface

logger = get_logger(__name__)


class SourceGitlabClient(SourceGitlabInterface):
    def __init__(self):
        gl = Gitlab("https://gitlab.cern.ch")
        self.project = gl.projects.get("hflav/shared/hflav-fair")

    def _get_file_content(self, file_path, ref="main"):
        """Get the content of a file in the project at a specific ref (branch/tag)."""
        file = self.project.files.get(file_path=file_path, ref=ref)
        content = file.decode()
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        return content

    def _get_tag_name(self, tag_name):
        """Get a tag by its name."""
        try:
            return self.project.tags.get(tag_name).name
        except GitlabGetError as e:
            raise NoVersionTagFound(
                message=f"Tag '{tag_name}' not found in the GitLab repository",
                details=str(e),
            )

    def _search_schema(self, path=""):
        try:
            items = self.project.repository_tree(path=path, recursive=False)
            for item in items:
                if item["type"] == "tree":
                    return self._search_schema(item["path"])
                elif item["type"] == "blob":
                    if item["name"].endswith(".schema"):
                        return item
        except Exception as e:
            raise NoSchemaFoundInsideGitlabRepository(
                message="No schema found inside the GitLab repository",
                details=str(e),
            )

    def get_schema_inside_repository(self, tag_version="main") -> dict:
        schema = self._search_schema("")
        file_path = schema["path"]
        tag_name = self._get_tag_name(tag_version)
        content = self._get_file_content(file_path, ref=tag_name)
        try:
            schema_dict = json.loads(content)
            return schema_dict
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in schema file: {e}")
