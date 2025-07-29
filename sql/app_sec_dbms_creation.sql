-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema social_sage_db
-- -----------------------------------------------------
DROP SCHEMA IF EXISTS `social_sage_db` ;

-- -----------------------------------------------------
-- Schema social_sage_db
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `social_sage_db` DEFAULT CHARACTER SET utf8 ;
USE `social_sage_db` ;

-- -----------------------------------------------------
-- Table `social_sage_db`.`user_role`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `social_sage_db`.`user_role` ;

CREATE TABLE IF NOT EXISTS `social_sage_db`.`user_role` (
  `role_id` TINYINT(1) NOT NULL AUTO_INCREMENT,
  `user_role` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`role_id`),
  UNIQUE INDEX `user_role_UNIQUE` (`user_role` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `social_sage_db`.`users`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `social_sage_db`.`users` ;

CREATE TABLE IF NOT EXISTS `social_sage_db`.`users` (
  `user_id` INT NOT NULL AUTO_INCREMENT,
  `first_name` VARCHAR(50) NOT NULL,
  `last_name` VARCHAR(50) NOT NULL,
  `email` VARCHAR(50) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `profile_pic` VARCHAR(255) NULL DEFAULT NULL,
  `email_notif` TINYINT NOT NULL DEFAULT 1,
  `mfa_secret` VARCHAR(50) NULL DEFAULT NULL,
  `mfa_enabled` TINYINT NOT NULL DEFAULT 0,
  `user_role` TINYINT NULL DEFAULT NULL,
  `user_role` TINYINT NULL DEFAULT NULL ,
  `mfa_secret` VARCHAR(32) NULL DEFAULT NULL,
  `mfa_enabled` TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`user_id`),
  INDEX `fk_user_role_idx` (`user_role` ASC) VISIBLE,
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE,
  CONSTRAINT `fk_user_role`
    FOREIGN KEY (`user_role`)
    REFERENCES `social_sage_db`.`user_role` (`role_id`)
    ON DELETE NO ACTION
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `social_sage_db`.`activity_occurences`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `social_sage_db`.`activity_occurences` ;

CREATE TABLE IF NOT EXISTS `social_sage_db`.`activity_occurences` (
  `activity_occurence_id` INT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`activity_occurence_id`),
  UNIQUE INDEX `title_UNIQUE` (`title` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `social_sage_db`.`statuses`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `social_sage_db`.`statuses` ;

CREATE TABLE IF NOT EXISTS `social_sage_db`.`statuses` (
  `status_id` TINYINT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`status_id`),
  UNIQUE INDEX `title_UNIQUE` (`title` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `social_sage_db`.`interest_group`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `social_sage_db`.`interest_group` ;

CREATE TABLE IF NOT EXISTS `social_sage_db`.`interest_group` (
  `group_id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(50) NOT NULL,
  `topic` VARCHAR(50) NOT NULL,
  `description` VARCHAR(200) NOT NULL,
  `max_size` TINYINT NOT NULL,
  `is_public` TINYINT NOT NULL,
  `picture` VARCHAR(255) NULL DEFAULT NULL,
  `proposal` VARCHAR(1000) NOT NULL,
  `activity_occurence_id` INT NOT NULL,
  `status_id` TINYINT NOT NULL,
  `owner` INT NOT NULL,
  PRIMARY KEY (`group_id`),
  INDEX `fk_interest_group_activity_occurences1_idx` (`activity_occurence_id` ASC) VISIBLE,
  INDEX `fk_interest_group_group_status1_idx` (`status_id` ASC) VISIBLE,
  INDEX `fk_interest_group_users1_idx` (`owner` ASC) VISIBLE,
  CONSTRAINT `fk_interest_group_activity_occurences1`
    FOREIGN KEY (`activity_occurence_id`)
    REFERENCES `social_sage_db`.`activity_occurences` (`activity_occurence_id`)
    ON DELETE NO ACTION
    ON UPDATE CASCADE,
  CONSTRAINT `fk_interest_group_group_status1`
    FOREIGN KEY (`status_id`)
    REFERENCES `social_sage_db`.`statuses` (`status_id`)
    ON DELETE NO ACTION
    ON UPDATE CASCADE,
  CONSTRAINT `fk_interest_group_users1`
    FOREIGN KEY (`owner`)
    REFERENCES `social_sage_db`.`users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `social_sage_db`.`tags`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `social_sage_db`.`tags` ;

CREATE TABLE IF NOT EXISTS `social_sage_db`.`tags` (
  `tag_id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`tag_id`),
  UNIQUE INDEX `name_UNIQUE` (`name` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `social_sage_db`.`user_interest_group`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `social_sage_db`.`user_interest_group` ;

CREATE TABLE IF NOT EXISTS `social_sage_db`.`user_interest_group` (
  `user_id` INT NOT NULL,
  `group_id` INT NOT NULL,
  `status_id` TINYINT NOT NULL,
  `date_joined` DATETIME NOT NULL,
  INDEX `fk_user_interest_group_users1_idx` (`user_id` ASC) VISIBLE,
  INDEX `fk_user_interest_group_interest_group1_idx` (`group_id` ASC) VISIBLE,
  PRIMARY KEY (`user_id`, `group_id`),
  INDEX `fk_user_interest_group_statuses1_idx` (`status_id` ASC) VISIBLE,
  CONSTRAINT `fk_user_interest_group_users1`
    FOREIGN KEY (`user_id`)
    REFERENCES `social_sage_db`.`users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_user_interest_group_interest_group1`
    FOREIGN KEY (`group_id`)
    REFERENCES `social_sage_db`.`interest_group` (`group_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_user_interest_group_statuses1`
    FOREIGN KEY (`status_id`)
    REFERENCES `social_sage_db`.`statuses` (`status_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `social_sage_db`.`group_discussion_post`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `social_sage_db`.`group_discussion_post` ;

CREATE TABLE IF NOT EXISTS `social_sage_db`.`group_discussion_post` (
  `post_id` INT NOT NULL AUTO_INCREMENT,
  `title` VARCHAR(50) NOT NULL,
  `description` VARCHAR(1000) NOT NULL,
  `group_id` INT NOT NULL,
  PRIMARY KEY (`post_id`),
  INDEX `fk_group_discussion_post_interest_group1_idx` (`group_id` ASC) VISIBLE,
  CONSTRAINT `fk_group_discussion_post_interest_group1`
    FOREIGN KEY (`group_id`)
    REFERENCES `social_sage_db`.`interest_group` (`group_id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `social_sage_db`.`post_comment`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `social_sage_db`.`post_comment` ;

CREATE TABLE IF NOT EXISTS `social_sage_db`.`post_comment` (
  `comment_id` INT NOT NULL AUTO_INCREMENT,
  `description` VARCHAR(1000) NOT NULL,
  `post_id` INT NOT NULL,
  PRIMARY KEY (`comment_id`),
  INDEX `fk_post_comment_group_discussion_post1_idx` (`post_id` ASC) VISIBLE,
  CONSTRAINT `fk_post_comment_group_discussion_post1`
    FOREIGN KEY (`post_id`)
    REFERENCES `social_sage_db`.`group_discussion_post` (`post_id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `social_sage_db`.`activity_location`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `social_sage_db`.`activity_location` ;

CREATE TABLE IF NOT EXISTS `social_sage_db`.`activity_location` (
  `location_code` VARCHAR(7) NOT NULL,
  `name` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`location_code`),
  UNIQUE INDEX `name_UNIQUE` (`name` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `social_sage_db`.`interest_activity`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `social_sage_db`.`interest_activity` ;

CREATE TABLE IF NOT EXISTS `social_sage_db`.`interest_activity` (
  `activity_id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(50) NOT NULL,
  `description` VARCHAR(200) NOT NULL,
  `start_datetime` DATETIME NOT NULL,
  `end_datetime` DATETIME NOT NULL,
  `max_size` TINYINT NOT NULL,
  `funds` SMALLINT NOT NULL,
  `location_code` VARCHAR(7) NOT NULL,
  `remarks` VARCHAR(300) NULL DEFAULT NULL,
  `picture` VARCHAR(200) NULL DEFAULT NULL,
  `status_id` TINYINT NOT NULL,
  `group_id` INT NOT NULL,
  PRIMARY KEY (`activity_id`),
  INDEX `fk_interest_activity_interest_group1_idx` (`group_id` ASC) VISIBLE,
  INDEX `fk_interest_activity_statuses1_idx` (`status_id` ASC) VISIBLE,
  INDEX `fk_interest_activity_activity_location1_idx` (`location_code` ASC) VISIBLE,
  CONSTRAINT `fk_interest_activity_interest_group1`
    FOREIGN KEY (`group_id`)
    REFERENCES `social_sage_db`.`interest_group` (`group_id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_interest_activity_statuses1`
    FOREIGN KEY (`status_id`)
    REFERENCES `social_sage_db`.`statuses` (`status_id`)
    ON DELETE NO ACTION
    ON UPDATE CASCADE,
  CONSTRAINT `fk_interest_activity_activity_location1`
    FOREIGN KEY (`location_code`)
    REFERENCES `social_sage_db`.`activity_location` (`location_code`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `social_sage_db`.`activity_tags`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `social_sage_db`.`activity_tags` ;

CREATE TABLE IF NOT EXISTS `social_sage_db`.`activity_tags` (
  `activity_id` INT NOT NULL,
  `tag_id` INT NOT NULL,
  INDEX `fk_activity_tags_interest_activity1_idx` (`activity_id` ASC) VISIBLE,
  PRIMARY KEY (`tag_id`, `activity_id`),
  CONSTRAINT `fk_activity_tags_interest_activity1`
    FOREIGN KEY (`activity_id`)
    REFERENCES `social_sage_db`.`interest_activity` (`activity_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_activity_tags_tags1`
    FOREIGN KEY (`tag_id`)
    REFERENCES `social_sage_db`.`tags` (`tag_id`)
    ON DELETE CASCADE
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `social_sage_db`.`calendar_event`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `social_sage_db`.`calendar_event` ;

CREATE TABLE IF NOT EXISTS `social_sage_db`.`calendar_event` (
  `event_id` INT NOT NULL,
  `title` VARCHAR(50) NOT NULL,
  `start_datetime` DATETIME NOT NULL,
  `end_datetime` DATETIME NOT NULL,
  `user_id` INT NOT NULL,
  PRIMARY KEY (`event_id`),
  INDEX `fk_calendar_event_users1_idx` (`user_id` ASC) VISIBLE,
  CONSTRAINT `fk_calendar_event_users1`
    FOREIGN KEY (`user_id`)
    REFERENCES `social_sage_db`.`users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `social_sage_db`.`flagged_activities`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `social_sage_db`.`flagged_activities` ;

CREATE TABLE IF NOT EXISTS `social_sage_db`.`flagged_activities` (
  `flag_id` VARCHAR(45) NOT NULL,
  `activity_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `status_id` TINYINT NOT NULL,
  `reason` VARCHAR(255) NULL DEFAULT NULL,
  INDEX `fk_flagged_groups_interest_activity1_idx` (`activity_id` ASC) VISIBLE,
  INDEX `fk_flagged_groups_users1_idx` (`user_id` ASC) VISIBLE,
  PRIMARY KEY (`flag_id`),
  INDEX `fk_flagged_groups_statuses1_idx` (`status_id` ASC) VISIBLE,
  CONSTRAINT `fk_flagged_groups_interest_activity1`
    FOREIGN KEY (`activity_id`)
    REFERENCES `social_sage_db`.`interest_activity` (`activity_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_flagged_groups_users1`
    FOREIGN KEY (`user_id`)
    REFERENCES `social_sage_db`.`users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_flagged_groups_statuses1`
    FOREIGN KEY (`status_id`)
    REFERENCES `social_sage_db`.`statuses` (`status_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `social_sage_db`.`flagged_groups`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `social_sage_db`.`flagged_groups` ;

CREATE TABLE IF NOT EXISTS `social_sage_db`.`flagged_groups` (
  `flag_id` INT NOT NULL,
  `group_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `status_id` TINYINT NOT NULL,
  `reason` VARCHAR(255) NULL DEFAULT NULL,
  PRIMARY KEY (`flag_id`),
  INDEX `fk_flagged_groups_interest_group1_idx` (`group_id` ASC) VISIBLE,
  INDEX `fk_flagged_groups_users2_idx` (`user_id` ASC) VISIBLE,
  INDEX `fk_flagged_groups_statuses2_idx` (`status_id` ASC) VISIBLE,
  CONSTRAINT `fk_flagged_groups_interest_group1`
    FOREIGN KEY (`group_id`)
    REFERENCES `social_sage_db`.`interest_group` (`group_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_flagged_groups_users2`
    FOREIGN KEY (`user_id`)
    REFERENCES `social_sage_db`.`users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_flagged_groups_statuses2`
    FOREIGN KEY (`status_id`)
    REFERENCES `social_sage_db`.`statuses` (`status_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `social_sage_db`.`user_interest_activity`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `social_sage_db`.`user_interest_activity` ;

CREATE TABLE IF NOT EXISTS `social_sage_db`.`user_interest_activity` (
  `activity_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `join_datetime` DATETIME NOT NULL DEFAULT NOW(),
  INDEX `fk_user_interest_activity_interest_activity1_idx` (`activity_id` ASC) VISIBLE,
  INDEX `fk_user_interest_activity_users1_idx` (`user_id` ASC) VISIBLE,
  PRIMARY KEY (`activity_id`, `user_id`),
  CONSTRAINT `fk_user_interest_activity_interest_activity1`
    FOREIGN KEY (`activity_id`)
    REFERENCES `social_sage_db`.`interest_activity` (`activity_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_user_interest_activity_users1`
    FOREIGN KEY (`user_id`)
    REFERENCES `social_sage_db`.`users` (`user_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
