-- ============================================
-- 学生信息管理系统 - PostgreSQL 建表脚本
-- 版本: 2.0 (MVC 重构)
-- ============================================

-- 1. 院系表
CREATE TABLE departments (
    dept_id SERIAL PRIMARY KEY,
    dept_name VARCHAR(100) UNIQUE NOT NULL,
    dean VARCHAR(50),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 专业表
CREATE TABLE majors (
    major_id SERIAL PRIMARY KEY,
    major_name VARCHAR(100) NOT NULL,
    dept_id INTEGER NOT NULL REFERENCES departments(dept_id),
    duration SMALLINT DEFAULT 4,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. 班级表
CREATE TABLE classes (
    class_id SERIAL PRIMARY KEY,
    class_name VARCHAR(50) NOT NULL,
    major_id INTEGER NOT NULL REFERENCES majors(major_id),
    enrollment_year INTEGER NOT NULL,
    advisor VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 学生表
CREATE TABLE students (
    student_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    gender VARCHAR(1) CHECK (gender IN ('M','F')),
    birth_date DATE,
    id_card_no VARCHAR(18) UNIQUE,
    enrollment_year INTEGER NOT NULL,
    dept_id INTEGER REFERENCES departments(dept_id),
    class_id INTEGER REFERENCES classes(class_id),
    phone VARCHAR(20),
    email VARCHAR(100),
    address VARCHAR(200),
    status VARCHAR(10) DEFAULT '在校' CHECK (status IN ('在校','休学','毕业','退学')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 教师表
CREATE TABLE teachers (
    teacher_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    gender VARCHAR(1) CHECK (gender IN ('M','F')),
    title VARCHAR(50),
    dept_id INTEGER REFERENCES departments(dept_id),
    phone VARCHAR(20),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. 课程表
CREATE TABLE courses (
    course_id VARCHAR(20) PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL,
    credits NUMERIC(3,1) NOT NULL,
    hours SMALLINT,
    type VARCHAR(10) NOT NULL CHECK (type IN ('必修','选修','公共')),
    dept_id INTEGER REFERENCES departments(dept_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. 学期表
CREATE TABLE semesters (
    semester_id SERIAL PRIMARY KEY,
    academic_year VARCHAR(9) NOT NULL,
    semester_name VARCHAR(10) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. 授课表
CREATE TABLE teaching (
    teaching_id SERIAL PRIMARY KEY,
    course_id VARCHAR(20) NOT NULL REFERENCES courses(course_id),
    teacher_id VARCHAR(20) NOT NULL REFERENCES teachers(teacher_id),
    semester_id INTEGER NOT NULL REFERENCES semesters(semester_id),
    classroom VARCHAR(50),
    schedule VARCHAR(200),
    capacity SMALLINT DEFAULT 30,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. 选课/成绩表
CREATE TABLE enrollments (
    enroll_id SERIAL PRIMARY KEY,
    student_id VARCHAR(20) NOT NULL REFERENCES students(student_id),
    teaching_id INTEGER NOT NULL REFERENCES teaching(teaching_id),
    score NUMERIC(5,2),
    grade_point NUMERIC(3,2),
    enroll_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(10) DEFAULT '正常' CHECK (status IN ('正常','退课','缺考','违纪')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. 教室表
CREATE TABLE classrooms (
    classroom_id SERIAL PRIMARY KEY,
    classroom_name VARCHAR(50) NOT NULL,
    building VARCHAR(50),
    floor SMALLINT,
    capacity SMALLINT DEFAULT 30,
    type VARCHAR(20) DEFAULT '普通教室',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. 用户表
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(10) NOT NULL CHECK (role IN ('admin','teacher','student')),
    ref_id VARCHAR(20),
    email VARCHAR(100),
    phone VARCHAR(20),
    last_login TIMESTAMP,
    username_changed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. 用户权限表
CREATE TABLE user_permissions (
    perm_id SERIAL PRIMARY KEY,
    user_uuid VARCHAR(36) NOT NULL REFERENCES users(uuid),
    table_name VARCHAR(100) NOT NULL,
    permission_code VARCHAR(10) DEFAULT '000',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_uuid, table_name)
);

-- 13. 奖惩表
CREATE TABLE rewards_punishments (
    rp_id SERIAL PRIMARY KEY,
    student_id VARCHAR(20) NOT NULL REFERENCES students(student_id),
    rp_type VARCHAR(10) NOT NULL CHECK (rp_type IN ('奖励','处分')),
    title VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    reason TEXT,
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 14. 缴费表
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    student_id VARCHAR(20) NOT NULL REFERENCES students(student_id),
    fee_type VARCHAR(50) NOT NULL,
    academic_year VARCHAR(9) NOT NULL,
    semester VARCHAR(10),
    amount_due NUMERIC(10,2) NOT NULL,
    amount_paid NUMERIC(10,2) DEFAULT 0,
    payment_date DATE,
    status VARCHAR(10) DEFAULT '未缴' CHECK (status IN ('未缴','部分缴','已缴','退款')),
    payment_method VARCHAR(50),
    remark TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 15. 宿舍房间表
CREATE TABLE dorm_rooms (
    room_id SERIAL PRIMARY KEY,
    building VARCHAR(50) NOT NULL,
    room_number VARCHAR(20) NOT NULL,
    capacity SMALLINT NOT NULL,
    occupied SMALLINT DEFAULT 0,
    gender_limit VARCHAR(10) DEFAULT '不限' CHECK (gender_limit IN ('M','F','不限')),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 16. 住宿分配表
CREATE TABLE dorm_assignments (
    assign_id SERIAL PRIMARY KEY,
    student_id VARCHAR(20) NOT NULL REFERENCES students(student_id),
    room_id INTEGER NOT NULL REFERENCES dorm_rooms(room_id),
    bed_number VARCHAR(10),
    check_in_date DATE NOT NULL,
    check_out_date DATE,
    status VARCHAR(10) DEFAULT '在住' CHECK (status IN ('在住','已退','调换')),
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 视图
-- ============================================

-- 学生完整信息视图
CREATE VIEW v_student_full AS
SELECT
    s.student_id, s.name, s.gender, s.birth_date, s.enrollment_year,
    s.status, s.phone, s.email, s.id_card_no, s.address,
    c.class_id, c.class_name, c.enrollment_year AS class_year,
    m.major_id, m.major_name,
    d.dept_id, d.dept_name
FROM students s
LEFT JOIN classes c ON s.class_id = c.class_id
LEFT JOIN majors m ON c.major_id = m.major_id
LEFT JOIN departments d ON m.dept_id = d.dept_id;

-- 授课完整信息视图
CREATE VIEW v_teaching_full AS
SELECT
    t.teaching_id, t.classroom, t.schedule, t.capacity,
    c.course_id, c.course_name, c.credits, c.hours, c.type AS course_type,
    tr.teacher_id, tr.name AS teacher_name, tr.title,
    s.semester_id, s.academic_year, s.semester_name, s.is_current
FROM teaching t
JOIN courses c ON t.course_id = c.course_id
JOIN teachers tr ON t.teacher_id = tr.teacher_id
JOIN semesters s ON t.semester_id = s.semester_id;

-- 选课完整信息视图
CREATE VIEW v_enrollment_full AS
SELECT
    e.enroll_id, e.student_id, e.score, e.grade_point, e.enroll_time, e.status,
    t.teaching_id, t.classroom, t.schedule,
    c.course_id, c.course_name, c.credits,
    tr.teacher_id, tr.name AS teacher_name,
    s.semester_id, s.academic_year, s.semester_name
FROM enrollments e
JOIN teaching t ON e.teaching_id = t.teaching_id
JOIN courses c ON t.course_id = c.course_id
JOIN teachers tr ON t.teacher_id = tr.teacher_id
JOIN semesters s ON t.semester_id = s.semester_id;

-- ============================================
-- 触发器（PostgreSQL 语法）
-- ============================================

-- 入住触发器：自动增加宿舍已住人数
CREATE OR REPLACE FUNCTION trg_dorm_checkin()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE dorm_rooms SET occupied = occupied + 1 WHERE room_id = NEW.room_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_dorm_checkin ON dorm_assignments;
CREATE TRIGGER trigger_dorm_checkin
    AFTER INSERT ON dorm_assignments
    FOR EACH ROW
    WHEN (NEW.status = '在住')
    EXECUTE FUNCTION trg_dorm_checkin();

-- 退宿触发器：自动减少宿舍已住人数
CREATE OR REPLACE FUNCTION trg_dorm_checkout()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = '已退' AND OLD.status = '在住' THEN
        UPDATE dorm_rooms SET occupied = GREATEST(occupied - 1, 0) WHERE room_id = NEW.room_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_dorm_checkout ON dorm_assignments;
CREATE TRIGGER trigger_dorm_checkout
    AFTER UPDATE ON dorm_assignments
    FOR EACH ROW
    WHEN (NEW.status = '已退' AND OLD.status = '在住')
    EXECUTE FUNCTION trg_dorm_checkout();

-- ============================================
-- 索引（常用查询字段）
-- ============================================

-- students 表
CREATE INDEX idx_students_name ON students(name);
CREATE INDEX idx_students_class_id ON students(class_id);
CREATE INDEX idx_students_dept_id ON students(dept_id);
CREATE INDEX idx_students_enrollment_year ON students(enrollment_year);
CREATE INDEX idx_students_status ON students(status);
CREATE INDEX idx_students_gender ON students(gender);
CREATE INDEX idx_students_phone ON students(phone);
CREATE INDEX idx_students_birth_date ON students(birth_date);
CREATE INDEX idx_students_email ON students(email);

-- teachers 表
CREATE INDEX idx_teachers_name ON teachers(name);
CREATE INDEX idx_teachers_dept_id ON teachers(dept_id);
CREATE INDEX idx_teachers_title ON teachers(title);
CREATE INDEX idx_teachers_gender ON teachers(gender);
CREATE INDEX idx_teachers_phone ON teachers(phone);

-- courses 表
CREATE INDEX idx_courses_dept_id ON courses(dept_id);
CREATE INDEX idx_courses_type ON courses(type);
CREATE INDEX idx_courses_name ON courses(course_name);

-- semesters 表
CREATE INDEX idx_semesters_current ON semesters(is_current);

-- teaching 表
CREATE INDEX idx_teaching_course_id ON teaching(course_id);
CREATE INDEX idx_teaching_teacher_id ON teaching(teacher_id);
CREATE INDEX idx_teaching_semester_id ON teaching(semester_id);
CREATE INDEX idx_teaching_schedule ON teaching(schedule);
CREATE INDEX idx_teaching_classroom ON teaching(classroom);
CREATE INDEX idx_teaching_capacity ON teaching(capacity);

-- enrollments 表
CREATE INDEX idx_enrollments_student_id ON enrollments(student_id);
CREATE INDEX idx_enrollments_teaching_id ON enrollments(teaching_id);
CREATE INDEX idx_enrollments_status ON enrollments(status);
CREATE INDEX idx_enrollments_score ON enrollments(score);
CREATE INDEX idx_enrollments_grade_point ON enrollments(grade_point);

-- classrooms 表
CREATE INDEX idx_classrooms_building ON classrooms(building);
CREATE INDEX idx_classrooms_type ON classrooms(type);
CREATE INDEX idx_classrooms_name ON classrooms(classroom_name);
CREATE INDEX idx_classrooms_floor ON classrooms(floor);

-- users 表
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_uuid ON users(uuid);
CREATE INDEX idx_users_ref_id ON users(ref_id);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_created_at ON users(created_at);

-- user_permissions 表
CREATE INDEX idx_user_perm_user ON user_permissions(user_uuid);
CREATE INDEX idx_user_perm_table ON user_permissions(table_name);

-- rewards_punishments 表
CREATE INDEX idx_rp_student_id ON rewards_punishments(student_id);
CREATE INDEX idx_rp_type ON rewards_punishments(rp_type);
CREATE INDEX idx_rp_date ON rewards_punishments(date);
CREATE INDEX idx_rp_student_date ON rewards_punishments(student_id, date);

-- payments 表
CREATE INDEX idx_payments_student_id ON payments(student_id);
CREATE INDEX idx_payments_year ON payments(academic_year);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_fee_type ON payments(fee_type);
CREATE INDEX idx_payments_amount_due ON payments(amount_due);
CREATE INDEX idx_payments_amount_paid ON payments(amount_paid);
CREATE INDEX idx_payments_payment_date ON payments(payment_date);
CREATE INDEX idx_payments_student_year ON payments(student_id, academic_year, semester);

-- dorm_rooms 表
CREATE INDEX idx_dorm_rooms_building ON dorm_rooms(building);
CREATE INDEX idx_dorm_rooms_gender ON dorm_rooms(gender_limit);
CREATE INDEX idx_dorm_rooms_capacity ON dorm_rooms(capacity);
CREATE INDEX idx_dorm_rooms_occupied ON dorm_rooms(occupied);

-- dorm_assignments 表
CREATE INDEX idx_dorm_assign_student ON dorm_assignments(student_id);
CREATE INDEX idx_dorm_assign_room ON dorm_assignments(room_id);
CREATE INDEX idx_dorm_assign_status ON dorm_assignments(status);
CREATE INDEX idx_dorm_assign_student_status ON dorm_assignments(student_id, status);
CREATE INDEX idx_dorm_assign_room_status ON dorm_assignments(room_id, status);
CREATE INDEX idx_dorm_assign_checkin_date ON dorm_assignments(check_in_date);

-- 插入默认管理员账号（密码: admin123）
INSERT INTO users (uuid, username, password_hash, role, username_changed) VALUES
    ('00000000-0000-0000-0000-000000000001', 'admin', '$2b$12$LJ3m4ys3LkBCVxJGqOjPkuYVOYpGOKbHgEMoJxYzRqcMdFNP2oWby', 'admin', TRUE)
ON CONFLICT (username) DO NOTHING;
