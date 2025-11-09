/*
 Navicat Premium Dump SQL

 Source Server         : test1
 Source Server Type    : MySQL
 Source Server Version : 80041 (8.0.41)
 Source Host           : localhost:3306
 Source Schema         : face_rec

 Target Server Type    : MySQL
 Target Server Version : 80041 (8.0.41)
 File Encoding         : 65001

 Date: 14/09/2025 13:21:45
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for attendance
-- ----------------------------
DROP TABLE IF EXISTS `attendance`;
CREATE TABLE `attendance`  (
  `attendance_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NULL DEFAULT NULL,
  `clock_in_time` datetime NULL DEFAULT NULL COMMENT '上班时间',
  `clock_out_time` datetime NULL DEFAULT NULL COMMENT '下班时间',
  `status` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '考勤状态：未出勤、迟到、早退、正常、加班、请假、未签退',
  `work_date` date NULL DEFAULT NULL COMMENT '工作日期',
  `clock_in_status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '上班打卡状态：正常、迟到',
  `clock_out_status` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '下班打卡状态：正常、早退、加班、未签退',
  PRIMARY KEY (`attendance_id`) USING BTREE,
  INDEX `attendance_user`(`user_id` ASC) USING BTREE,
  INDEX `idx_work_date`(`work_date` ASC) USING BTREE,
  CONSTRAINT `attendance_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;