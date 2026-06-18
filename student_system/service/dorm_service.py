"""宿舍服务"""
from repository.dorm_room_repo import DormRoomRepo
from repository.dorm_assignment_repo import DormAssignmentRepo
from entity.dorm_room import DormRoom
from entity.dorm_assignment import DormAssignment
from entity.base import SessionLocal
from datetime import date


class DormService:
    def __init__(self):
        self._session = SessionLocal()
        self.room_repo = DormRoomRepo(session=self._session)
        self.assignment_repo = DormAssignmentRepo(session=self._session)

    def close(self):
        self.room_repo.close()
        self.assignment_repo.close()
        self._session.close()

    # ---- 房间管理 ----
    def get_rooms(self, page=1, page_size=10, filters=None):
        return self.room_repo.filter_paginate(filters or [], page, page_size,
                                              DormRoom.room_id)

    def get_buildings(self):
        """获取楼栋列表"""
        buildings = self.room_repo.db.query(DormRoom.building).distinct().all()
        return [b[0] for b in buildings]

    def get_available_rooms(self):
        """获取有空床位的房间"""
        return self.room_repo.db.query(DormRoom).filter(
            DormRoom.occupied < DormRoom.capacity
        ).all()

    def create_room(self, data: dict):
        return self.room_repo.create(DormRoom(**data))

    def update_room(self, room_id, data: dict):
        ALLOWED_FIELDS = {'building', 'room_number', 'capacity', 'gender_limit', 'phone'}
        filtered_data = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
        room = self.room_repo.get_by_id(room_id)
        if not room:
            return None
        for k, v in filtered_data.items():
            if v is not None and v != '' and hasattr(room, k):
                setattr(room, k, v)
        self.room_repo.db.commit()
        return room

    def delete_room(self, room_id):
        return self.room_repo.delete_by_id(room_id)

    # ---- 住宿分配 ----
    def get_assignments(self, page=1, page_size=10, filters=None):
        return self.assignment_repo.filter_paginate(filters or [], page, page_size,
                                                    DormAssignment.assign_id.desc())

    def assign(self, data: dict):
        """分配宿舍（使用行级锁防止并发超卖）"""
        from sqlalchemy import select
        room_id = data.get('room_id')
        student_id = data.get('student_id', '')

        # 使用 SELECT FOR UPDATE 锁定房间行，防止并发分配导致超卖
        room = self._session.execute(
            select(DormRoom).where(DormRoom.room_id == room_id).with_for_update()
        ).scalar_one_or_none()

        if not room:
            return False, '房间不存在'
        if room.occupied >= room.capacity:
            return False, '房间已满'

        # 检查性别限制
        gender_limit = room.gender_limit or ''
        if gender_limit and gender_limit != '不限':
            from entity.student import Student
            student = self._session.query(Student).filter(Student.student_id == student_id).first()
            if student and student.gender and student.gender != gender_limit:
                gender_map = {'M': '男', 'F': '女'}
                limit_display = gender_map.get(gender_limit, gender_limit)
                return False, f'该房间仅限{limit_display}生入住'

        # 检查学生是否已分配
        existing = self._session.query(DormAssignment).filter(
            DormAssignment.student_id == student_id,
            DormAssignment.status == '在住'
        ).first()
        if existing:
            return False, '该学生已有宿舍，请先退宿'

        try:
            assignment = DormAssignment(
                student_id=student_id,
                room_id=room_id,
                bed_number=data.get('bed_number', ''),
                check_in_date=data.get('check_in_date', date.today()),
                status='在住'
            )
            self.assignment_repo.create(assignment, auto_commit=False)

            # 更新房间入住人数
            room.occupied = (room.occupied or 0) + 1

            self.room_repo.db.commit()
            return True, '分配成功'
        except Exception:
            self.room_repo.db.rollback()
            raise

    def checkout(self, assign_id: int):
        """退宿"""
        assignment = self.assignment_repo.get_by_id(assign_id)
        if not assignment:
            return False, '分配记录不存在'

        try:
            assignment.status = '已退'
            assignment.check_out_date = date.today()

            room = self.room_repo.get_by_id(assignment.room_id)
            if room and room.occupied > 0:
                room.occupied -= 1

            self.assignment_repo.db.commit()
            return True, '退宿成功'
        except Exception:
            self.assignment_repo.db.rollback()
            raise
