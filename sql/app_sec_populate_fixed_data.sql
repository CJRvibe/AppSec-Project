USE social_sage_db;

START TRANSACTION;
BEGIN;

INSERT INTO statuses (status_id, title)
VALUES
	(1, "pending"),
	(2, "approved"),
    (3, "rejected"),
    (4, "completed"),
    (5, "cancelled"),
    (6, "suspended");
    
INSERT INTO user_role (role_id, user_role)
VALUES 
	(1, "elderly"),
    (2, "volunteer"),
    (3, "admin");
    
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
    
INSERT INTO users (first_name, last_name, email, password, user_role)
VALUES
    ("Jian Hao", "Boo", "boojianhao@gmail.com", "scrypt:32768:8:1$OdjtJNaE4MmMEhUi$aeba4e9565b897dd40b45ad91fe5e10ae253a324d79d4ec891d29ad54aa690c6ac989b953e9a6c303cf526cbc748b9f537d07a84a3cc335fd3d450df99920674", 1),
    ("Tom", "Tan", "tomtan@gmail.com", "scrypt:32768:8:1$nDxwfSmPjmWDJ3dV$ca54472e55e47f0bd573971c205331e20bb3d1fba892ee365ba2e5aa533ad8f35dbc127aee92b5a635efe73e19c63e16dffcbaf8d6cea2ae422feb45ed1a7008", 2),
    ("social", "sage", "socialsage.management@gmail.com", "scrypt:32768:8:1$NpJdo0T9CYT9txvD$85a4f4c1b0b1e0599520eba9db3dbcb1b70af0c3b51e2f762856e4ee4e433c0d194ae00f2bd331500cb77d5a65dd14219b27111813cc51a2a0db1291a4d712d1", 3);
    
INSERT INTO interest_group (group_id, name, topic, description, max_size, is_public, picture, proposal, activity_occurence_id, status_id, owner)
VALUES
    (1, "Health and Wellness", "Fitness", "Activities focused on improving health and wellness for seniors.", 30, 1, "healthandwellness.jpg", "A new proposal for health and wellness", 1, 2, 2),
    (2, "Gardening Enthusiasts", "Gardening", "A group for seniors who love gardening and nature.", 20, 0, "gardeningenthusiasts.jpg", "Another proposal", 2, 2, 2),
    (3, "Culinary Arts", "Cooking", "A group for seniors interested in cooking and sharing recipes.", 15, 1, "culinary.jpeg", "Last proposal", 3, 2, 2),
    (4, "Mahjong Strategists", "Gambling", "A group for seniors who love mahjong", 50, 1, "mahjong.jpg", "We love gambling", 3, 1, 2),
    (5, "Super Chefz", "Cooking", "A group for seniors who love cooking", 50, 1, "superchefz.jpg", "We love cooking", 3, 1, 2),
    (6, "Art and Craft", "Arts", "A group for seniors who love arts and crafts", 20, 1, "artncraft.jpg", "We love arts and crafts", 2, 3, 2),
    (7, "Book Lovers", "Literature", "A group for seniors who love reading and discussing books", 25, 1, "bookreading.png", "We love reading", 2, 3, 2),
    (8, "Music and Dance", "Music", "A group for seniors who love music and dance", 30, 1, "dance.jpg", "We love music and dance", 2, 6, 2);


INSERT INTO interest_activity (activity_id, name, description, start_datetime, end_datetime, max_size, funds, location_code, remarks, picture, status_id, group_id)
VALUES
    (1, "Yoga for Seniors", "A gentle yoga class designed for seniors to improve flexibility and relaxation.", "2023-11-01 10:00:00", "2023-11-01 11:00:00", 20, 50.00, "ALCC", "Bring your own mat.", "elderly.jpg", 1, 1),
    (2, "Gardening Club", "Join us in our community garden to learn about gardening and enjoy nature.", "2023-11-02 09:00:00", "2023-11-02 11:00:00", 15, 30.00, "ANCC", "All tools provided.", "elderly.jpg", 2, 2),
    (3, "Cooking Class", "Learn to cook healthy meals with our experienced chef.", "2023-11-03 14:00:00", "2023-11-03 16:00:00", 10, 40.00, "AMKCC", "Ingredients provided.", "elderly.jpg", 1, 3),
    (4, "Mahjong Tournament", "Compete in our monthly mahjong tournament with exciting prizes.", "2023-11-04 13:00:00", "2023-11-04 17:00:00", 30, 20.00, "ARCC", "Bring your own set if possible.", NULL, 1, 4),
    (5, "Cooking Competition", "Show off your culinary skills in our cooking competition.", "2023-11-05 10:00:00", "2023-11-05 14:00:00", 25, 60.00, "BICC", "All ingredients provided.", NULL, 1, 5),
    (6, "Art and Craft Workshop", "A creative workshop for seniors to explore their artistic side.", "2023-11-06 10:00:00", "2023-11-06 12:00:00", 15, 25.00, "BLCC", "Materials provided.", NULL, 1, 2),
    (7, "Book Club", "Join our book club to discuss and share your love for literature.", "2023-11-07 15:00:00", "2023-11-07 17:00:00", 20, 10.00, "BHCC", "Bring your favorite book.", NULL, 1, 2),
    (8, "Tai Chi Class", "A relaxing tai chi class for seniors to improve balance and mindfulness.", "2023-11-08 09:00:00", "2023-11-08 10:30:00", 20, 15.00, "BBCC", "Wear comfortable clothing.", NULL, 1, 1),
    (9, "Dance Class", "Join our dance class to learn new moves and have fun.", "2023-11-09 16:00:00", "2023-11-09 18:00:00", 25, 20.00, "BPCC", "No prior experience needed.", NULL, 2, 1),
    (10, "Morning Walk", "A morning walk session to enjoy the fresh air and socialize.", "2023-11-10 07:00:00", "2023-11-10 08:30:00", 30, 5.00, "BTCC", "Wear comfortable shoes.", NULL, 3, 1),
    (11, "Meditation Session", "A guided meditation session to promote relaxation and mental well-being.", "2023-11-11 11:00:00", "2023-11-11 12:00:00", 20, 10.00, "CSCC", "Bring a cushion if needed.", NULL, 4, 1),
    (12, "Leisure Hiking", "A leisurely hike through a scenic trail to enjoy nature.", "2023-11-12 08:00:00", "2023-11-12 11:00:00", 15, 15.00, "CCKCC", "Wear comfortable hiking shoes.", NULL, 5, 1),
    (13, "Bird Watching", "Join us for a bird watching session in the park.", "2023-11-13 07:30:00", "2023-11-13 09:00:00", 20, 10.00, "CCC", "Bring binoculars if you have them.", NULL, 6, 1);


INSERT INTO user_interest_group (user_id, group_id, status_id, date_joined)
VALUES
    (1, 1, 1, "2023-10-01"),
    (1, 2, 1, "2023-10-02"),
    (2, 1, 2, "2023-10-03"),
    (2, 2, 2, "2023-10-12"),
    (2, 3, 2, "2023-10-04"),
    (3, 1, 2, "2023-10-05");

COMMIT;
