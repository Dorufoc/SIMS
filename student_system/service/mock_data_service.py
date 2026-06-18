"""模拟数据生成服务 —— 为各表生成结构化中文模拟数据"""
import random
import uuid
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

# ============================================================
# 结构化院系/专业/班级定义
# ============================================================
# 3 个学院，每个学院 2 个专业，每个专业 2 个班
DEPT_MAJOR_CLASS = [
    {
        'dept_name': '计算机学院',
        'dean': '张院长',
        'phone': '010-12345601',
        'majors': [
            {
                'major_name': '计算机科学与技术',
                'major_short': '计科',
                'duration': 4,
                'class_years': [2023, 2024],  # 2 个班，不同入学年份
                'teacher_count': 2,
                'courses': [
                    ('CS101', '数据结构', 4.0, 64, '必修'),
                    ('CS102', '操作系统', 4.0, 64, '必修'),
                ],
                # (name, gender, title)
                'teachers': [
                    ('王刚', 'M', '教授'),
                    ('李红', 'F', '副教授'),
                ],
                # 学生性别比例 (M男, F女) - 工科男多
                'student_gender_ratio': (70, 30),
            },
            {
                'major_name': '软件工程',
                'major_short': '软件',
                'duration': 4,
                'class_years': [2024, 2025],
                'teacher_count': 2,
                'courses': [
                    ('SE101', '软件工程导论', 3.0, 48, '必修'),
                    ('SE102', '数据库原理', 3.5, 56, '必修'),
                ],
                'teachers': [
                    ('张强', 'M', '副教授'),
                    ('刘洋', 'M', '讲师'),
                ],
                'student_gender_ratio': (75, 25),
            },
        ]
    },
    {
        'dept_name': '外国语学院',
        'dean': '李院长',
        'phone': '010-12345602',
        'majors': [
            {
                'major_name': '英语',
                'major_short': '英语',
                'duration': 4,
                'class_years': [2023, 2024],
                'teacher_count': 2,
                'courses': [
                    ('EN101', '综合英语', 4.0, 64, '必修'),
                    ('EN102', '英语写作', 2.0, 32, '必修'),
                ],
                'teachers': [
                    ('陈芳', 'F', '教授'),
                    ('赵敏', 'F', '讲师'),
                ],
                'student_gender_ratio': (20, 80),  # 文科女多
            },
            {
                'major_name': '日语',
                'major_short': '日语',
                'duration': 4,
                'class_years': [2024, 2025],
                'teacher_count': 2,
                'courses': [
                    ('JP101', '基础日语', 4.0, 64, '必修'),
                    ('JP102', '日本文化', 2.0, 32, '选修'),
                ],
                'teachers': [
                    ('孙丽', 'F', '副教授'),
                    ('周婷', 'F', '助教'),
                ],
                'student_gender_ratio': (15, 85),
            },
        ]
    },
    {
        'dept_name': '经济管理学院',
        'dean': '王院长',
        'phone': '010-12345603',
        'majors': [
            {
                'major_name': '会计学',
                'major_short': '会计',
                'duration': 4,
                'class_years': [2023, 2024],
                'teacher_count': 2,
                'courses': [
                    ('AC101', '基础会计', 3.5, 56, '必修'),
                    ('AC102', '财务管理', 3.5, 56, '必修'),
                ],
                'teachers': [
                    ('吴明', 'M', '副教授'),
                    ('郑华', 'F', '讲师'),
                ],
                'student_gender_ratio': (35, 65),  # 经管女稍多
            },
            {
                'major_name': '工商管理',
                'major_short': '工商',
                'duration': 4,
                'class_years': [2024, 2025],
                'teacher_count': 2,
                'courses': [
                    ('BM101', '管理学原理', 3.0, 48, '必修'),
                    ('BM102', '市场营销', 3.0, 48, '必修'),
                ],
                'teachers': [
                    ('钱峰', 'M', '教授'),
                    ('冯磊', 'M', '讲师'),
                ],
                'student_gender_ratio': (45, 55),
            },
        ]
    },
]

# ============================================================
# 辅导员池
# ============================================================
ADVISORS = [
    '张明', '李华', '王芳', '赵强', '陈静', '刘洋',
    '周敏', '吴磊', '郑洁', '孙鹏', '钱丽', '冯刚',
]

# ============================================================
# 跨年制学期
# ============================================================
SEMESTER_DATA = [
    ('2022-2023', '秋季', date(2022, 9, 1), date(2023, 1, 15)),
    ('2022-2023', '春季', date(2023, 2, 20), date(2023, 7, 5)),
    ('2023-2024', '秋季', date(2023, 9, 1), date(2024, 1, 15)),
    ('2023-2024', '春季', date(2024, 2, 20), date(2024, 7, 5)),
    ('2024-2025', '秋季', date(2024, 9, 1), date(2025, 1, 15)),
    ('2024-2025', '春季', date(2025, 2, 20), date(2025, 7, 5)),
    ('2025-2026', '秋季', date(2025, 9, 1), date(2026, 1, 15)),
    ('2025-2026', '春季', date(2026, 2, 20), date(2026, 7, 5)),
]

# ============================================================
# 宿舍楼定义
# ============================================================
DORM_BUILDINGS = [
    {'building': '梅苑', 'gender': 'F', 'rooms_per_floor': 10, 'floors': 4},
    {'building': '兰苑', 'gender': 'F', 'rooms_per_floor': 10, 'floors': 4},
    {'building': '竹苑', 'gender': 'M', 'rooms_per_floor': 10, 'floors': 4},
    {'building': '菊苑', 'gender': 'M', 'rooms_per_floor': 10, 'floors': 4},
]

STUDENTS_PER_CLASS = 30


# ============================================================
# 工具函数
# ============================================================

def _weighted_gender(male_pct):
    """按百分比返回性别 'M' 或 'F'"""
    return 'M' if random.randint(1, 100) <= male_pct else 'F'


def random_name():
    """随机生成中文姓名"""
    if random.random() < 0.3:
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


# ============================================================
# 服务类
# ============================================================

class MockDataService:
    """模拟数据生成服务"""

    def __init__(self):
        self.db = SessionLocal()

    def close(self):
        self.db.close()

    TABLE_ORDER = [
        'departments', 'majors', 'classes', 'students', 'teachers',
        'courses', 'semesters', 'teaching', 'enrollments',
        'rewards_punishments', 'payments', 'dorm_rooms', 'dorm_assignments',
        'users', 'user_permissions',
    ]

    VALID_TABLES = set(TABLE_ORDER)

    GENERATE_COUNTS = {
        'departments': 3,
        'majors': 6,
        'classes': 12,
        'students': 360,  # 12 个班 × 30 人
        'teachers': 12,
        'courses': 12,
        'semesters': 8,
        'teaching': 48,
        'enrollments': 720,
        'rewards_punishments': 80,
        'payments': 720,
        'dorm_rooms': 40,
        'dorm_assignments': 300,
        'users': 372,
        'user_permissions': 500,
    }

    # ================================================================
    #  公开入口
    # ================================================================

    def generate(self, tables: list) -> dict:
        """主入口：按依赖顺序为指定表生成数据，返回各表生成条数统计"""
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
        from entity.user import User
        from entity.user_permission import UserPermission

        for table_name in ordered:
            count = self.GENERATE_COUNTS.get(table_name, 0)
            if table_name == 'departments':
                result[table_name] = self._gen_departments()
            elif table_name == 'majors':
                result[table_name] = self._gen_majors()
            elif table_name == 'classes':
                result[table_name] = self._gen_classes()
            elif table_name == 'students':
                result[table_name] = self._gen_students()
            elif table_name == 'teachers':
                result[table_name] = self._gen_teachers()
            elif table_name == 'courses':
                result[table_name] = self._gen_courses()
            elif table_name == 'semesters':
                result[table_name] = self._gen_semesters()
            elif table_name == 'teaching':
                result[table_name] = self._gen_teaching()
            elif table_name == 'enrollments':
                result[table_name] = self._gen_enrollments(count)
            elif table_name == 'rewards_punishments':
                result[table_name] = self._gen_rewards_punishments(count)
            elif table_name == 'payments':
                result[table_name] = self._gen_payments(count)
            elif table_name == 'dorm_rooms':
                result[table_name] = self._gen_dorm_rooms()
            elif table_name == 'dorm_assignments':
                result[table_name] = self._gen_dorm_assignments(count)
            elif table_name == 'users':
                result[table_name] = self._gen_users()
            elif table_name == 'user_permissions':
                result[table_name] = self._gen_user_permissions(count)

        return result

    # ================================================================
    #  院系
    # ================================================================

    def _gen_departments(self):
        """生成 3 个学院"""
        from entity.department import Department
        count = 0
        for info in DEPT_MAJOR_CLASS:
            name = info['dept_name']
            if not self.db.query(Department).filter(Department.dept_name == name).first():
                self.db.add(Department(
                    dept_name=name,
                    dean=info['dean'],
                    phone=info['phone'],
                ))
                count += 1
        self.db.commit()
        return count

    # ================================================================
    #  专业
    # ================================================================

    def _gen_majors(self):
        """每个学院 2 个专业，共 6 个"""
        from entity.department import Department
        from entity.major import Major
        count = 0
        for info in DEPT_MAJOR_CLASS:
            dept = self.db.query(Department).filter(Department.dept_name == info['dept_name']).first()
            if not dept:
                continue
            for m in info['majors']:
                if self.db.query(Major).filter(Major.major_name == m['major_name']).first():
                    continue
                self.db.add(Major(
                    major_name=m['major_name'],
                    dept_id=dept.dept_id,
                    duration=m['duration'],
                    degree_type='学士',
                ))
                count += 1
        self.db.commit()
        return count

    # ================================================================
    #  班级
    # ================================================================

    def _gen_classes(self):
        """每个专业 2 个班（各配辅导员），共 12 个班"""
        from entity.major import Major
        from entity.class_ import Class
        existing_names = {c[0] for c in self.db.query(Class.class_name).all()}
        count = 0
        advisor_idx = 0
        for info in DEPT_MAJOR_CLASS:
            for m in info['majors']:
                major = self.db.query(Major).filter(Major.major_name == m['major_name']).first()
                if not major:
                    continue
                for i, year in enumerate(m['class_years']):
                    short = m['major_short']
                    year_suffix = str(year)[2:]
                    class_name = f'{short}{year_suffix}0{i + 1}'
                    if class_name in existing_names:
                        continue
                    advisor = ADVISORS[advisor_idx % len(ADVISORS)]
                    advisor_idx += 1
                    self.db.add(Class(
                        class_name=class_name,
                        major_id=major.major_id,
                        enrollment_year=year,
                        advisor=advisor,
                    ))
                    existing_names.add(class_name)
                    count += 1
        self.db.commit()
        return count

    # ================================================================
    #  学生（每班 30 人）
    # ================================================================

    def _gen_students(self):
        """每个班 30 个学生，按专业合理分配性别"""
        from entity.class_ import Class
        from entity.student import Student
        classes = self.db.query(Class).order_by(Class.class_id).all()
        if not classes:
            return 0

        from sqlalchemy import func
        max_id = self.db.query(func.max(Student.student_id)).scalar()
        base_num = 1
        if max_id:
            try:
                base_num = int(max_id) + 1
            except ValueError:
                base_num = 1

        existing_id_cards = {s[0] for s in self.db.query(Student.id_card_no).filter(Student.id_card_no.isnot(None)).all()}
        statuses = ['在校'] * 85 + ['休学'] * 8 + ['退学'] * 4 + ['毕业'] * 3
        count = 0
        batch = []

        for clazz in classes:
            # 找到该班级所属专业的性别比例
            major_name = clazz.major.major_name if clazz.major else ''
            gender_ratio = (50, 50)  # 默认
            for info in DEPT_MAJOR_CLASS:
                for m in info['majors']:
                    if m['major_name'] == major_name:
                        gender_ratio = m['student_gender_ratio']
                        break

            for i in range(STUDENTS_PER_CLASS):
                sid = str(base_num + count).zfill(10)
                gender = _weighted_gender(gender_ratio[0])
                name = random_name()
                birth = date(clazz.enrollment_year - 18, random.randint(1, 12), random.randint(1, 28))
                id_card = self._gen_id_card(birth, gender, existing_id_cards)
                existing_id_cards.add(id_card)

                batch.append(Student(
                    student_id=sid,
                    name=name,
                    gender=gender,
                    birth_date=birth,
                    id_card_no=id_card,
                    enrollment_year=clazz.enrollment_year,
                    dept_id=clazz.major.dept_id if clazz.major else None,
                    class_id=clazz.class_id,
                    phone=random_phone(),
                    email=random_email(name),
                    address=f'{random.choice(["北京市", "上海市", "广州市", "深圳市", "杭州市", "成都市", "武汉市", "南京市", "西安市", "重庆市"])}{random.choice(["朝阳区", "海淀区", "浦东新区", "天河区", "西湖区", "武侯区"])}某某路{random.randint(1, 999)}号',
                    status=random.choice(statuses),
                ))
                count += 1
                if len(batch) >= 100:
                    self.db.bulk_save_objects(batch)
                    self.db.commit()
                    batch = []
        if batch:
            self.db.bulk_save_objects(batch)
            self.db.commit()
        return count

    def _gen_id_card(self, birth, gender, existing):
        """生成不重复的模拟身份证号"""
        for _ in range(100):
            area = random.choice(['110101', '310101', '440103', '320105', '330106', '510107'])
            birth_str = birth.strftime('%Y%m%d')
            suffix = str(random.randint(0, 9)) + str(random.randint(0, 9))
            last = str(random.randint(0, 4) * 2 + (1 if gender == 'M' else 0))
            suffix = suffix + last + str(random.randint(0, 9))
            id_card = f'{area}{birth_str}{suffix}'
            if id_card not in existing:
                return id_card
        return f'{random.randint(100000, 999999)}{birth.strftime("%Y%m%d")}{random.randint(1000, 9999)}'

    # ================================================================
    #  教师（每个专业 2 名）
    # ================================================================

    def _gen_teachers(self):
        """按预设为每个专业分配 2 名教师"""
        from entity.department import Department
        from entity.major import Major
        from entity.teacher import Teacher
        from sqlalchemy import func

        max_id = self.db.query(func.max(Teacher.teacher_id)).scalar()
        base = 1
        if max_id:
            try:
                base = int(max_id[1:]) + 1
            except (ValueError, IndexError):
                base = 1

        count = 0
        batch = []
        for info in DEPT_MAJOR_CLASS:
            dept = self.db.query(Department).filter(Department.dept_name == info['dept_name']).first()
            if not dept:
                continue
            for m in info['majors']:
                for t_info in m['teachers']:
                    t_name, t_gender, t_title = t_info
                    # 检查是否已存在同名教师（避免重复生成）
                    existing = self.db.query(Teacher).filter(
                        Teacher.name == t_name,
                        Teacher.dept_id == dept.dept_id,
                    ).first()
                    if existing:
                        continue
                    tid = f'T{base + count:03d}'
                    batch.append(Teacher(
                        teacher_id=tid,
                        name=t_name,
                        gender=t_gender,
                        title=t_title,
                        dept_id=dept.dept_id,
                        phone=random_phone(),
                        email=f'{t_name}@university.edu.cn',
                    ))
                    count += 1
        if batch:
            self.db.bulk_save_objects(batch)
            self.db.commit()
        return count

    # ================================================================
    #  课程（每个专业 2 门）
    # ================================================================

    def _gen_courses(self):
        """为每个专业生成 2 门课程"""
        from entity.department import Department
        from entity.major import Major
        from entity.course import Course
        count = 0
        for info in DEPT_MAJOR_CLASS:
            dept = self.db.query(Department).filter(Department.dept_name == info['dept_name']).first()
            if not dept:
                continue
            for m in info['majors']:
                for cid, cname, credits, hours, ctype in m['courses']:
                    if self.db.query(Course).filter(Course.course_id == cid).first():
                        continue
                    self.db.add(Course(
                        course_id=cid,
                        course_name=cname,
                        credits=credits,
                        hours=hours,
                        type=ctype,
                        dept_id=dept.dept_id,
                    ))
                    count += 1
        self.db.commit()
        return count

    # ================================================================
    #  学期（跨年制，每学年 2 个学期）
    # ================================================================

    def _gen_semesters(self):
        """生成 4 学年 × 2 学期 = 8 个学期（跨年制）"""
        from entity.semester import Semester
        count = 0
        for ay, sn, sd, ed in SEMESTER_DATA:
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
                    is_current=(ay == '2025-2026' and sn == '春季'),
                ))
                count += 1
        self.db.commit()
        return count

    # ================================================================
    #  授课安排
    # ================================================================

    def _gen_teaching(self):
        """为每门课程在各个学年合理分配授课教师"""
        from entity.course import Course
        from entity.teacher import Teacher
        from entity.semester import Semester
        from entity.teaching import Teaching

        courses = self.db.query(Course).all()
        teachers = self.db.query(Teacher).all()
        semesters = self.db.query(Semester).all()

        if not courses or not teachers or not semesters:
            return 0

        classrooms = ['A101', 'A102', 'A103', 'A201', 'A202', 'A203',
                      'B101', 'B102', 'B201', 'B202',
                      'C101', 'C102', 'C201', 'C301']
        days = ['周一', '周二', '周三', '周四', '周五']
        periods = ['1-2节', '3-4节', '5-6节', '7-8节']

        existing = set()
        for t in self.db.query(Teaching).all():
            existing.add((t.course_id, t.teacher_id, t.semester_id))

        # 教师姓名 → teacher 对象 映射
        teacher_map = {t.name: t for t in teachers}

        from entity.department import Department
        from entity.major import Major

        # 获取课程 → 所属专业的教师映射
        # 遍历结构化定义，为课程匹配同专业教师
        course_teacher_pairs = []
        for info in DEPT_MAJOR_CLASS:
            dept = self.db.query(Department).filter(Department.dept_name == info['dept_name']).first()
            if not dept:
                continue
            for m in info['majors']:
                # 该专业的教师
                major_teachers = []
                for t_name, _, _ in m['teachers']:
                    t = teacher_map.get(t_name)
                    if t:
                        major_teachers.append(t)
                if not major_teachers:
                    continue
                # 该专业的课程
                for cid, _, _, _, _ in m['courses']:
                    course = self.db.query(Course).filter(Course.course_id == cid).first()
                    if not course:
                        continue
                    course_teacher_pairs.append((course, major_teachers))

        added = 0
        batch = []
        # 每门课程在多个学期中授课
        for course, major_teachers in course_teacher_pairs:
            for t in major_teachers:
                # 每位教师每门课教 2~3 个学期
                num_semesters = random.randint(2, 3)
                chosen_sems = random.sample(semesters, min(num_semesters, len(semesters)))
                for sem in chosen_sems:
                    key = (course.course_id, t.teacher_id, sem.semester_id)
                    if key in existing:
                        continue
                    existing.add(key)
                    batch.append(Teaching(
                        course_id=course.course_id,
                        teacher_id=t.teacher_id,
                        semester_id=sem.semester_id,
                        classroom=random.choice(classrooms),
                        schedule=f'{random.choice(days)}{random.choice(periods)}',
                        capacity=random.choice([30, 40, 50, 60]),
                    ))
                    added += 1
                    if len(batch) >= 50:
                        self.db.bulk_save_objects(batch)
                        self.db.commit()
                        batch = []
        if batch:
            self.db.bulk_save_objects(batch)
            self.db.commit()
        return added

    # ================================================================
    #  选课/成绩
    # ================================================================

    def _gen_enrollments(self, count):
        """生成选课/成绩记录"""
        from entity.student import Student
        from entity.teaching import Teaching
        from entity.enrollment import Enrollment

        students = self.db.query(Student).all()
        teachings = self.db.query(Teaching).all()

        if not students or not teachings:
            return 0

        existing = set()
        for e in self.db.query(Enrollment).all():
            existing.add((e.student_id, e.teaching_id))

        statuses = ['正常'] * 82 + ['退课'] * 5 + ['缺考'] * 4 + ['违纪'] * 1

        added = 0
        batch = []
        per_student = max(1, count // len(students))

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

    # ================================================================
    #  奖惩
    # ================================================================

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
            is_reward = random.random() < 0.7
            if is_reward:
                r = random.choice(rewards)
                all_rp.append(RewardPunishment(
                    student_id=stu.student_id,
                    rp_type='奖励',
                    title=r[0],
                    date=date(random.randint(2022, 2025), random.randint(1, 12), random.randint(1, 28)),
                    reason=f'{r[1]}: {r[2]}',
                ))
            else:
                p = random.choice(punishments)
                all_rp.append(RewardPunishment(
                    student_id=stu.student_id,
                    rp_type='处分',
                    title=p[0],
                    date=date(random.randint(2022, 2025), random.randint(1, 12), random.randint(1, 28)),
                    reason=f'{p[1]}: {p[2]}',
                ))
        self.db.bulk_save_objects(all_rp)
        self.db.commit()
        return count

    # ================================================================
    #  缴费
    # ================================================================

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

        for _ in range(count * 3):
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

    # ================================================================
    #  宿舍房间
    # ================================================================

    def _gen_dorm_rooms(self):
        """生成宿舍房间（梅兰竹菊四苑）"""
        from entity.dorm_room import DormRoom
        existing = {(r.building, r.room_number) for r in self.db.query(DormRoom).all()}
        count = 0
        batch = []
        for bld_info in DORM_BUILDINGS:
            bld = bld_info['building']
            gender = bld_info['gender']
            for floor in range(1, bld_info['floors'] + 1):
                for room_num in range(1, bld_info['rooms_per_floor'] + 1):
                    rn = f'{floor:02d}{room_num:02d}'
                    if (bld, rn) in existing:
                        continue
                    capacity = 4
                    batch.append(DormRoom(
                        building=bld,
                        room_number=rn,
                        capacity=capacity,
                        occupied=0,
                        gender_limit=gender,
                        phone=f'010-{random.randint(10000000, 99999999)}',
                    ))
                    count += 1
                    if len(batch) >= 100:
                        self.db.bulk_save_objects(batch)
                        self.db.commit()
                        batch = []
        if batch:
            self.db.bulk_save_objects(batch)
            self.db.commit()
        return count

    # ================================================================
    #  住宿分配
    # ================================================================

    def _gen_dorm_assignments(self, count):
        """按性别分配宿舍"""
        from entity.student import Student
        from entity.dorm_room import DormRoom
        from entity.dorm_assignment import DormAssignment

        students = self.db.query(Student).all()
        rooms = self.db.query(DormRoom).all()
        if not students or not rooms:
            return 0

        existing_students = {a.student_id for a in self.db.query(DormAssignment.student_id).filter(DormAssignment.status == '在住').all()}
        occupied = {(a.room_id, a.bed_number) for a in self.db.query(
            DormAssignment.room_id, DormAssignment.bed_number
        ).filter(DormAssignment.status == '在住').all()}
        bed_numbers = ['A', 'B', 'C', 'D']

        # 按性别分宿舍
        male_rooms = [r for r in rooms if r.gender_limit == 'M']
        female_rooms = [r for r in rooms if r.gender_limit == 'F']

        added = 0
        batch = []

        def assign_dorm(stu, room_pool):
            nonlocal added
            if stu.student_id in existing_students:
                return
            if added >= count:
                return
            available = []
            for room in room_pool:
                for bed in bed_numbers[:room.capacity]:
                    if (room.room_id, bed) not in occupied:
                        available.append((room, bed))
            if not available:
                return
            room, bed = random.choice(available)
            occupied.add((room.room_id, bed))
            check_in = date(stu.enrollment_year, 9, random.randint(1, 5))
            batch.append(DormAssignment(
                student_id=stu.student_id,
                room_id=room.room_id,
                bed_number=bed,
                check_in_date=check_in,
                status='在住',
            ))
            existing_students.add(stu.student_id)
            added += 1

        for stu in students:
            if stu.gender == 'M':
                assign_dorm(stu, male_rooms)
            else:
                assign_dorm(stu, female_rooms)
            if added >= count:
                break
            if len(batch) >= 100:
                self.db.bulk_save_objects(batch)
                self.db.commit()
                batch = []
        if batch:
            self.db.bulk_save_objects(batch)
            self.db.commit()
        return added

    # ================================================================
    #  用户账号
    # ================================================================

    def _gen_users(self):
        """为所有学生和教师创建账号"""
        from entity.student import Student
        from entity.teacher import Teacher
        from entity.user import User

        existing_usernames = {u[0] for u in self.db.query(User.username).all()}
        count = 0
        batch = []
        import secrets

        for stu in self.db.query(Student).all():
            username = f'stu_{stu.student_id}'
            if username in existing_usernames:
                continue
            existing_usernames.add(username)
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
            count += 1
            if len(batch) >= 100:
                self.db.bulk_save_objects(batch)
                self.db.commit()
                batch = []

        for t in self.db.query(Teacher).all():
            username = f'tch_{t.teacher_id}'
            if username in existing_usernames:
                continue
            existing_usernames.add(username)
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
            count += 1
            if len(batch) >= 100:
                self.db.bulk_save_objects(batch)
                self.db.commit()
                batch = []

        if batch:
            self.db.bulk_save_objects(batch)
            self.db.commit()
        return count

    # ================================================================
    #  用户权限
    # ================================================================

    def _gen_user_permissions(self, count):
        """生成用户权限"""
        from entity.user import User
        from entity.user_permission import UserPermission

        users = self.db.query(User).filter(User.role != 'admin').all()
        if not users:
            return 0

        tables = ['students', 'teachers', 'courses', 'classes', 'departments', 'majors',
                  'semesters', 'teaching', 'enrollments', 'rewards_punishments', 'payments',
                  'dorm_rooms', 'dorm_assignments', 'statistics']
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
