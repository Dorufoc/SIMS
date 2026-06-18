"""批量导入实体配置 —— 定义各实体的 CSV 列映射、解析、导入导出规则"""
from datetime import date
from repository.student_repo import StudentRepo
from repository.teacher_repo import TeacherRepo
from repository.course_repo import CourseRepo
from repository.department_repo import DepartmentRepo
from repository.major_repo import MajorRepo
from repository.class_repo import ClassRepo
from repository.dorm_room_repo import DormRoomRepo
from repository.dorm_assignment_repo import DormAssignmentRepo
from repository.reward_punishment_repo import RewardPunishmentRepo
from repository.enrollment_repo import EnrollmentRepo
from repository.user_repo import UserRepo
from entity.student import Student
from entity.enrollment import Enrollment
from entity.user import User
from entity.teacher import Teacher
from entity.course import Course
from entity.department import Department
from entity.major import Major
from entity.class_ import Class
from entity.dorm_room import DormRoom
from entity.dorm_assignment import DormAssignment
from entity.reward_punishment import RewardPunishment


def _parse_int(i: int, raw_val, csv_col: str):
    """类型转换：整数"""
    if not raw_val:
        return None, []
    try:
        return int(raw_val), []
    except (ValueError, TypeError):
        return None, [f'第{i}行：{csv_col} 格式不正确（应为整数）']


def _parse_year(i: int, raw_val, csv_col: str):
    """类型转换：年份"""
    if not raw_val:
        return date.today().year, []
    try:
        val = int(raw_val)
        if val < 2000 or val > 2099:
            return None, [f'第{i}行：{csv_col} 年份不在合理范围']
        return val, []
    except (ValueError, TypeError):
        return None, [f'第{i}行：{csv_col} 格式不正确']


# ==================== 学生 ====================

def _student_parse_row(i: int, item: dict, row: dict):
    """学生行解析：类型转换"""
    errors = []
    enrollment_year, errs = _parse_year(i, item.get('enrollment_year'), '入学年份')
    errors.extend(errs)
    if errs:
        return item, errors
    item['enrollment_year'] = enrollment_year

    class_id, errs = _parse_int(i, item.get('class_id'), '班级编号')
    errors.extend(errs)
    item['class_id'] = class_id

    if item.get('birth_date'):
        item['birth_date'] = item['birth_date'] if item['birth_date'] else None

    item.setdefault('status', '在校')
    return item, errors


def _student_find_existing(repo, item: dict):
    return repo.find_by_student_id(item['student_id'])


def _student_export_row(s):
    return [
        s.student_id, s.name,
        '男' if s.gender == 'M' else ('女' if s.gender == 'F' else ''),
        str(s.birth_date) if s.birth_date else '',
        s.id_card_no or '', s.enrollment_year, s.status or '在校',
        s.phone or '', s.email or '', s.address or ''
    ]


STUDENT_IMPORT_CONFIG = {
    'repo': StudentRepo,
    'model': Student,
    'template_headers': [
        '学号', '姓名', '性别(M/F)', '出生日期(YYYY-MM-DD)', '身份证号',
        '入学年份', '班级编号', '手机号', '邮箱', '地址'
    ],
    'template_example': [
        '2024001', '张三', 'M', '2000-01-01', '110101200001011234',
        '2024', '1', '13800138000', 'zhangsan@example.com', '北京市'
    ],
    'export_headers': [
        '学号', '姓名', '性别', '出生日期', '身份证号',
        '入学年份', '状态', '手机号', '邮箱', '地址'
    ],
    'header_check_field': '学号',
    'field_map': {
        '学号': 'student_id', '姓名': 'name', '性别(M/F)': 'gender',
        '出生日期(YYYY-MM-DD)': 'birth_date', '身份证号': 'id_card_no',
        '入学年份': 'enrollment_year', '班级编号': 'class_id',
        '手机号': 'phone', '邮箱': 'email', '地址': 'address'
    },
    'required_fields': ['student_id', 'name'],
    'field_labels': {'student_id': '学号', 'name': '姓名'},
    'on_parse_row': _student_parse_row,
    'find_existing': _student_find_existing,
    'export_row': _student_export_row,
    # 前端预览列
    'preview_columns': ['学号', '姓名', '性别', '出生日期', '入学年份', '班级编号'],
}

# ==================== 教师 ====================

def _teacher_find_existing(repo, item: dict):
    return repo.find_by(teacher_id=item['teacher_id'])


def _teacher_export_row(t):
    return [
        t.teacher_id, t.name,
        '男' if t.gender == 'M' else ('女' if t.gender == 'F' else ''),
        t.title or '', t.dept_id or '', t.phone or '', t.email or ''
    ]


TEACHER_IMPORT_CONFIG = {
    'repo': TeacherRepo,
    'model': Teacher,
    'template_headers': ['教师编号', '姓名', '性别(M/F)', '职称', '所属院系编号', '联系电话', '邮箱'],
    'template_example': ['T001', '李教授', 'M', '教授', '1', '13800000001', 'lijaoshou@example.com'],
    'export_headers': ['教师编号', '姓名', '性别', '职称', '所属院系编号', '联系电话', '邮箱'],
    'header_check_field': '教师编号',
    'field_map': {
        '教师编号': 'teacher_id', '姓名': 'name', '性别(M/F)': 'gender',
        '职称': 'title', '所属院系编号': 'dept_id',
        '联系电话': 'phone', '邮箱': 'email'
    },
    'required_fields': ['teacher_id', 'name'],
    'field_labels': {'teacher_id': '教师编号', 'name': '姓名'},
    'find_existing': _teacher_find_existing,
    'export_row': _teacher_export_row,
    'preview_columns': ['教师编号', '姓名', '性别', '职称', '联系电话'],
}

# ==================== 课程 ====================

def _course_parse_row(i: int, item: dict, row: dict):
    errors = []
    credits, errs = _parse_int(i, item.get('credits'), '学分')
    errors.extend(errs)
    if credits is not None:
        item['credits'] = credits
    hours, errs = _parse_int(i, item.get('hours'), '学时')
    errors.extend(errs)
    if hours is not None:
        item['hours'] = hours
    dept_id, errs = _parse_int(i, item.get('dept_id'), '开课院系编号')
    errors.extend(errs)
    if dept_id is not None:
        item['dept_id'] = dept_id
    return item, errors


def _course_find_existing(repo, item: dict):
    return repo.find_by(course_id=item['course_id'])


def _course_export_row(c):
    return [c.course_id, c.course_name, c.dept_id or '', c.credits, c.hours or '', c.type or '']


COURSE_IMPORT_CONFIG = {
    'repo': CourseRepo,
    'model': Course,
    'template_headers': ['课程代码', '课程名称', '学分', '学时', '类型(必修/选修/公共)', '开课院系编号'],
    'template_example': ['CS101', '计算机基础', '3', '48', '必修', '1'],
    'export_headers': ['课程代码', '课程名称', '开课院系', '学分', '学时', '类型'],
    'header_check_field': '课程代码',
    'field_map': {
        '课程代码': 'course_id', '课程名称': 'course_name',
        '学分': 'credits', '学时': 'hours',
        '类型(必修/选修/公共)': 'type', '开课院系编号': 'dept_id'
    },
    'required_fields': ['course_id', 'course_name'],
    'field_labels': {'course_id': '课程代码', 'course_name': '课程名称'},
    'on_parse_row': _course_parse_row,
    'find_existing': _course_find_existing,
    'export_row': _course_export_row,
    'preview_columns': ['课程代码', '课程名称', '学分', '学时', '类型'],
}

# ==================== 院系 ====================

def _dept_find_existing(repo, item: dict):
    return repo.find_by(dept_name=item['dept_name'])


def _dept_export_row(d):
    return [d.dept_id, d.dept_name, d.dean or '', d.phone or '']


DEPARTMENT_IMPORT_CONFIG = {
    'repo': DepartmentRepo,
    'model': Department,
    'template_headers': ['院系名称', '院长/主任', '联系电话'],
    'template_example': ['信息工程学院', '王院长', '010-12345678'],
    'export_headers': ['院系编号', '院系名称', '院长/主任', '联系电话'],
    'header_check_field': '院系名称',
    'field_map': {
        '院系名称': 'dept_name', '院长/主任': 'dean', '联系电话': 'phone'
    },
    'required_fields': ['dept_name'],
    'field_labels': {'dept_name': '院系名称'},
    'find_existing': _dept_find_existing,
    'export_row': _dept_export_row,
    'preview_columns': ['院系名称', '院长/主任', '联系电话'],
}

# ==================== 专业 ====================

def _major_parse_row(i: int, item: dict, row: dict):
    errors = []
    dept_id, errs = _parse_int(i, item.get('dept_id'), '所属院系编号')
    errors.extend(errs)
    if dept_id is not None:
        item['dept_id'] = dept_id
    if item.get('duration'):
        dur, errs = _parse_int(i, item.get('duration'), '学制')
        errors.extend(errs)
        if dur is not None:
            item['duration'] = dur
        else:
            item['duration'] = 4
    else:
        item['duration'] = 4
    return item, errors


def _major_find_existing(repo, item: dict):
    return repo.find_by(major_name=item['major_name'], dept_id=item.get('dept_id'))


def _major_export_row(m):
    return [m.major_id, m.major_name, m.dept_id or '', m.duration or 4]


MAJOR_IMPORT_CONFIG = {
    'repo': MajorRepo,
    'model': Major,
    'template_headers': ['专业名称', '所属院系编号', '学制(年)'],
    'template_example': ['计算机科学与技术', '1', '4'],
    'export_headers': ['专业编号', '专业名称', '所属院系编号', '学制(年)'],
    'header_check_field': '专业名称',
    'field_map': {
        '专业名称': 'major_name', '所属院系编号': 'dept_id', '学制(年)': 'duration'
    },
    'required_fields': ['major_name', 'dept_id'],
    'field_labels': {'major_name': '专业名称', 'dept_id': '所属院系编号'},
    'on_parse_row': _major_parse_row,
    'find_existing': _major_find_existing,
    'export_row': _major_export_row,
    'preview_columns': ['专业名称', '所属院系编号', '学制(年)'],
}

# ==================== 班级 ====================

def _class_parse_row(i: int, item: dict, row: dict):
    errors = []
    major_id, errs = _parse_int(i, item.get('major_id'), '所属专业编号')
    errors.extend(errs)
    if major_id is not None:
        item['major_id'] = major_id
    enrollment_year, errs = _parse_year(i, item.get('enrollment_year'), '入学年份')
    errors.extend(errs)
    if enrollment_year is not None:
        item['enrollment_year'] = enrollment_year
    return item, errors


def _class_find_existing(repo, item: dict):
    return repo.find_by(class_name=item['class_name'], major_id=item.get('major_id'))


def _class_export_row(c):
    return [c.class_id, c.class_name, c.major_id or '', c.enrollment_year or '', c.advisor or '']


CLASS_IMPORT_CONFIG = {
    'repo': ClassRepo,
    'model': Class,
    'template_headers': ['班级名称', '所属专业编号', '入学年份', '辅导员'],
    'template_example': ['计算机2024-1班', '1', '2024', '张老师'],
    'export_headers': ['班级编号', '班级名称', '所属专业编号', '入学年份', '辅导员'],
    'header_check_field': '班级名称',
    'field_map': {
        '班级名称': 'class_name', '所属专业编号': 'major_id',
        '入学年份': 'enrollment_year', '辅导员': 'advisor'
    },
    'required_fields': ['class_name', 'major_id'],
    'field_labels': {'class_name': '班级名称', 'major_id': '所属专业编号'},
    'on_parse_row': _class_parse_row,
    'find_existing': _class_find_existing,
    'export_row': _class_export_row,
    'preview_columns': ['班级名称', '所属专业编号', '入学年份', '辅导员'],
}

# ==================== 宿舍 ====================

def _dorm_room_parse_row(i: int, item: dict, row: dict):
    errors = []
    capacity, errs = _parse_int(i, item.get('capacity'), '容量')
    errors.extend(errs)
    if capacity is not None:
        item['capacity'] = capacity
    if item.get('occupied'):
        occ, _ = _parse_int(i, item.get('occupied'), '已住')
        if occ is not None:
            item['occupied'] = occ
        else:
            item['occupied'] = 0
    else:
        item['occupied'] = 0
    item.setdefault('gender_limit', '不限')
    return item, errors


def _dorm_room_find_existing(repo, item: dict):
    return repo.find_by(building=item['building'], room_number=item['room_number'])


def _dorm_room_export_row(d):
    occ_rate = f"{d.occupied}/{d.capacity}" if d.capacity else ''
    return [d.building, d.room_number, d.capacity, d.occupied, occ_rate,
            d.gender_limit or '不限', d.phone or '']


DORM_ROOM_IMPORT_CONFIG = {
    'repo': DormRoomRepo,
    'model': DormRoom,
    'template_headers': ['楼栋', '房间号', '容量', '已住人数', '性别限制(M/F/不限)', '联系电话'],
    'template_example': ['1号楼', '101', '4', '0', '不限', ''],
    'export_headers': ['楼栋', '房间号', '容量', '已住', '入住率', '性别限制', '联系电话'],
    'header_check_field': '楼栋',
    'field_map': {
        '楼栋': 'building', '房间号': 'room_number', '容量': 'capacity',
        '已住人数': 'occupied', '性别限制(M/F/不限)': 'gender_limit', '联系电话': 'phone'
    },
    'required_fields': ['building', 'room_number', 'capacity'],
    'field_labels': {'building': '楼栋', 'room_number': '房间号', 'capacity': '容量'},
    'on_parse_row': _dorm_room_parse_row,
    'find_existing': _dorm_room_find_existing,
    'export_row': _dorm_room_export_row,
    'preview_columns': ['楼栋', '房间号', '容量', '性别限制'],
}

# ==================== 住宿分配 ====================

def _dorm_assign_parse_row(i: int, item: dict, row: dict):
    errors = []
    room_id, errs = _parse_int(i, item.get('room_id'), '房间编号')
    errors.extend(errs)
    if room_id is not None:
        item['room_id'] = room_id
    if not item.get('check_in_date'):
        item['check_in_date'] = date.today()
    else:
        item['check_in_date'] = item['check_in_date']
    item.setdefault('status', '在住')
    return item, errors


def _dorm_assign_find_existing(repo, item: dict):
    return repo.find_by(student_id=item['student_id'], status='在住')


def _dorm_assign_export_row(a):
    return [a.assign_id, a.student_id, a.room_id or '', a.bed_number or '',
            str(a.check_in_date) if a.check_in_date else '', a.status or '在住']


DORM_ASSIGN_IMPORT_CONFIG = {
    'repo': DormAssignmentRepo,
    'model': DormAssignment,
    'template_headers': ['学号', '房间编号', '床位号', '入住日期(YYYY-MM-DD)', '状态'],
    'template_example': ['2024001', '1', 'A1', '2024-09-01', '在住'],
    'export_headers': ['分配编号', '学号', '房间编号', '床位号', '入住日期', '状态'],
    'header_check_field': '学号',
    'field_map': {
        '学号': 'student_id', '房间编号': 'room_id', '床位号': 'bed_number',
        '入住日期(YYYY-MM-DD)': 'check_in_date', '状态': 'status'
    },
    'required_fields': ['student_id', 'room_id'],
    'field_labels': {'student_id': '学号', 'room_id': '房间编号'},
    'on_parse_row': _dorm_assign_parse_row,
    'find_existing': _dorm_assign_find_existing,
    'export_row': _dorm_assign_export_row,
    'preview_columns': ['学号', '房间编号', '床位号', '入住日期', '状态'],
}

# ==================== 奖惩 ====================

def _reward_find_existing(repo, item: dict):
    return None  # 奖惩允许重复，不做去重更新


def _reward_export_row(r):
    return [r.rp_id, r.student_id, r.rp_type, r.title, r.level or '',
            str(r.date) if r.date else '', r.issuing_authority or '']


REWARD_IMPORT_CONFIG = {
    'repo': RewardPunishmentRepo,
    'model': RewardPunishment,
    'template_headers': ['学号', '类型(奖励/处分)', '标题', '级别', '日期(YYYY-MM-DD)', '原因', '发文单位', '备注'],
    'template_example': ['2024001', '奖励', '优秀学生', '校级', '2025-01-15', '学习成绩优异', '学生处', ''],
    'export_headers': ['编号', '学号', '类型', '标题', '级别', '日期', '发文单位'],
    'header_check_field': '学号',
    'field_map': {
        '学号': 'student_id', '类型(奖励/处分)': 'rp_type', '标题': 'title',
        '级别': 'level', '日期(YYYY-MM-DD)': 'date', '原因': 'reason',
        '发文单位': 'issuing_authority', '备注': 'remark'
    },
    'required_fields': ['student_id', 'rp_type', 'title', 'date'],
    'field_labels': {'student_id': '学号', 'rp_type': '类型', 'title': '标题', 'date': '日期'},
    'find_existing': _reward_find_existing,
    'export_row': _reward_export_row,
    'preview_columns': ['学号', '类型', '标题', '级别', '日期'],
}


# ==================== 选课记录 ====================

def _enrollment_find_existing(repo, item: dict):
    return repo.find_by(student_id=item['student_id'], teaching_id=item.get('teaching_id'))


def _enrollment_export_row(e):
    return [
        e.enroll_id, e.student_id, e.teaching_id or '',
        float(e.score) if e.score else '', e.status or '正常'
    ]


ENROLLMENT_IMPORT_CONFIG = {
    'repo': EnrollmentRepo,
    'model': Enrollment,
    'template_headers': ['学号', '授课编号', '成绩', '状态(正常/退课/缺考/违纪)'],
    'template_example': ['2024001', '1', '85', '正常'],
    'export_headers': ['选课编号', '学号', '授课编号', '成绩', '状态'],
    'header_check_field': '学号',
    'field_map': {
        '学号': 'student_id', '授课编号': 'teaching_id',
        '成绩': 'score', '状态(正常/退课/缺考/违纪)': 'status'
    },
    'required_fields': ['student_id', 'teaching_id'],
    'field_labels': {'student_id': '学号', 'teaching_id': '授课编号'},
    'find_existing': _enrollment_find_existing,
    'export_row': _enrollment_export_row,
    'preview_columns': ['学号', '授课编号', '成绩', '状态'],
}

# ==================== 用户账号 ====================

def _user_create_entity(item: dict):
    """创建用户时自动生成 uuid 和密码哈希"""
    import uuid
    from utils.password_utils import encrypt_password
    entity = User(
        uuid=str(uuid.uuid4()),
        username=item['username'],
        password_hash=encrypt_password(item.get('password', '123456')),
        role=item.get('role', 'student'),
        ref_id=item.get('ref_id'),
        real_name=item.get('real_name'),
        email=item.get('email'),
        phone=item.get('phone'),
    )
    return entity


def _user_find_existing(repo, item: dict):
    return repo.find_by(username=item['username'])


def _user_export_row(u):
    return [u.user_id, u.username, u.role, u.ref_id or '',
            u.real_name or '', u.email or '', u.phone or '']


USER_IMPORT_CONFIG = {
    'repo': UserRepo,
    'model': User,
    'template_headers': ['用户名', '密码(默认123456)', '角色(admin/teacher/student)', '关联ID', '真实姓名', '邮箱', '电话'],
    'template_example': ['zhangsan', '123456', 'student', '2024001', '张三', 'zhangsan@example.com', '13800000001'],
    'export_headers': ['用户ID', '用户名', '角色', '关联ID', '真实姓名', '邮箱', '电话'],
    'header_check_field': '用户名',
    'field_map': {
        '用户名': 'username', '密码(默认123456)': 'password', '角色(admin/teacher/student)': 'role',
        '关联ID': 'ref_id', '真实姓名': 'real_name', '邮箱': 'email', '电话': 'phone'
    },
    'required_fields': ['username', 'role'],
    'field_labels': {'username': '用户名', 'role': '角色'},
    'create_entity': _user_create_entity,
    'find_existing': _user_find_existing,
    'export_row': _user_export_row,
    'preview_columns': ['用户名', '角色', '关联ID', '真实姓名'],
}


# ── 注册所有配置 ──

from service.batch_import_service import BatchImportService

BatchImportService.register('student', **STUDENT_IMPORT_CONFIG)
BatchImportService.register('teacher', **TEACHER_IMPORT_CONFIG)
BatchImportService.register('course', **COURSE_IMPORT_CONFIG)
BatchImportService.register('department', **DEPARTMENT_IMPORT_CONFIG)
BatchImportService.register('major', **MAJOR_IMPORT_CONFIG)
BatchImportService.register('class', **CLASS_IMPORT_CONFIG)
BatchImportService.register('dorm_room', **DORM_ROOM_IMPORT_CONFIG)
BatchImportService.register('dorm_assignment', **DORM_ASSIGN_IMPORT_CONFIG)
BatchImportService.register('reward', **REWARD_IMPORT_CONFIG)
BatchImportService.register('enrollment', **ENROLLMENT_IMPORT_CONFIG)
BatchImportService.register('user', **USER_IMPORT_CONFIG)
