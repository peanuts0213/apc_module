from typing import Dict, List

from ..dto.module_manage.rule_line_dto import RuleLineDto
from ..dto.socket.result_dto import ResultDto

class Tracking:
  def __init__(self, rule_line_list: list[RuleLineDto], bottom_offset_ratio: int):
    """트래킹 초기화"""
    self.bottom_offset_ratio = bottom_offset_ratio
    self.rule_line_list = rule_line_list
    self.object_positions: Dict[int, tuple[float, float]] = {}  # {obj_id: (x, y)}
    self.crossing_results: Dict[int, bool] = {}  # {obj_id: True/False}

  def check_crossing(self, obj: ResultDto) -> bool | None:
    """객체가 rule_line을 넘었는지 확인"""
    
    x1, y1, x2, y2 = obj.xyxy
    obj_id = obj.id
    center_x = (x1 + x2) / 2
    center_y = y2 - (y2 - y1) * (self.bottom_offset_ratio / 100)
    
    prev_x, prev_y = self.object_positions.get(obj_id, (None, None))
    self.object_positions[obj_id] = (center_x, center_y)
    
    
    if prev_x is None or prev_y is None:
      return None
    
    for rule_line_dto in self.rule_line_list:
      rule_line = rule_line_dto.ruleLine
      
      if len(rule_line) != 2:
        continue

      point_a, point_b = sorted(rule_line, key=lambda p: p.orderIndex)

      ab_x = point_b.x - point_a.x
      ab_y = point_b.y - point_a.y
      ab_len_sq = ab_x**2 + ab_y**2

      # 벡터 AP (A → 현재 객체 위치)
      ap_x = center_x - point_a.x
      ap_y = center_y - point_a.y
      # projection 비율 (dot product)
      proj_ratio = (ap_x * ab_x + ap_y * ab_y) / ab_len_sq

      #   0 <= proj <= 1: 선 내부에 위치한 객체만 crossing 체크
      if proj_ratio < 0 or proj_ratio > 1:
        continue
      
      prev_ap_x = prev_x - point_a.x
      prev_ap_y = prev_y - point_a.y
      curr_ap_x = center_x - point_a.x
      curr_ap_y = center_y - point_a.y
    
      prev_cross = ab_x * prev_ap_y - ab_y * prev_ap_x
      curr_cross = ab_x * curr_ap_y - ab_y * curr_ap_x

      if prev_cross * curr_cross < 0:
        is_in = curr_cross < 0  # 기준선을 아래 방향으로 통과하면 IN
        self.crossing_results[obj_id] = is_in
        print(f"Object {obj_id} crossed the line: {'IN' if is_in else 'OUT'}", flush=True)
        return is_in
    
    return None

  def update_tracking(self, objects: List[ResultDto]):
    """객체 추적 업데이트 및 제거"""
    current_ids = {obj.id for obj in objects}
    to_remove = [
      obj_id for obj_id in self.object_positions if obj_id not in current_ids
    ]
    for obj_id in to_remove:
      self.object_positions.pop(obj_id, None)
      self.crossing_results.pop(obj_id, None)
      print(f"Object {obj_id} no longer detected, removed from tracking")

  def clear(self):
    """트래킹 데이터 초기화"""
    self.object_positions.clear()
    self.crossing_results.clear()