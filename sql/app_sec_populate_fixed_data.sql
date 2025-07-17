USE social_sage_db;

START TRANSACTION;

INSERT INTO statuses (title)
VALUES
	("pending"),
	("approved"),
    ("rejected");
    
INSERT INTO user_role (user_role)
VALUES 
	("elderly"),
    ("volunteer"),
    ("admin");
    
INSERT INTO activity_occurences (title)
VALUES 
	("twice a week"),
    ("once a week"),
    ("every fortnight"),
    ("every month"),
    ("every two months");
    
INSERT INTO activity_location (location_code, name)
VALUES 
	("ALCC", "aljunied community center"),
    ("ANCC", "anchorvale community center"),
    ("AMKCC", "ang mo kio community center"),
    ("ARCC", "ayer rajah community center"),
    ("BICC", "bishan community center"),
    ("BLCC", "boon lay community center"),
    ("BHCC", "braddel heights community center"),
    ("BBCC", "bukit batok community center"),
    ("BPCC", "bukit panjang community center"),
    ("BTCC", "bukit timah community center"),
    ("CSCC", "cheng san community center"),
    ("CCKCC", "chua chu kang community center"),
    ("CCC", "clementi community center"),
    ("ECC", "eunos community center"),
    ("FCC", "fengshan community center"),
    ("FECC", "fernvale community center"),
    ("HCC", "hougang community center"),
    ("JCCC", "joo chiat community center");
    
INSERT INTO users (user_id, first_name, last_name, email, password, profile_pic, user_role)
VALUES
    (1, "John", "Doe", "roblox@gmail.com", "password123", "elderly.jpg", "3");

INSERT INTO interest_group (group_id, name, topic, description, max_size, is_public, picture, activity_occurence_id, status_id, owner)
VALUES
    (1, "Health and Wellness", "Fitness", "Activities focused on improving health and wellness for seniors.", 30, TRUE, "elderly.jpg", 1, 1, "1"),
    (2, "Gardening Enthusiasts", "Gardening", "A group for seniors who love gardening and nature.", 20, TRUE, "elderly.jpg", 2, 1, "1"),
    (3, "Culinary Arts", "Cooking", "A group for seniors interested in cooking and sharing recipes.", 15, TRUE, "elderly.jpg", 3, 1, "1");


INSERT INTO interest_activity (activity_id, name, description, start_datetime, end_datetime, max_size, funds, location_code, remarks, picture, status_id, group_id)
VALUES
    (1, "Yoga for Seniors", "A gentle yoga class designed for seniors to improve flexibility and relaxation.", "2023-11-01 10:00:00", "2023-11-01 11:00:00", 20, 50.00, "ALCC", "Bring your own mat.", "elderly.jpg", 1, 1),
    (2, "Gardening Club", "Join us in our community garden to learn about gardening and enjoy nature.", "2023-11-02 09:00:00", "2023-11-02 11:00:00", 15, 30.00, "ANCC", "All tools provided.", "elderly.jpg", 1, 2),
    (3, "Cooking Class", "Learn to cook healthy meals with our experienced chef.", "2023-11-03 14:00:00", "2023-11-03 16:00:00", 10, 40.00, "AMKCC", "Ingredients provided.", "elderly.jpg", 1, 3);

COMMIT;