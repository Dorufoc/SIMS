-- ============================================
-- 为已有数据库补充常用查询字段索引
-- 用法:
--   PostgreSQL: psql -U postgres -d student_manage -f postgresql_indexes.sql
-- ============================================

-- ============================================
-- students 表
-- ============================================
CREATE INDEX IF NOT EXISTS idx_students_gender ON students(gender);
CREATE INDEX IF NOT EXISTS idx_students_phone ON students(phone);
CREATE INDEX IF NOT EXISTS idx_students_birth_date ON students(birth_date);
CREATE INDEX IF NOT EXISTS idx_students_email ON students(email);

-- ============================================
-- teachers 表
-- ============================================
CREATE INDEX IF NOT EXISTS idx_teachers_title ON teachers(title);
CREATE INDEX IF NOT EXISTS idx_teachers_gender ON teachers(gender);
CREATE INDEX IF NOT EXISTS idx_teachers_phone ON teachers(phone);

-- ============================================
-- courses 表
-- ============================================
CREATE INDEX IF NOT EXISTS idx_courses_type ON courses(type);
CREATE INDEX IF NOT EXISTS idx_courses_name ON courses(course_name);

-- ============================================
-- teaching 表
-- ============================================
CREATE INDEX IF NOT EXISTS idx_teaching_schedule ON teaching(schedule);
CREATE INDEX IF NOT EXISTS idx_teaching_classroom ON teaching(classroom);
CREATE INDEX IF NOT EXISTS idx_teaching_capacity ON teaching(capacity);

-- ============================================
-- enrollments 表
-- ============================================
CREATE INDEX IF NOT EXISTS idx_enrollments_score ON enrollments(score);
CREATE INDEX IF NOT EXISTS idx_enrollments_grade_point ON enrollments(grade_point);

-- ============================================
-- classrooms 表
-- ============================================
CREATE INDEX IF NOT EXISTS idx_classrooms_floor ON classrooms(floor);

-- ============================================
-- users 表
-- ============================================
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- ============================================
-- payments 表
-- ============================================
CREATE INDEX IF NOT EXISTS idx_payments_fee_type ON payments(fee_type);
CREATE INDEX IF NOT EXISTS idx_payments_amount_due ON payments(amount_due);
CREATE INDEX IF NOT EXISTS idx_payments_amount_paid ON payments(amount_paid);
CREATE INDEX IF NOT EXISTS idx_payments_payment_date ON payments(payment_date);

-- ============================================
-- dorm_rooms 表
-- ============================================
CREATE INDEX IF NOT EXISTS idx_dorm_rooms_capacity ON dorm_rooms(capacity);
CREATE INDEX IF NOT EXISTS idx_dorm_rooms_occupied ON dorm_rooms(occupied);

-- ============================================
-- dorm_assignments 表
-- ============================================
CREATE INDEX IF NOT EXISTS idx_dorm_assignments_checkin_date ON dorm_assignments(check_in_date);
