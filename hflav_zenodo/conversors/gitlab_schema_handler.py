from hflav_zenodo import logger

from hflav_zenodo.conversors.conversor_handler import ConversorHandler
from hflav_zenodo.models.models import Template

logger = logger.get_logger(__name__)


class GitlabSchemaHandler(ConversorHandler):
    """Handler for Gitlab schema conversor.

    It's triggered when the first handler fails and the schema can be found inside Gitlab repository.

    If it cannot handle the request, it passes it to the next handler in the chain.
    """

    def handle(self, template: Template, data_path: str) -> object:
        logger.info("GitlabSchemaHandler: Handling the request...")
        if not self.can_handle(template, data_path):
            logger.info(
                "GitlabSchemaHandler: Cannot handle the request, passing to next handler..."
            )
            return self._next_handler.handle(template, data_path)
        pass

    def can_handle(self, template: Template, data_path: str) -> bool:
        return False

    def set_next(self, handler: "ConversorHandler") -> "ConversorHandler":
        self._next_handler = handler
        return handler
