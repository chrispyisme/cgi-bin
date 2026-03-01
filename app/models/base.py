from lib.data.model.base import BaseModel
from lib.data.model.AbstractModel import AbstractModel
from lib.data.source.contracts import CrudInterface
from typing import Optional, Dict, Any
from lib.data.source.abstract import AbstractDatasource
class LayoutModel(AbstractModel):
    def __init__(self, datasource:CrudInterface, data:Optional[Dict[str, Any]]):
        super().__init__(datasource, data)

    def get_template(self):
        return self.get("base_template")
    
    def get_links(self, section:str = "main") -> Dict[str, Any]:
        links = self.get("links") or {}