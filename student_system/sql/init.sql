-- ============================================
-- 学生信息管理系统 - 数据库初始化脚本
-- 兼容 MySQL 5.6 标准
-- ============================================

DROP DATABASE IF EXISTS `student_manage`;

CREATE DATABASE IF NOT EXISTS `student_manage`
  DEFAULT CHARACTER SET utf8;

USE `student_manage`;

-- ============================================
-- 学生信息表
-- ============================================
CREATE TABLE IF NOT EXISTS `student_info` (
  `id`           INT          PRIMARY KEY AUTO_INCREMENT NOT NULL COMMENT '主键自增ID',
  `student_no`   VARCHAR(20)  UNIQUE NOT NULL COMMENT '学生学号',
  `student_name` VARCHAR(30)  NOT NULL COMMENT '姓名',
  `gender`       VARCHAR(6)   DEFAULT NULL COMMENT '性别',
  `age`          TINYINT      DEFAULT NULL COMMENT '年龄',
  `major`        VARCHAR(50)  DEFAULT NULL COMMENT '专业',
  `grade`        VARCHAR(20)  DEFAULT NULL COMMENT '年级',
  `class_name`   VARCHAR(30)  DEFAULT NULL COMMENT '班级',
  `create_time`  DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '录入时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='学生信息表';

-- ============================================
-- 系统管理员账号表
-- ============================================
CREATE TABLE IF NOT EXISTS `user_info` (
  `uid`         INT          PRIMARY KEY AUTO_INCREMENT COMMENT '用户主键',
  `username`    VARCHAR(32)  NOT NULL UNIQUE COMMENT '登录账号，唯一不可重复',
  `password`    VARCHAR(64)  NOT NULL COMMENT '登录密码',
  `real_name`   VARCHAR(20)  DEFAULT NULL COMMENT '管理员姓名',
  `role`        VARCHAR(10)  DEFAULT 'user' COMMENT '角色：admin/user',
  `create_time` DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '账号创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='系统管理员账号表';
