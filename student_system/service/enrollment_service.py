"""选课服务"""
from repository.enrollment_repo import EnrollmentRepo
from entity.enrollment import Enrollment
from entity.teaching import Teaching
from entity.course import Course


class EnrollmentService:
    def __init__(self):
        self.repo = EnrollmentRepo()

    def close(self):
        self.repo.close()

    def get_available_courses(self, student_id: str):
        """获取可选课程列表 — 返回所有未选的课程"""
        # 已选课程ID（排除退课）
        enrolled_ids = self.repo.db.query(Enrollment.teaching_id).filter(
            Enrollment.student_id == student_id,
            Enrollment.status != '退课'
        ).subquery()

        # 返回所有未选的课程
        q = self.repo.db.query(Teaching).filter(
            ~Teaching.teaching_id.in_(enrolled_ids)
        ).order_by(Teaching.teaching_id)
        return q.all()

    def enroll(self, student_id: str, teaching_id: int):
        """学生选课"""
        # 检查是否已选
        existing = self.repo.find_by(student_id=student_id, teaching_id=teaching_id)
        if existing:
            if existing.status == '退课':
                # 重新选课也要检查容量和时间冲突
                teaching = self.repo.db.query(Teaching).filter(
                    Teaching.teaching_id == teaching_id
                ).first()
                if not teaching:
                    return False, '课程不存在'

                enrolled_count = self.repo.db.query(Enrollment).filter(
                    Enrollment.teaching_id == teaching_id,
                    Enrollment.status != '退课'
                ).count()
                if teaching.capacity is not None and enrolled_count >= teaching.capacity:
                    return False, '课程容量已满'

                if teaching.schedule:
                    if self._check_schedule_conflict(student_id, teaching.schedule, teaching_id):
                        return False, f'与已有课程时间冲突'

                existing.status = '正常'
                self.repo.db.commit()
                return True, '重新选课成功'
            return False, '已选该课程'

        # 检查课程容量
        teaching = self.repo.db.query(Teaching).filter(
            Teaching.teaching_id == teaching_id
        ).first()
        if not teaching:
            return False, '课程不存在'
        
        enrolled_count = self.repo.db.query(Enrollment).filter(
            Enrollment.teaching_id == teaching_id,
            Enrollment.status != '退课'
        ).count()
        if teaching.capacity is not None and enrolled_count >= teaching.capacity:
            return False, '课程容量已满'

        # 检查时间冲突
        if teaching.schedule:
            if self._check_schedule_conflict(student_id, teaching.schedule, teaching_id):
                return False, f'与已有课程时间冲突'

        enrollment = Enrollment(
            student_id=student_id,
            teaching_id=teaching_id,
            status='正常'
        )
        self.repo.create(enrollment)
        return True, '选课成功'

    def _check_schedule_conflict(self, student_id: str, new_schedule: str, exclude_teaching_id=None) -> bool:
        """检查时间冲突，支持部分重叠检测
        
        将 schedule 字符串解析为 (day, start, end) 结构化数据，
        实现真正的时段重叠检测。
        返回 True 表示有冲突。
        """
        new_slots = self._parse_schedule(new_schedule)
        if not new_slots:
            return False

        enrolled_teachings = self.repo.db.query(Enrollment.teaching_id).filter(
            Enrollment.student_id == student_id,
            Enrollment.status != '退课'
        ).all()
        enrolled_t_ids = [e[0] for e in enrolled_teachings]
        if not enrolled_t_ids:
            return False

        existing_teachings = self.repo.db.query(Teaching).filter(
            Teaching.teaching_id.in_(enrolled_t_ids)
        )
        if exclude_teaching_id:
            existing_teachings = existing_teachings.filter(
                Teaching.teaching_id != exclude_teaching_id
            )
        existing_teachings = existing_teachings.all()

        for et in existing_teachings:
            if not et.schedule:
                continue
            existing_slots = self._parse_schedule(et.schedule)
            for ns in new_slots:
                for es in existing_slots:
                    if self._slots_overlap(ns, es):
                        return True
        return False

    @staticmethod
    def _parse_schedule(schedule: str) -> list:
        """解析 schedule 字符串为结构化数据
        
        格式示例: "周一 1-2节", "周二 3-4节;周三 5-6节"
        返回: [{'day': '周一', 'start': 1, 'end': 2}, ...]
        """
        import re
        slots = []
        parts = schedule.replace('；', ';').split(';')
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # 支持 "周一", "周一 1-2节", "周一第1-2节", "周一 1-2节" 等格式
            match = re.match(r'(周[一二三四五六日]|星期一|星期二|星期三|星期四|星期五|星期六|星期日)\s*(?:第)?\s*(\d+)\s*[-~至到]\s*(\d+)\s*节?', part)
            if match:
                day = match.group(1)
                start = int(match.group(2))
                end = int(match.group(3))
                slots.append({'day': day, 'start': start, 'end': end})
            else:
                # 精确匹配：只有周几无节次信息时，不与任何课程冲突
                day_match = re.match(r'(周[一二三四五六日]|星期一|星期二|星期三|星期四|星期五|星期六|星期日)\s*$', part)
                if day_match:
                    slots.append({'day': day_match.group(1), 'start': 0, 'end': 24})
        return slots

    @staticmethod
    def _slots_overlap(slot_a, slot_b) -> bool:
        """判断两个时段是否重叠"""
        if slot_a['day'] != slot_b['day']:
            return False
        return slot_a['start'] < slot_b['end'] and slot_b['start'] < slot_a['end']

    def drop(self, enroll_id: int):
        """退课"""
        enrollment = self.repo.get_by_id(enroll_id)
        if not enrollment:
            return False, '选课记录不存在'
        enrollment.status = '退课'
        self.repo.db.commit()
        return True, '退课成功'

    def get_student_enrollments(self, student_id: str):
        """获取学生选课记录"""
        return self.repo.find_all_by(student_id=student_id)
