from pydantic import BaseModel
from typing import List

class ResponseModuleManageDto(BaseModel):
    isSuccess: bool
    cctvIdListOfRunningActor: List[int]
    