from pydantic import BaseModel


class ApcEventDto(BaseModel):
  cctvId: int
  areaId: int
  isIn: bool