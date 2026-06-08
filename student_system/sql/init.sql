-- ============================================
-- 学生信息管理系统 - 数据库初始化脚本
-- 多表复合存储架构：4张关联表 + 用户表
-- ============================================

DROP DATABASE IF EXISTS `student_manage`;

CREATE DATABASE IF NOT EXISTS `student_manage`
  DEFAULT CHARACTER SET utf8;

USE `student_manage`;

-- ============================================
-- 学院表
-- ============================================
CREATE TABLE IF NOT EXISTS `departments` (
  `dept_id`   INT         PRIMARY KEY AUTO_INCREMENT COMMENT '学院ID',
  `dept_name` VARCHAR(50) NOT NULL UNIQUE COMMENT '学院名称'
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='学院表';

-- ============================================
-- 专业表
-- ============================================
CREATE TABLE IF NOT EXISTS `majors` (
  `major_id`   INT         PRIMARY KEY AUTO_INCREMENT COMMENT '专业ID',
  `major_name` VARCHAR(50) NOT NULL COMMENT '专业名称',
  `dept_id`    INT         NOT NULL COMMENT '所属学院ID',
  FOREIGN KEY (`dept_id`) REFERENCES `departments`(`dept_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='专业表';

-- ============================================
-- 班级表
-- ============================================
CREATE TABLE IF NOT EXISTS `classes` (
  `class_id`  INT         PRIMARY KEY AUTO_INCREMENT COMMENT '班级ID',
  `class_name` VARCHAR(30) NOT NULL COMMENT '班级名称',
  `major_id`  INT         NOT NULL COMMENT '所属专业ID',
  `grade`     VARCHAR(20) DEFAULT NULL COMMENT '年级',
  FOREIGN KEY (`major_id`) REFERENCES `majors`(`major_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='班级表';

-- ============================================
-- 学生表
-- ============================================
CREATE TABLE IF NOT EXISTS `students` (
  `student_id`   INT          PRIMARY KEY AUTO_INCREMENT NOT NULL COMMENT '主键自增ID',
  `student_no`   VARCHAR(20)  UNIQUE NOT NULL COMMENT '学生学号',
  `student_name` VARCHAR(30)  NOT NULL COMMENT '姓名',
  `gender`       VARCHAR(6)   DEFAULT NULL COMMENT '性别',
  `age`          TINYINT      DEFAULT NULL COMMENT '年龄',
  `class_id`     INT          DEFAULT NULL COMMENT '所属班级ID',
  `create_time`  DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '录入时间',
  FOREIGN KEY (`class_id`) REFERENCES `classes`(`class_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='学生表';

-- ============================================
-- 系统用户表
-- ============================================
CREATE TABLE IF NOT EXISTS `user_info` (
  `uid`         INT          PRIMARY KEY AUTO_INCREMENT COMMENT '用户主键',
  `username`    VARCHAR(32)  NOT NULL UNIQUE COMMENT '登录账号',
  `password`    VARCHAR(64)  NOT NULL COMMENT '登录密码',
  `real_name`   VARCHAR(20)  DEFAULT NULL COMMENT '用户姓名',
  `create_time` DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '账号创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='系统用户表';

-- ============================================
-- 插入样例数据
-- ============================================
INSERT INTO `departments` (`dept_name`) VALUES
('计算机学院'),
('自动化学院'),
('外国语学院'),
('数学学院');

INSERT INTO `majors` (`major_name`, `dept_id`) VALUES
('计算机科学与技术', 1),
('软件工程', 1),
('自动化', 2),
('电气工程', 2),
('英语', 3),
('日语', 3),
('数学与应用数学', 4),
('信息与计算科学', 4);

INSERT INTO `classes` (`class_name`, `major_id`, `grade`) VALUES
('计科1班', 1, '2022'),
('计科2班', 1, '2022'),
('软工1班', 2, '2022'),
('软工2班', 2, '2022'),
('自动化1班', 3, '2022'),
('电气1班', 4, '2022'),
('英语1班', 5, '2022'),
('日语1班', 6, '2022'),
('数学1班', 7, '2022'),
('信计1班', 8, '2022');
