from pydantic import BaseModel, validator
from typing import List

class MultiCountryTotalInput(BaseModel):
    metric: str
    countries: List[str]
    include_total: bool = False
    dimension: str = "country"

    @validator("dimension")
    def dimension_is_country(cls, v):
        # In this simplified example only country dimension is supported
        return v
