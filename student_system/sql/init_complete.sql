-- ============================================
-- 学生信息管理系统 - 完整数据库初始化脚本
-- 17张业务表：基础11张 + 扩展6张
-- MySQL 5.6+ 兼容
-- ============================================

DROP DATABASE IF EXISTS `student_manage`;

CREATE DATABASE IF NOT EXISTS `student_manage`
  DEFAULT CHARACTER SET utf8;

USE `student_manage`;

-- ============================================
-- 1. 院系表 (departments)
-- ============================================
CREATE TABLE IF NOT EXISTS `departments` (
  `dept_id`     INT         PRIMARY KEY AUTO_INCREMENT COMMENT '院系唯一编号',
  `dept_name`   VARCHAR(100) NOT NULL UNIQUE COMMENT '院系名称',
  `dean`        VARCHAR(50) COMMENT '院长/主任姓名',
  `phone`       VARCHAR(20) COMMENT '联系电话',
  `created_at`  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  INDEX `idx_dept_name` (`dept_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='院系表';

-- ============================================
-- 2. 专业表 (majors)
-- ============================================
CREATE TABLE IF NOT EXISTS `majors` (
  `major_id`    INT         PRIMARY KEY AUTO_INCREMENT COMMENT '专业唯一编号',
  `major_name`  VARCHAR(100) NOT NULL COMMENT '专业名称',
  `dept_id`     INT         NOT NULL COMMENT '所属院系',
  `duration`    TINYINT     DEFAULT 4 COMMENT '学制（年）',
  `created_at`  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`dept_id`) REFERENCES `departments`(`dept_id`) ON DELETE RESTRICT,
  INDEX `idx_major_dept` (`dept_id`),
  INDEX `idx_major_name` (`major_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='专业表';

-- ============================================
-- 3. 班级表 (classes)
-- ============================================
CREATE TABLE IF NOT EXISTS `classes` (
  `class_id`         INT         PRIMARY KEY AUTO_INCREMENT COMMENT '班级编号',
  `class_name`       VARCHAR(50) NOT NULL COMMENT '班级名称（如"计算机2101"）',
  `major_id`         INT         NOT NULL COMMENT '所属专业',
  `enrollment_year`  YEAR        NOT NULL COMMENT '入学年份',
  `advisor`          VARCHAR(50) COMMENT '辅导员姓名',
  `created_at`       TIMESTAMP   DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`major_id`) REFERENCES `majors`(`major_id`) ON DELETE RESTRICT,
  INDEX `idx_class_major` (`major_id`),
  INDEX `idx_class_year` (`enrollment_year`),
  INDEX `idx_class_name` (`class_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='班级表';

-- ============================================
-- 4. 学生表 (students)
-- ============================================
CREATE TABLE IF NOT EXISTS `students` (
  `student_id`      VARCHAR(20)  PRIMARY KEY COMMENT '学号（手工录入，唯一）',
  `name`            VARCHAR(50)  NOT NULL COMMENT '姓名',
  `gender`          ENUM('M','F') COMMENT '性别（M=男，F=女）',
  `birth_date`      DATE         COMMENT '出生日期',
  `id_card_no`      VARCHAR(18)  UNIQUE COMMENT '身份证号',
  `enrollment_year` YEAR         NOT NULL COMMENT '入学年份',
  `dept_id`         INT          COMMENT '所属院系',
  `class_id`        INT          COMMENT '所属班级',
  `phone`           VARCHAR(20)  COMMENT '手机号码',
  `email`           VARCHAR(100) COMMENT '电子邮箱',
  `address`         VARCHAR(200) COMMENT '家庭住址',
  `status`          ENUM('在校','休学','毕业','退学') DEFAULT '在校' COMMENT '学生状态',
  `created_at`      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`dept_id`) REFERENCES `departments`(`dept_id`) ON DELETE SET NULL,
  FOREIGN KEY (`class_id`) REFERENCES `classes`(`class_id`) ON DELETE SET NULL,
  INDEX `idx_student_dept` (`dept_id`),
  INDEX `idx_student_class` (`class_id`),
  INDEX `idx_student_year` (`enrollment_year`),
  INDEX `idx_student_status` (`status`),
  INDEX `idx_student_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='学生表';

-- ============================================
-- 5. 教师表 (teachers)
-- ============================================
CREATE TABLE IF NOT EXISTS `teachers` (
  `teacher_id`  VARCHAR(20)  PRIMARY KEY COMMENT '教师工号',
  `name`        VARCHAR(50)  NOT NULL COMMENT '姓名',
  `gender`      ENUM('M','F') COMMENT '性别',
  `title`       VARCHAR(50)  COMMENT '职称（教授/副教授等）',
  `dept_id`     INT          COMMENT '所属院系',
  `phone`       VARCHAR(20)  COMMENT '电话',
  `email`       VARCHAR(100) COMMENT '邮箱',
  `created_at`  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`dept_id`) REFERENCES `departments`(`dept_id`) ON DELETE SET NULL,
  INDEX `idx_teacher_dept` (`dept_id`),
  INDEX `idx_teacher_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='教师表';

-- ============================================
-- 6. 课程表 (courses)
-- ============================================
CREATE TABLE IF NOT EXISTS `courses` (
  `course_id`    VARCHAR(20)  PRIMARY KEY COMMENT '课程编号',
  `course_name`  VARCHAR(100) NOT NULL COMMENT '课程名称',
  `credits`      DECIMAL(3,1) NOT NULL COMMENT '学分',
  `hours`        SMALLINT     COMMENT '总学时',
  `type`         ENUM('必修','选修','公共') NOT NULL COMMENT '课程类型',
  `dept_id`      INT          COMMENT '开课院系',
  `created_at`   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`dept_id`) REFERENCES `departments`(`dept_id`) ON DELETE SET NULL,
  INDEX `idx_course_dept` (`dept_id`),
  INDEX `idx_course_type` (`type`),
  INDEX `idx_course_name` (`course_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='课程表';

-- ============================================
-- 7. 学期表 (semesters)
-- ============================================
CREATE TABLE IF NOT EXISTS `semesters` (
  `semester_id`    INT         PRIMARY KEY AUTO_INCREMENT COMMENT '学期编号',
  `academic_year`  VARCHAR(9)  NOT NULL COMMENT '学年（如"2025-2026"）',
  `semester_name`  VARCHAR(10) NOT NULL COMMENT '学期名称（秋季/春季/夏季）',
  `start_date`     DATE        NOT NULL COMMENT '开始日期',
  `end_date`       DATE        NOT NULL COMMENT '结束日期',
  `is_current`     BOOLEAN     DEFAULT FALSE COMMENT '是否为当前学期',
  `created_at`     TIMESTAMP   DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  UNIQUE KEY `uk_semester` (`academic_year`, `semester_name`),
  INDEX `idx_semester_current` (`is_current`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='学期表';

-- ============================================
-- 8. 授课表 (teaching)
-- ============================================
CREATE TABLE IF NOT EXISTS `teaching` (
  `teaching_id`  INT          PRIMARY KEY AUTO_INCREMENT COMMENT '授课唯一编号',
  `course_id`    VARCHAR(20)  NOT NULL COMMENT '课程ID',
  `teacher_id`   VARCHAR(20)  NOT NULL COMMENT '教师ID',
  `semester_id`  INT          NOT NULL COMMENT '学期ID',
  `classroom`    VARCHAR(50)  COMMENT '上课教室',
  `schedule`     VARCHAR(200) COMMENT '上课时间（如"周一1-2节"）',
  `capacity`     SMALLINT     DEFAULT 30 COMMENT '课程容量',
  `created_at`   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`course_id`) REFERENCES `courses`(`course_id`) ON DELETE RESTRICT,
  FOREIGN KEY (`teacher_id`) REFERENCES `teachers`(`teacher_id`) ON DELETE RESTRICT,
  FOREIGN KEY (`semester_id`) REFERENCES `semesters`(`semester_id`) ON DELETE RESTRICT,
  INDEX `idx_teaching_course` (`course_id`),
  INDEX `idx_teaching_teacher` (`teacher_id`),
  INDEX `idx_teaching_semester` (`semester_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='授课表';

-- ============================================
-- 9. 选课/成绩表 (enrollments)
-- ============================================
CREATE TABLE IF NOT EXISTS `enrollments` (
  `enroll_id`    INT          PRIMARY KEY AUTO_INCREMENT COMMENT '选课记录编号',
  `student_id`   VARCHAR(20)  NOT NULL COMMENT '学生ID',
  `teaching_id`  INT          NOT NULL COMMENT '授课ID',
  `score`        DECIMAL(5,2) COMMENT '总评成绩（0-100）',
  `grade_point`  DECIMAL(3,2) COMMENT '绩点',
  `enroll_time`  DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '选课时间',
  `status`       ENUM('正常','退课','缺考','违纪') DEFAULT '正常' COMMENT '选课状态',
  `created_at`   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`student_id`) REFERENCES `students`(`student_id`) ON DELETE RESTRICT,
  FOREIGN KEY (`teaching_id`) REFERENCES `teaching`(`teaching_id`) ON DELETE RESTRICT,
  UNIQUE KEY `uk_enrollment` (`student_id`, `teaching_id`),
  INDEX `idx_enroll_student` (`student_id`),
  INDEX `idx_enroll_teaching` (`teaching_id`),
  INDEX `idx_enroll_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='选课/成绩表';

-- ============================================
-- 10. 成绩等级表 (grade_scale)
-- ============================================
CREATE TABLE IF NOT EXISTS `grade_scale` (
  `grade_level` CHAR(1)      PRIMARY KEY COMMENT '等级（A、B、C、D、F）',
  `min_score`   DECIMAL(5,2) NOT NULL COMMENT '最低分数',
  `max_score`   DECIMAL(5,2) NOT NULL COMMENT '最高分数',
  `grade_point` DECIMAL(3,2) NOT NULL COMMENT '对应绩点',
  `description` VARCHAR(50)  COMMENT '描述（如"优秀"）'
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='成绩等级表';

-- ============================================
-- 11. 用户表 (users)
-- ============================================
CREATE TABLE IF NOT EXISTS `users` (
  `user_id`       INT          PRIMARY KEY AUTO_INCREMENT COMMENT '用户编号',
  `uuid`          VARCHAR(36)  NOT NULL UNIQUE COMMENT '用户唯一UUID',
  `username`      VARCHAR(50)  NOT NULL UNIQUE COMMENT '登录用户名',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '加密密码',
  `role`          ENUM('admin','teacher','student') NOT NULL COMMENT '角色',
  `ref_id`        VARCHAR(20)  COMMENT '关联的学生学号或教师工号',
  `last_login`    DATETIME     COMMENT '最后登录时间',
  `created_at`    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  INDEX `idx_user_role` (`role`),
  INDEX `idx_user_ref` (`ref_id`),
  INDEX `idx_user_username` (`username`),
  INDEX `idx_user_uuid` (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='用户表';

-- ============================================
-- 11.5. 用户权限表 (user_permissions)
-- ============================================
CREATE TABLE IF NOT EXISTS `user_permissions` (
  `perm_id`       INT          PRIMARY KEY AUTO_INCREMENT COMMENT '权限记录ID',
  `user_uuid`     VARCHAR(36)  NOT NULL COMMENT '用户UUID',
  `table_name`    VARCHAR(100) NOT NULL COMMENT '表名',
  `permission_code` VARCHAR(10) NOT NULL DEFAULT '000' COMMENT '权限代码(RWX)',
  `created_at`    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at`    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  FOREIGN KEY (`user_uuid`) REFERENCES `users`(`uuid`) ON DELETE CASCADE,
  UNIQUE KEY `uk_user_table` (`user_uuid`, `table_name`),
  INDEX `idx_perm_user` (`user_uuid`),
  INDEX `idx_perm_table` (`table_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='用户权限表';

-- ============================================
-- 12. 奖惩表 (rewards_punishments)
-- ============================================
CREATE TABLE IF NOT EXISTS `rewards_punishments` (
  `rp_id`             INT          PRIMARY KEY AUTO_INCREMENT COMMENT '奖惩记录ID',
  `student_id`        VARCHAR(20)  NOT NULL COMMENT '学生学号',
  `rp_type`           ENUM('奖励','处分') NOT NULL COMMENT '类型',
  `title`             VARCHAR(100) NOT NULL COMMENT '奖惩名称（如"三好学生"、"记过"）',
  `level`             VARCHAR(50)  COMMENT '级别（校级/院级；奖励分一等/二等；处分分警告/记过等）',
  `date`              DATE         NOT NULL COMMENT '发生或公布日期',
  `reason`            TEXT         COMMENT '原因/事由',
  `issuing_authority` VARCHAR(100) COMMENT '颁发或处分单位',
  `remark`            TEXT         COMMENT '备注（如撤销日期、文件编号）',
  `created_at`        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  FOREIGN KEY (`student_id`) REFERENCES `students`(`student_id`) ON DELETE CASCADE,
  INDEX `idx_rp_student` (`student_id`),
  INDEX `idx_rp_type` (`rp_type`),
  INDEX `idx_rp_date` (`date`),
  INDEX `idx_rp_student_date` (`student_id`, `date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='奖惩表';

-- ============================================
-- 13. 缴费表 (payments)
-- ============================================
CREATE TABLE IF NOT EXISTS `payments` (
  `payment_id`     INT          PRIMARY KEY AUTO_INCREMENT COMMENT '缴费流水号',
  `student_id`     VARCHAR(20)  NOT NULL COMMENT '学生学号',
  `fee_type`       VARCHAR(50)  NOT NULL COMMENT '费用类型（学费/住宿费/教材费等）',
  `academic_year`  VARCHAR(9)   NOT NULL COMMENT '学年（如"2025-2026"）',
  `semester`       VARCHAR(10)  COMMENT '学期（秋季/春季/夏季）',
  `amount_due`     DECIMAL(10,2) NOT NULL COMMENT '应缴金额',
  `amount_paid`    DECIMAL(10,2) DEFAULT 0.00 COMMENT '已缴金额',
  `payment_date`   DATE         COMMENT '最近一次缴费日期',
  `status`         ENUM('未缴','部分缴','已缴','退款') DEFAULT '未缴' COMMENT '缴费状态',
  `payment_method` VARCHAR(50)  COMMENT '缴费方式（银行转账/微信/现金等）',
  `remark`         TEXT         COMMENT '备注（如减免说明、滞纳金）',
  `updated_at`     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
  FOREIGN KEY (`student_id`) REFERENCES `students`(`student_id`) ON DELETE CASCADE,
  INDEX `idx_payment_student` (`student_id`),
  INDEX `idx_payment_year` (`academic_year`),
  INDEX `idx_payment_status` (`status`),
  INDEX `idx_payment_student_year` (`student_id`, `academic_year`, `semester`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='缴费表';

-- ============================================
-- 14. 宿舍房间表 (dorm_rooms)
-- ============================================
CREATE TABLE IF NOT EXISTS `dorm_rooms` (
  `room_id`      INT          PRIMARY KEY AUTO_INCREMENT COMMENT '房间唯一ID',
  `building`     VARCHAR(50)  NOT NULL COMMENT '楼栋名称',
  `room_number`  VARCHAR(20)  NOT NULL COMMENT '房间号',
  `capacity`     TINYINT      NOT NULL COMMENT '可住人数',
  `occupied`     TINYINT      DEFAULT 0 COMMENT '当前已住人数',
  `gender_limit` ENUM('M','F','不限') DEFAULT '不限' COMMENT '性别限制',
  `phone`        VARCHAR(20)  COMMENT '楼管电话',
  `created_at`   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  UNIQUE KEY `uk_dorm_room` (`building`, `room_number`),
  INDEX `idx_dorm_building` (`building`),
  INDEX `idx_dorm_gender` (`gender_limit`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='宿舍房间表';

-- ============================================
-- 15. 住宿分配表 (dorm_assignments)
-- ============================================
CREATE TABLE IF NOT EXISTS `dorm_assignments` (
  `assign_id`      INT          PRIMARY KEY AUTO_INCREMENT COMMENT '分配记录ID',
  `student_id`     VARCHAR(20)  NOT NULL COMMENT '学生学号',
  `room_id`        INT          NOT NULL COMMENT '房间ID',
  `bed_number`     VARCHAR(10)  COMMENT '床号（如"A床"、"1"）',
  `check_in_date`  DATE         NOT NULL COMMENT '入住日期',
  `check_out_date` DATE         COMMENT '退宿日期（空表示当前仍在住）',
  `status`         ENUM('在住','已退','调换') DEFAULT '在住' COMMENT '住宿状态',
  `remark`         TEXT         COMMENT '备注（如换宿舍原因）',
  `created_at`     TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`student_id`) REFERENCES `students`(`student_id`) ON DELETE CASCADE,
  FOREIGN KEY (`room_id`) REFERENCES `dorm_rooms`(`room_id`) ON DELETE RESTRICT,
  INDEX `idx_dorm_assign_student` (`student_id`),
  INDEX `idx_dorm_assign_room` (`room_id`),
  INDEX `idx_dorm_assign_status` (`status`),
  INDEX `idx_dorm_assign_student_status` (`student_id`, `status`),
  INDEX `idx_dorm_assign_room_status` (`room_id`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='住宿分配表';

-- ============================================
-- 16. 培养计划表 (curriculum)
-- ============================================
CREATE TABLE IF NOT EXISTS `curriculum` (
  `plan_id`           INT          PRIMARY KEY AUTO_INCREMENT COMMENT '培养计划项ID',
  `major_id`          INT          NOT NULL COMMENT '专业ID',
  `enrollment_year`   YEAR         NOT NULL COMMENT '入学年份（适用该计划的学生年级）',
  `course_id`         VARCHAR(20)  NOT NULL COMMENT '课程ID',
  `course_type`       ENUM('必修','选修','公共') DEFAULT '必修' COMMENT '课程性质',
  `recommended_term`  VARCHAR(20)  COMMENT '建议修读学期（如"第3学期"）',
  `min_grade`         DECIMAL(4,1) COMMENT '要求的最低成绩或绩点（如60或1.0）',
  `is_core`           BOOLEAN      DEFAULT FALSE COMMENT '是否专业核心课',
  `remark`            TEXT         COMMENT '备注',
  `created_at`        TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  FOREIGN KEY (`major_id`) REFERENCES `majors`(`major_id`) ON DELETE CASCADE,
  FOREIGN KEY (`course_id`) REFERENCES `courses`(`course_id`) ON DELETE CASCADE,
  UNIQUE KEY `uk_curriculum` (`major_id`, `enrollment_year`, `course_id`),
  INDEX `idx_curriculum_major` (`major_id`),
  INDEX `idx_curriculum_course` (`course_id`),
  INDEX `idx_curriculum_year` (`enrollment_year`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='培养计划表';

-- ============================================
-- 17. 选课日志表 (enroll_logs)
-- ============================================
CREATE TABLE IF NOT EXISTS `enroll_logs` (
  `log_id`          BIGINT       PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
  `student_id`      VARCHAR(20)  NOT NULL COMMENT '学生学号',
  `teaching_id`     INT          NOT NULL COMMENT '授课ID',
  `operation_type`  ENUM('选课','退课','成绩修改','状态变更') NOT NULL COMMENT '操作类型',
  `old_value`       TEXT         COMMENT '变更前的值',
  `new_value`       TEXT         COMMENT '变更后的值',
  `operator`        VARCHAR(50)  COMMENT '操作人（管理员/教师/系统）',
  `operator_ip`     VARCHAR(45)  COMMENT '操作IP地址',
  `reason`          TEXT         COMMENT '操作原因',
  `created_at`      TIMESTAMP    DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间戳',
  FOREIGN KEY (`student_id`) REFERENCES `students`(`student_id`) ON DELETE CASCADE,
  FOREIGN KEY (`teaching_id`) REFERENCES `teaching`(`teaching_id`) ON DELETE CASCADE,
  INDEX `idx_log_student` (`student_id`),
  INDEX `idx_log_teaching` (`teaching_id`),
  INDEX `idx_log_type` (`operation_type`),
  INDEX `idx_log_student_time` (`student_id`, `created_at`),
  INDEX `idx_log_teaching_type` (`teaching_id`, `operation_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='选课日志表';

-- ============================================
-- 初始化基础数据
-- ============================================

-- 初始化成绩等级标准（4.0绩点制）
INSERT INTO `grade_scale` (`grade_level`, `min_score`, `max_score`, `grade_point`, `description`) VALUES
('A', 90.00, 100.00, 4.00, '优秀'),
('B', 80.00, 89.99, 3.00, '良好'),
('C', 70.00, 79.99, 2.00, '中等'),
('D', 60.00, 69.99, 1.00, '及格'),
('F', 0.00, 59.99, 0.00, '不及格');

-- 初始化院系数据
INSERT INTO `departments` (`dept_name`, `dean`, `phone`) VALUES
('计算机学院', '张教授', '010-12345601'),
('自动化学院', '李教授', '010-12345602'),
('外国语学院', '王教授', '010-12345603'),
('数学学院', '赵教授', '010-12345604'),
('物理学院', '陈教授', '010-12345605'),
('经济管理学院', '刘教授', '010-12345606');

-- 初始化专业数据
INSERT INTO `majors` (`major_name`, `dept_id`, `duration`) VALUES
('计算机科学与技术', 1, 4),
('软件工程', 1, 4),
('网络工程', 1, 4),
('自动化', 2, 4),
('电气工程及其自动化', 2, 4),
('测控技术与仪器', 2, 4),
('英语', 3, 4),
('日语', 3, 4),
('数学与应用数学', 4, 4),
('信息与计算科学', 4, 4),
('应用物理学', 5, 4),
('工商管理', 6, 4),
('会计学', 6, 4);

-- 初始化班级数据（2022级示例）
INSERT INTO `classes` (`class_name`, `major_id`, `enrollment_year`, `advisor`) VALUES
('计科2201', 1, 2022, '张老师'),
('计科2202', 1, 2022, '李老师'),
('软工2201', 2, 2022, '王老师'),
('软工2202', 2, 2022, '赵老师'),
('自动化2201', 4, 2022, '陈老师'),
('电气2201', 5, 2022, '刘老师'),
('英语2201', 7, 2022, '周老师'),
('日语2201', 8, 2022, '吴老师'),
('数学2201', 9, 2022, '郑老师'),
('信计2201', 10, 2022, '孙老师');

-- 初始化学期数据
INSERT INTO `semesters` (`academic_year`, `semester_name`, `start_date`, `end_date`, `is_current`) VALUES
('2024-2025', '秋季', '2024-09-01', '2025-01-15', FALSE),
('2024-2025', '春季', '2025-02-20', '2025-07-05', TRUE),
('2025-2026', '秋季', '2025-09-01', '2026-01-15', FALSE);

-- 初始化课程数据（示例）
INSERT INTO `courses` (`course_id`, `course_name`, `credits`, `hours`, `type`, `dept_id`) VALUES
('CS101', '计算机导论', 3.0, 48, '必修', 1),
('CS102', '程序设计基础', 4.0, 64, '必修', 1),
('CS201', '数据结构', 4.0, 64, '必修', 1),
('CS202', '算法设计与分析', 3.5, 56, '必修', 1),
('CS301', '数据库原理', 3.5, 56, '必修', 1),
('CS302', '操作系统', 4.0, 64, '必修', 1),
('SE201', '软件工程', 3.0, 48, '必修', 1),
('NET201', '计算机网络', 3.5, 56, '必修', 1),
('AUTO101', '自动控制原理', 4.0, 64, '必修', 2),
('EE101', '电路原理', 4.0, 64, '必修', 2),
('MATH101', '高等数学A', 5.0, 80, '必修', 4),
('MATH102', '线性代数', 3.0, 48, '必修', 4),
('ENG101', '大学英语', 4.0, 64, '公共', NULL),
('PE101', '体育', 1.0, 32, '公共', NULL);

-- 初始化教师数据（示例）
INSERT INTO `teachers` (`teacher_id`, `name`, `gender`, `title`, `dept_id`, `phone`, `email`) VALUES
('T001', '张教授', 'M', '教授', 1, '13800000001', 'zhang@example.com'),
('T002', '李副教授', 'M', '副教授', 1, '13800000002', 'li@example.com'),
('T003', '王讲师', 'F', '讲师', 1, '13800000003', 'wang@example.com'),
('T004', '赵教授', 'M', '教授', 2, '13800000004', 'zhao@example.com'),
('T005', '陈副教授', 'F', '副教授', 4, '13800000005', 'chen@example.com'),
('T006', '刘老师', 'M', '讲师', 4, '13800000006', 'liu@example.com');

-- 初始化授课安排（示例）
INSERT INTO `teaching` (`course_id`, `teacher_id`, `semester_id`, `classroom`, `schedule`, `capacity`) VALUES
('CS101', 'T001', 1, 'A101', '周一1-2节', 60),
('CS102', 'T002', 1, 'A102', '周二3-4节', 60),
('CS201', 'T002', 2, 'B201', '周三5-6节', 50),
('CS301', 'T003', 2, 'B202', '周四7-8节', 50),
('MATH101', 'T005', 1, 'C101', '周一3-4节', 80),
('MATH102', 'T006', 2, 'C102', '周二1-2节', 80);

-- 初始化管理员账号
-- 默认密码: admin123
INSERT INTO `users` (`uuid`, `username`, `password_hash`, `role`, `ref_id`) VALUES
('a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'admin', '6oW0mxWYd76qGntJUZn/JQ==$7HAZRkxKG2qG8Si273yMOKhH+E9spm1vzVmB7uXIORI=', 'admin', NULL);

-- ============================================
-- 创建触发器：自动更新宿舍已住人数
-- ============================================
DELIMITER //

CREATE TRIGGER `trg_dorm_checkin` 
AFTER INSERT ON `dorm_assignments`
FOR EACH ROW
BEGIN
  IF NEW.status = '在住' THEN
    UPDATE `dorm_rooms` SET `occupied` = `occupied` + 1 
    WHERE `room_id` = NEW.room_id;
  END IF;
END//

CREATE TRIGGER `trg_dorm_checkout`
AFTER UPDATE ON `dorm_assignments`
FOR EACH ROW
BEGIN
  IF OLD.status = '在住' AND NEW.status = '已退' THEN
    UPDATE `dorm_rooms` SET `occupied` = `occupied` - 1 
    WHERE `room_id` = NEW.room_id;
  END IF;
END//

DELIMITER ;

-- ============================================
-- 创建视图：方便查询
-- ============================================

-- 学生完整信息视图
CREATE VIEW `v_student_full` AS
SELECT 
  s.*,
  d.dept_name,
  c.class_name,
  m.major_name
FROM `students` s
LEFT JOIN `departments` d ON s.dept_id = d.dept_id
LEFT JOIN `classes` c ON s.class_id = c.class_id
LEFT JOIN `majors` m ON c.major_id = m.major_id;

-- 授课完整信息视图
CREATE VIEW `v_teaching_full` AS
SELECT 
  t.*,
  c.course_name,
  c.credits,
  c.hours,
  c.type AS course_type,
  te.name AS teacher_name,
  te.title AS teacher_title,
  s.academic_year,
  s.semester_name,
  s.is_current
FROM `teaching` t
JOIN `courses` c ON t.course_id = c.course_id
JOIN `teachers` te ON t.teacher_id = te.teacher_id
JOIN `semesters` s ON t.semester_id = s.semester_id;

-- 选课完整信息视图
CREATE VIEW `v_enrollment_full` AS
SELECT 
  e.*,
  s.name AS student_name,
  s.class_id,
  c.class_name,
  t.course_id,
  co.course_name,
  co.credits,
  te.teacher_id,
  te.name AS teacher_name,
  sem.academic_year,
  sem.semester_name
FROM `enrollments` e
JOIN `students` s ON e.student_id = s.student_id
LEFT JOIN `classes` c ON s.class_id = c.class_id
JOIN `teaching` t ON e.teaching_id = t.teaching_id
JOIN `courses` co ON t.course_id = co.course_id
JOIN `teachers` te ON t.teacher_id = te.teacher_id
JOIN `semesters` sem ON t.semester_id = sem.semester_id;
