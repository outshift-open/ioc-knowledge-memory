from pydantic import BaseModel, Field, RootModel
from typing import List, Dict, Any
from enum import Enum

# This will be a list of dictionaries (JSON objects)
SoftwareList = RootModel[List[Dict[str, Any]]]

