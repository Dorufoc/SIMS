"""模拟数据生成服务 —— 为各表生成随机中文模拟数据"""
import random
import uuid
import math
from datetime import date, timedelta, datetime
from entity.base import SessionLocal
from utils.password_utils import encrypt_password

# ============================================================
# 中文姓名库
# ============================================================
SURNAMES = [
    '王', '李', '张', '刘', '陈', '杨', '黄', '赵', '周', '吴',
    '徐', '孙', '马', '朱', '胡', '郭', '何', '林', '罗', '高',
    '梁', '郑', '谢', '宋', '唐', '韩', '曹', '许', '邓', '冯',
    '彭', '曾', '萧', '田', '董', '潘', '袁', '蔡', '蒋', '余',
    '于', '杜', '叶', '程', '苏', '魏', '吕', '丁', '任', '沈',
]

GIVEN_NAMES = [
    '伟', '芳', '娜', '敏', '静', '丽', '强', '磊', '洋', '勇',
    '艳', '杰', '军', '秀英', '涛', '明', '超', '秀兰', '霞', '平',
    '刚', '桂英', '文', '华', '飞', '玉兰', '斌', '玲', '建国', '国强',
    '志强', '志明', '秀珍', '建军', '建华', '文博', '海燕', '小龙', '雪', '慧',
    '鑫', '宇', '浩', '然', '博', '毅', '恒', '睿', '晨', '曦',
]


def random_name():
    """随机生成中文姓名"""
    if random.random() < 0.3:
        # 30% 单字名
        return random.choice(SURNAMES) + random.choice(GIVEN_NAMES[:20])
    else:
        return random.choice(SURNAMES) + random.choice(GIVEN_NAMES)


def random_phone():
    """生成手机号"""
    prefixes = ['138', '139', '150', '151', '152', '158', '159', '186', '187', '188', '130', '131', '155', '156', '185']
    return random.choice(prefixes) + ''.join(str(random.randint(0, 9)) for _ in range(8))


def random_email(name):
    """根据姓名生成邮箱"""
    domains = ['example.com', 'university.edu.cn', 'stu.university.edu.cn', 'mail.sims.cn']
    pinyin = ''.join(str(ord(c))[-2:] for c in name if c)
    return f'{pinyin}{random.randint(10, 999)}@{random.choice(domains)}'


def random_score():
    """正态分布随机成绩 (均值72, 标准差15, 裁剪到0-100)"""
    return max(0, min(100, round(random.gauss(72, 15), 1)))


def score_to_grade_point(score):
    """成绩 → 绩点映射 (按 grade_scale 等级)"""
    if score >= 90:
        return 4.0
    elif score >= 80:
        return 3.0
    elif score >= 70:
        return 2.0
    elif score >= 60:
        return 1.0
    else:
        return 0.0


class MockDataService:
    """模拟数据生成服务"""

    def __init__(self):
        self.db = SessionLocal()

    def close(self):
        self.db.close()

    # ---- 表生成依赖顺序（拓扑排序） ----
    TABLE_ORDER = [
        'departments', 'majors', 'classes', 'students', 'teachers',
        'courses', 'semesters', 'teaching', 'enrollments',
        'rewards_punishments', 'payments', 'dorm_rooms', 'dorm_assignments',
        'curriculum', 'enroll_logs', 'users', 'user_permissions',
    ]

    VALID_TABLES = set(TABLE_ORDER)

    GENERATE_COUNTS = {
        'departments': 2,
        'majors': 12,
        'classes': 40,
        'students': 200,
        'teachers': 60,
        'courses': 36,
        'semesters': 5,
        'teaching': 100,
        'enrollments': 600,
        'rewards_punishments': 80,
        'payments': 400,
        'dorm_rooms': 60,
        'dorm_assignments': 160,
        'curriculum': 100,
        'enroll_logs': 150,
        'users': 260,
        'user_permissions': 380,
    }

    # ================================================================
    #  公开入口
    # ================================================================

    def generate(self, tables: list) -> dict:
        """主入口：按依赖顺序为指定表生成数据，返回各表生成条数统计"""
        # 过滤有效表名并按依赖顺序排列
        ordered = [t for t in self.TABLE_ORDER if t in tables]
        result = {}

        from entity.department import Department
        from entity.major import Major
        from entity.class_ import Class
        from entity.student import Student
        from entity.teacher import Teacher
        from entity.course import Course
        from entity.semester import Semester
        from entity.teaching import Teaching
        from entity.enrollment import Enrollment
        from entity.reward_punishment import RewardPunishment
        from entity.payment import Payment
        from entity.dorm_room import DormRoom
        from entity.dorm_assignment import DormAssignment
        from entity.curriculum import Curriculum
        from entity.enroll_log import EnrollLog
        from entity.user import User
        from entity.user_permission import UserPermission

        for table_name in ordered:
            count = self.GENERATE_COUNTS.get(table_name, 0)
            if table_name == 'departments':
                result[table_name] = self._gen_departments()
            elif table_name == 'majors':
                result[table_name] = self._gen_majors(count)
            elif table_name == 'classes':
                result[table_name] = self._gen_classes(count)
            elif table_name == 'students':
                result[table_name] = self._gen_students(count)
            elif table_name == 'teachers':
                result[table_name] = self._gen_teachers(count)
            elif table_name == 'courses':
                result[table_name] = self._gen_courses(count)
            elif table_name == 'semesters':
                result[table_name] = self._gen_semesters(count)
            elif table_name == 'teaching':
                result[table_name] = self._gen_teaching(count)
            elif table_name == 'enrollments':
                result[table_name] = self._gen_enrollments(count)
            elif table_name == 'rewards_punishments':
                result[table_name] = self._gen_rewards_punishments(count)
            elif table_name == 'payments':
                result[table_name] = self._gen_payments(count)
            elif table_name == 'dorm_rooms':
                result[table_name] = self._gen_dorm_rooms(count)
            elif table_name == 'dorm_assignments':
                result[table_name] = self._gen_dorm_assignments(count)
            elif table_name == 'curriculum':
                result[table_name] = self._gen_curriculum(count)
            elif table_name == 'enroll_logs':
                result[table_name] = self._gen_enroll_logs(count)
            elif table_name == 'users':
                result[table_name] = self._gen_users(count)
            elif table_name == 'user_permissions':
                result[table_name] = self._gen_user_permissions(count)

        return result

    # ================================================================
    #  各表生成方法
    # ================================================================

    def _gen_departments(self):
        """补充 2 个院系"""
        from entity.department import Department
        names = [
            ('法学院', '周院长', '010-12345607'),
            ('医学院', '孙院长', '010-12345608'),
        ]
        count = 0
        for name, dean, phone in names:
            if not self.db.query(Department).filter(Department.dept_name == name).first():
                self.db.add(Department(dept_name=name, dean=dean, phone=phone))
                count += 1
        self.db.commit()
        return count

    def _gen_majors(self, count):
        """生成专业（每院系约 3 个）"""
        from entity.department import Department
        from entity.major import Major
        dept_ids = [d[0] for d in self.db.query(Department.dept_id).all()]

        major_pool = {
            '法学院': ['法学', '知识产权法', '国际法'],
            '医学院': ['临床医学', '护理学', '药学', '预防医学'],
            '计算机学院': ['人工智能', '大数据技术', '物联网工程', '信息安全'],
            '自动化学院': ['机器人工程', '智能制造'],
            '外国语学院': ['法语', '德语', '翻译'],
            '数学学院': ['统计学', '金融数学'],
            '物理学院': ['光电信息科学', '核物理'],
            '经济管理学院': ['金融学', '市场营销', '物流管理', '电子商务'],
        }
        for dept in self.db.query(Department).all():
            pool = major_pool.get(dept.dept_name, [])
            if not pool:
                continue
            for m_name in pool:
                if self.db.query(Major).filter(Major.major_name == m_name).first():
                    continue
                self.db.add(Major(
                    major_name=m_name,
                    dept_id=dept.dept_id,
                    duration=random.choice([4, 5]),
                ))
        self.db.commit()
        # 返回新增的专业总数（粗略）
        existing = self.db.query(Major).count()
        return count  # 约等于 count

    def _gen_classes(self, count):
        """生成班级（每专业 2 班 × 多入学年份）"""
        from entity.major import Major
        from entity.class_ import Class
        majors = self.db.query(Major).all()
        years = [2022, 2023, 2024, 2025]
        advisors = ['张老师', '李老师', '王老师', '赵老师', '陈老师', '刘老师',
                     '周老师', '吴老师', '郑老师', '孙老师', '钱老师', '冯老师']

        existing_names = {c[0] for c in self.db.query(Class.class_name).all()}
        added = 0

        for major in majors:
            for year in years:
                for i in range(1, 3):  # 每年级 2 班
                    short = major.major_name[:2] if len(major.major_name) >= 2 else major.major_name
                    year_suffix = str(year)[2:]
                    class_name = f'{short}{year_suffix}{i:02d}'
                    if class_name in existing_names:
                        continue
                    self.db.add(Class(
                        class_name=class_name,
                        major_id=major.major_id,
                        enrollment_year=year,
                        advisor=random.choice(advisors),
                    ))
                    existing_names.add(class_name)
                    added += 1
        self.db.commit()
        return added

    def _gen_students(self, count):
        """生成学生"""
        from entity.department import Department
        from entity.class_ import Class
        from entity.student import Student
        dept_ids = [d[0] for d in self.db.query(Department.dept_id).all()]
        classes = self.db.query(Class).all()
        if not classes:
            return 0
        # 取已有的最大 student_id 序号
        from sqlalchemy import func
        max_id = self.db.query(func.max(Student.student_id)).scalar()
        base_num = 1
        if max_id:
            try:
                base_num = int(max_id) + 1
            except ValueError:
                base_num = 1

        existing_id_cards = {s[0] for s in self.db.query(Student.id_card_no).filter(Student.id_card_no.isnot(None)).all()}

        statuses = ['在校'] * 75 + ['休学'] * 10 + ['毕业'] * 10 + ['退学'] * 5

        batch = []
        for i in range(count):
            sid = str(base_num + i).zfill(10)
            gender = random.choice(['M', 'F'])
            name = random_name()
            birth = date(random.randint(1998, 2006), random.randint(1, 12), random.randint(1, 28))
            # 生成唯一身份证号
            id_card = self._gen_id_card(birth, gender, existing_id_cards)
            existing_id_cards.add(id_card)
            chosen_class = random.choice(classes)
            dept_id = chosen_class.major.department.dept_id if chosen_class.major and chosen_class.major.department else random.choice(dept_ids)

            batch.append(Student(
                student_id=sid,
                name=name,
                gender=gender,
                birth_date=birth,
                id_card_no=id_card,
                enrollment_year=chosen_class.enrollment_year,
                dept_id=dept_id,
                class_id=chosen_class.class_id,
                phone=random_phone(),
                email=random_email(name),
                address=f'{random.choice(["北京市", "上海市", "广州市", "深圳市", "杭州市", "成都市", "武汉市", "南京市", "西安市", "重庆市"])}{random.choice(["朝阳区", "海淀区", "浦东新区", "天河区", "西湖区", "武侯区"])}某某路{random.randint(1, 999)}号',
                status=random.choice(statuses),
            ))
            if len(batch) >= 100:
                self.db.bulk_save_objects(batch)
                self.db.commit()
                batch = []
        if batch:
            self.db.bulk_save_objects(batch)
            self.db.commit()
        return count

    def _gen_id_card(self, birth, gender, existing):
        """生成不重复的模拟身份证号 (6位地区 + 8位生日 + 4位后缀)"""
        for _ in range(100):
            area = random.choice(['110101', '310101', '440103', '320105', '330106', '510107'])
            birth_str = birth.strftime('%Y%m%d')
            suffix = str(random.randint(0, 9)) + str(random.randint(0, 9))
            # 倒数第2位奇数为男，偶数为女
            last = str(random.randint(0, 4) * 2 + (1 if gender == 'M' else 0))
            suffix = suffix + last + str(random.randint(0, 9))
            id_card = f'{area}{birth_str}{suffix}'
            if id_card not in existing:
                return id_card
        # fallback
        return f'{random.randint(100000, 999999)}{birth.strftime("%Y%m%d")}{random.randint(1000, 9999)}'

    def _gen_teachers(self, count):
        """生成教师"""
        from entity.department import Department
        from entity.teacher import Teacher
        dept_ids = [d[0] for d in self.db.query(Department.dept_id).all()]
        titles = ['教授'] * 10 + ['副教授'] * 20 + ['讲师'] * 40 + ['助教'] * 20 + ['研究员'] * 5 + ['高级工程师'] * 5
        genders = ['M', 'F']

        # 取最大工号
        from sqlalchemy import func
        max_id = self.db.query(func.max(Teacher.teacher_id)).scalar()
        base = 1
        if max_id:
            try:
                base = int(max_id[1:]) + 1
            except (ValueError, IndexError):
                base = 1

        batch = []
        for i in range(count):
            tid = f'T{base + i:03d}'
            name = random_name()
            batch.append(Teacher(
                teacher_id=tid,
                name=name,
                gender=random.choice(genders),
                title=random.choice(titles),
                dept_id=random.choice(dept_ids),
                phone=random_phone(),
                email=random_email(name),
            ))
            if len(batch) >= 100:
                self.db.bulk_save_objects(batch)
                self.db.commit()
                batch = []
        if batch:
            self.db.bulk_save_objects(batch)
            self.db.commit()
        return count

    def _gen_courses(self, count):
        """生成课程"""
        from entity.department import Department
        from entity.course import Course
        dept_ids = [d[0] for d in self.db.query(Department.dept_id).all()]

        course_data = [
            ('CS303', '计算机网络', 3.5, 56, '必修'),
            ('CS304', '软件工程', 3.0, 48, '必修'),
            ('CS305', '编译原理', 4.0, 64, '必修'),
            ('CS306', '计算机图形学', 3.0, 48, '选修'),
            ('CS307', '人工智能导论', 3.5, 56, '选修'),
            ('CS308', '机器学习', 4.0, 64, '选修'),
            ('CS309', '大数据技术', 3.0, 48, '选修'),
            ('CS310', '云计算概论', 2.5, 40, '选修'),
            ('AUTO102', '传感器技术', 3.0, 48, '必修'),
            ('AUTO103', '微机原理', 4.0, 64, '必修'),
            ('AUTO104', '过程控制', 3.5, 56, '选修'),
            ('EE102', '模拟电子技术', 4.0, 64, '必修'),
            ('EE103', '电力系统分析', 3.5, 56, '必修'),
            ('MATH103', '概率论与数理统计', 3.0, 48, '必修'),
            ('MATH104', '离散数学', 3.5, 56, '必修'),
            ('MATH105', '数值分析', 3.0, 48, '选修'),
            ('ENG102', '英语听说', 2.0, 32, '必修'),
            ('ENG103', '英语写作', 2.0, 32, '必修'),
            ('LAW101', '法学概论', 3.0, 48, '必修'),
            ('LAW102', '宪法学', 4.0, 64, '必修'),
            ('LAW103', '刑法学', 4.5, 72, '必修'),
            ('LAW104', '民法学', 4.5, 72, '必修'),
            ('MED101', '人体解剖学', 5.0, 80, '必修'),
            ('MED102', '病理学', 4.0, 64, '必修'),
            ('MED103', '药理学', 3.5, 56, '必修'),
            ('MGMT101', '管理学原理', 3.0, 48, '必修'),
            ('MGMT102', '市场营销学', 3.0, 48, '必修'),
            ('MGMT103', '人力资源管理', 2.5, 40, '选修'),
            ('PE102', '篮球', 1.0, 32, '公共'),
            ('PE103', '足球', 1.0, 32, '公共'),
            ('PE104', '游泳', 1.0, 32, '公共'),
            ('ART101', '音乐欣赏', 1.5, 24, '公共'),
            ('ART102', '美术鉴赏', 1.5, 24, '公共'),
            ('HIST101', '中国近现代史', 2.0, 32, '公共'),
            ('PHIL101', '马克思主义原理', 3.0, 48, '公共'),
            ('PHIL102', '思想道德修养', 2.0, 32, '公共'),
        ]

        existing = {c[0] for c in self.db.query(Course.course_id).all()}
        added = 0
        for cid, cname, credits, hours, ctype in course_data:
            if cid in existing:
                continue
            # 合理分配 dept_id（根据 course_id 前缀）
            if cid.startswith('CS'):
                did = next((d for d in dept_ids if d == 1), random.choice(dept_ids))
            elif cid.startswith('AUTO') or cid.startswith('EE'):
                did = next((d for d in dept_ids if d == 2), random.choice(dept_ids))
            elif cid.startswith('MATH'):
                did = next((d for d in dept_ids if d == 4), random.choice(dept_ids))
            elif cid.startswith('ENG'):
                did = next((d for d in dept_ids if d == 3), random.choice(dept_ids))
            elif cid.startswith('LAW'):
                did = next((d for d in dept_ids if d >= 7), random.choice(dept_ids))
            elif cid.startswith('MED'):
                did = next((d for d in dept_ids if d >= 8), random.choice(dept_ids))
            elif cid.startswith('MGMT'):
                did = next((d for d in dept_ids if d == 6), random.choice(dept_ids))
            else:
                did = random.choice(dept_ids) if dept_ids else None

            self.db.add(Course(
                course_id=cid,
                course_name=cname,
                credits=credits,
                hours=hours,
                type=ctype,
                dept_id=did,
            ))
            existing.add(cid)
            added += 1
        self.db.commit()
        return added

    def _gen_semesters(self, count):
        """补充学期"""
        from entity.semester import Semester
        seasons = [
            ('2022-2023', '秋季', date(2022, 9, 1), date(2023, 1, 15)),
            ('2022-2023', '春季', date(2023, 2, 20), date(2023, 7, 5)),
            ('2023-2024', '秋季', date(2023, 9, 1), date(2024, 1, 15)),
            ('2023-2024', '春季', date(2024, 2, 20), date(2024, 7, 5)),
            ('2025-2026', '春季', date(2026, 2, 20), date(2026, 7, 5)),
        ]
        added = 0
        for ay, sn, sd, ed in seasons:
            exists = self.db.query(Semester).filter(
                Semester.academic_year == ay,
                Semester.semester_name == sn,
            ).first()
            if not exists:
                self.db.add(Semester(
                    academic_year=ay,
                    semester_name=sn,
                    start_date=sd,
                    end_date=ed,
                    is_current=False,
                ))
                added += 1
        self.db.commit()
        return added

    def _gen_teaching(self, count):
        """生成授课安排"""
        from entity.course import Course
        from entity.teacher import Teacher
        from entity.semester import Semester
        from entity.teaching import Teaching

        courses = self.db.query(Course).all()
        teachers = self.db.query(Teacher).all()
        semesters = self.db.query(Semester).all()

        if not courses or not teachers or not semesters:
            return 0

        classrooms = ['A101', 'A102', 'A103', 'A201', 'A202', 'A203', 'B101', 'B102', 'B201',
                      'B202', 'C101', 'C102', 'C201', 'C301', 'D101', 'D201', '实验室301', '实验室302']
        days = ['周一', '周二', '周三', '周四', '周五']
        periods = ['1-2节', '3-4节', '5-6节', '7-8节', '9-10节']

        # 检查已有授课避免重复
        existing = set()
        for t in self.db.query(Teaching).all():
            existing.add((t.course_id, t.teacher_id, t.semester_id))

        added = 0
        attempts = 0
        while added < count and attempts < count * 5:
            attempts += 1
            course = random.choice(courses)
            teacher = random.choice(teachers)
            semester = random.choice(semesters)
            key = (course.course_id, teacher.teacher_id, semester.semester_id)
            if key in existing:
                continue
            existing.add(key)
            self.db.add(Teaching(
                course_id=course.course_id,
                teacher_id=teacher.teacher_id,
                semester_id=semester.semester_id,
                classroom=random.choice(classrooms),
                schedule=f'{random.choice(days)}{random.choice(periods)}',
                capacity=random.choice([30, 40, 50, 60, 80]),
            ))
            added += 1
            if added % 50 == 0:
                self.db.commit()
        self.db.commit()
        return added

    def _gen_enrollments(self, count):
        """生成选课/成绩记录"""
        from entity.student import Student
        from entity.teaching import Teaching
        from entity.enrollment import Enrollment

        students = self.db.query(Student).all()
        teachings = self.db.query(Teaching).all()

        if not students or not teachings:
            return 0

        # 检查已有选课
        existing = set()
        for e in self.db.query(Enrollment).all():
            existing.add((e.student_id, e.teaching_id))

        statuses = ['正常'] * 82 + ['退课'] * 5 + ['缺考'] * 4 + ['违纪'] * 1

        added = 0
        # 给每个学生分配 3 门课（尽量）
        per_student = max(1, count // len(students))
        batch = []
        for stu in students:
            stu_teachings = random.sample(teachings, min(per_student, len(teachings)))
            for teach in stu_teachings:
                key = (stu.student_id, teach.teaching_id)
                if key in existing:
                    continue
                existing.add(key)
                score = random_score()
                batch.append(Enrollment(
                    student_id=stu.student_id,
                    teaching_id=teach.teaching_id,
                    score=score,
                    grade_point=score_to_grade_point(score),
                    status=random.choice(statuses),
                ))
                added += 1
                if len(batch) >= 100:
                    self.db.bulk_save_objects(batch)
                    self.db.commit()
                    batch = []
        if batch:
            self.db.bulk_save_objects(batch)
            self.db.commit()
        return added

    def _gen_rewards_punishments(self, count):
        """生成奖惩记录"""
        from entity.student import Student
        from entity.reward_punishment import RewardPunishment

        students = self.db.query(Student).all()
        if not students:
            return 0

        rewards = [
            ('三好学生', '校级', '成绩优异，表现突出'),
            ('优秀学生干部', '校级', '学生工作表现突出'),
            ('学习标兵', '院级', '学习成绩优异'),
            ('一等奖学金', '校级', '综合排名前5%'),
            ('二等奖学金', '校级', '综合排名前15%'),
            ('三等奖学金', '院级', '综合排名前30%'),
            ('优秀团员', '校级', '共青团工作表现突出'),
            ('创新创业奖', '校级', '科技创新成绩突出'),
            ('社会实践先进个人', '院级', '社会实践表现优异'),
            ('文体活动积极分子', '院级', '文体活动积极参与'),
        ]
        punishments = [
            ('通报批评', '院级', '违反校规校纪'),
            ('警告', '校级', '考试作弊'),
            ('严重警告', '校级', '旷课累计超过规定'),
            ('记过', '校级', '违反宿舍管理规定'),
            ('留校察看', '校级', '多次违纪'),
        ]

        all_rp = []
        for _ in range(count):
            stu = random.choice(students)
            is_reward = random.random() < 0.7  # 70% 奖励，30% 处分
            if is_reward:
                r = random.choice(rewards)
                all_rp.append(RewardPunishment(
                    student_id=stu.student_id,
                    rp_type='奖励',
                    title=r[0],
                    level=r[1],
                    date=date(random.randint(2022, 2025), random.randint(1, 12), random.randint(1, 28)),
                    reason=r[2],
                    issuing_authority='学生处' if '校级' in r[1] else random.choice(['计算机学院', '自动化学院', '外语学院', '数学学院']),
                ))
            else:
                p = random.choice(punishments)
                all_rp.append(RewardPunishment(
                    student_id=stu.student_id,
                    rp_type='处分',
                    title=p[0],
                    level=p[1],
                    date=date(random.randint(2022, 2025), random.randint(1, 12), random.randint(1, 28)),
                    reason=p[2],
                    issuing_authority='学生处' if '校级' in p[1] else random.choice(['计算机学院', '自动化学院', '外语学院', '数学学院']),
                ))
        self.db.bulk_save_objects(all_rp)
        self.db.commit()
        return count

    def _gen_payments(self, count):
        """生成缴费记录"""
        from entity.student import Student
        from entity.payment import Payment

        students = self.db.query(Student).all()
        if not students:
            return 0

        fee_types = ['学费', '住宿费', '教材费', '体检费']
        academic_years = ['2022-2023', '2023-2024', '2024-2025', '2025-2026']
        semesters = ['秋季', '春季']
        methods = ['银行转账', '微信支付', '支付宝', '现金', '刷卡']
        statuses = ['未缴'] * 25 + ['已缴'] * 55 + ['部分缴'] * 15 + ['退款'] * 5

        batch = []
        added = 0
        per_student = max(1, count // len(students))
        existing_keys = {(p.student_id, p.fee_type, p.academic_year, p.semester) for p in self.db.query(Payment).all()}

        for _ in range(count * 3):  # 多轮尝试
            if added >= count:
                break
            stu = random.choice(students)
            ft = random.choice(fee_types)
            ay = random.choice(academic_years)
            sem = random.choice(semesters)
            key = (stu.student_id, ft, ay, sem)
            if key in existing_keys:
                continue
            existing_keys.add(key)

            amount_due = {'学费': 5000.00, '住宿费': 1200.00, '教材费': 500.00, '体检费': 80.00}.get(ft, 500.00)
            status = random.choice(statuses)
            amount_paid = amount_due if status == '已缴' else (
                round(amount_due * random.uniform(0.3, 0.7), 2) if status == '部分缴' else 0.0
            )
            payment_date = date(random.randint(2022, 2025), random.randint(1, 12), random.randint(1, 28)) if status == '已缴' else None

            batch.append(Payment(
                student_id=stu.student_id,
                fee_type=ft,
                academic_year=ay,
                semester=sem,
                amount_due=amount_due,
                amount_paid=amount_paid,
                payment_date=payment_date,
                status=status,
                payment_method=random.choice(methods) if status == '已缴' else None,
            ))
            added += 1
            if len(batch) >= 100:
                self.db.bulk_save_objects(batch)
                self.db.commit()
                batch = []
        if batch:
            self.db.bulk_save_objects(batch)
            self.db.commit()
        return added

    def _gen_dorm_rooms(self, count):
        """生成宿舍房间"""
        from entity.dorm_room import DormRoom

        buildings = ['1号楼', '2号楼', '3号楼', '4号楼', '5号楼', '6号楼']
        capacities = [2, 4, 4, 4, 4, 4, 4, 6, 6, 8]
        gender_limits = ['M'] * 4 + ['F'] * 4 + ['不限'] * 2

        existing = {(r.building, r.room_number) for r in self.db.query(DormRoom).all()}
        added = 0
        batch = []
        for bld in buildings:
            for room_num in range(101, 121):  # 每栋 20 间
                rn = str(room_num)
                if (bld, rn) in existing:
                    continue
                batch.append(DormRoom(
                    building=bld,
                    room_number=rn,
                    capacity=random.choice(capacities),
                    occupied=0,
                    gender_limit=random.choice(gender_limits),
                    phone=f'010-{random.randint(10000000, 99999999)}',
                ))
                added += 1
                if added >= count:
                    break
                if len(batch) >= 100:
                    self.db.bulk_save_objects(batch)
                    self.db.commit()
                    batch = []
            if added >= count:
                break
        if batch:
            self.db.bulk_save_objects(batch)
            self.db.commit()
        return added

    def _gen_dorm_assignments(self, count):
        """生成住宿分配"""
        from entity.student import Student
        from entity.dorm_room import DormRoom
        from entity.dorm_assignment import DormAssignment

        students = self.db.query(Student).all()
        rooms = self.db.query(DormRoom).all()
        if not students or not rooms:
            return 0

        existing = {(a.student_id,) for a in self.db.query(DormAssignment.student_id).filter(DormAssignment.status == '在住').all()}
        bed_numbers = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

        added = 0
        batch = []
        for stu in students:
            if (stu.student_id,) in existing:
                continue
            if added >= count:
                break
            room = random.choice(rooms)
            bed = random.choice(bed_numbers[:room.capacity])
            check_in = date(random.randint(2022, 2025), 9, random.randint(1, 10))
            batch.append(DormAssignment(
                student_id=stu.student_id,
                room_id=room.room_id,
                bed_number=bed,
                check_in_date=check_in,
                status='在住',
            ))
            existing.add((stu.student_id,))
            added += 1
            if len(batch) >= 100:
                self.db.bulk_save_objects(batch)
                self.db.commit()
                batch = []
        if batch:
            self.db.bulk_save_objects(batch)
            self.db.commit()
        return added

    def _gen_curriculum(self, count):
        """生成培养计划"""
        from entity.major import Major
        from entity.course import Course
        from entity.curriculum import Curriculum

        majors = self.db.query(Major).all()
        courses = self.db.query(Course).all()
        if not majors or not courses:
            return 0

        existing = {(c.major_id, c.enrollment_year, c.course_id) for c in self.db.query(Curriculum).all()}
        years = [2022, 2023, 2024, 2025]
        course_types = ['必修', '选修', '公共']
        terms = [f'第{t}学期' for t in range(1, 9)]

        added = 0
        batch = []
        for major in majors:
            chosen_courses = random.sample(courses, min(5, len(courses)))
            for course in chosen_courses:
                year = random.choice(years)
                key = (major.major_id, year, course.course_id)
                if key in existing:
                    continue
                existing.add(key)
                is_core = random.random() < 0.4
                batch.append(Curriculum(
                    major_id=major.major_id,
                    enrollment_year=year,
                    course_id=course.course_id,
                    course_type=random.choice(course_types),
                    recommended_term=random.choice(terms),
                    min_grade=60.0,
                    is_core=is_core,
                ))
                added += 1
                if added >= count:
                    break
                if len(batch) >= 100:
                    self.db.bulk_save_objects(batch)
                    self.db.commit()
                    batch = []
            if added >= count:
                break
        if batch:
            self.db.bulk_save_objects(batch)
            self.db.commit()
        return added

    def _gen_enroll_logs(self, count):
        """生成选课日志"""
        from entity.student import Student
        from entity.teaching import Teaching
        from entity.enroll_log import EnrollLog

        students = self.db.query(Student).all()
        teachings = self.db.query(Teaching).all()
        if not students or not teachings:
            return 0

        ops = ['选课', '退课', '成绩修改']
        ips = [f'192.168.{random.randint(1, 255)}.{random.randint(1, 255)}' for _ in range(10)]

        batch = []
        for _ in range(count):
            stu = random.choice(students)
            teach = random.choice(teachings)
            op = random.choice(ops)
            batch.append(EnrollLog(
                student_id=stu.student_id,
                teaching_id=teach.teaching_id,
                operation_type=op,
                old_value='-' if op in ('选课', '退课') else str(random.randint(0, 100)),
                new_value='正常' if op == '选课' else ('退课' if op == '退课' else str(random.randint(0, 100))),
                operator='系统管理员' if random.random() < 0.5 else '自动填充',
                operator_ip=random.choice(ips),
                reason='模拟数据生成' if random.random() < 0.3 else None,
            ))
            if len(batch) >= 100:
                self.db.bulk_save_objects(batch)
                self.db.commit()
                batch = []
        if batch:
            self.db.bulk_save_objects(batch)
            self.db.commit()
        return count

    def _gen_users(self, count):
        """生成用户账号（为每个学生和教师创建账号）"""
        from entity.student import Student
        from entity.teacher import Teacher
        from entity.user import User

        existing_usernames = {u[0] for u in self.db.query(User.username).all()}
        added = 0
        batch = []

        # 为学生创建账号（使用随机密码，首次登录需重置）
        for stu in self.db.query(Student).all():
            username = f'stu_{stu.student_id}'
            if username in existing_usernames:
                continue
            existing_usernames.add(username)
            import secrets
            random_password = secrets.token_urlsafe(16)
            batch.append(User(
                uuid=str(uuid.uuid4()),
                username=username,
                password_hash=encrypt_password(random_password),
                role='student',
                ref_id=stu.student_id,
                real_name=stu.name,
                email=stu.email,
                phone=stu.phone,
            ))
            added += 1
            if len(batch) >= 100:
                self.db.bulk_save_objects(batch)
                self.db.commit()
                batch = []

        # 为教师创建账号（使用随机密码，首次登录需重置）
        for t in self.db.query(Teacher).all():
            username = f'tch_{t.teacher_id}'
            if username in existing_usernames:
                continue
            existing_usernames.add(username)
            import secrets
            random_password = secrets.token_urlsafe(16)
            batch.append(User(
                uuid=str(uuid.uuid4()),
                username=username,
                password_hash=encrypt_password(random_password),
                role='teacher',
                ref_id=t.teacher_id,
                real_name=t.name,
                email=t.email,
                phone=t.phone,
            ))
            added += 1
            if len(batch) >= 100:
                self.db.bulk_save_objects(batch)
                self.db.commit()
                batch = []

        if batch:
            self.db.bulk_save_objects(batch)
            self.db.commit()
        return added

    def _gen_user_permissions(self, count):
        """生成用户权限"""
        from entity.user import User
        from entity.user_permission import UserPermission

        users = self.db.query(User).filter(User.role != 'admin').all()
        if not users:
            return 0

        tables = ['students', 'teachers', 'courses', 'classes', 'departments', 'majors',
                  'semesters', 'teaching', 'enrollments', 'rewards_punishments', 'payments',
                  'dorm_rooms', 'dorm_assignments', 'curriculum', 'enroll_logs', 'statistics']
        perm_codes = ['040', '060', '070', '044', '064', '074']

        existing = {(p.user_uuid, p.table_name) for p in self.db.query(UserPermission).all()}
        added = 0
        batch = []

        for user in users:
            num_tables = random.randint(1, 3)
            chosen_tables = random.sample(tables, min(num_tables, len(tables)))
            for tbl in chosen_tables:
                key = (user.uuid, tbl)
                if key in existing:
                    continue
                existing.add(key)
                batch.append(UserPermission(
                    user_uuid=user.uuid,
                    table_name=tbl,
                    permission_code=random.choice(perm_codes),
                ))
                added += 1
                if added >= count:
                    break
                if len(batch) >= 100:
                    self.db.bulk_save_objects(batch)
                    self.db.commit()
                    batch = []
            if added >= count:
                break
        if batch:
            self.db.bulk_save_objects(batch)
            self.db.commit()
        return added
