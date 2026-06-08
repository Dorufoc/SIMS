from repository.base import BaseRepo
from entity.grade_scale import GradeScale


class GradeScaleRepo(BaseRepo):
    model = GradeScale
    field_map = {}
