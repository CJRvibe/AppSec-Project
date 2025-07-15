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
    
INSERT INTO users (first_name, last_name, email, password, user_role)
VALUES
    ("Jian Hao", "Boo", "boojianhao@gmail.com", "scrypt:32768:8:1$OdjtJNaE4MmMEhUi$aeba4e9565b897dd40b45ad91fe5e10ae253a324d79d4ec891d29ad54aa690c6ac989b953e9a6c303cf526cbc748b9f537d07a84a3cc335fd3d450df99920674", 1),
    ("Tom", "Tan", "tomtan@gmail.com", "scrypt:32768:8:1$nDxwfSmPjmWDJ3dV$ca54472e55e47f0bd573971c205331e20bb3d1fba892ee365ba2e5aa533ad8f35dbc127aee92b5a635efe73e19c63e16dffcbaf8d6cea2ae422feb45ed1a7008", 2),
    ("admin", "admin", "admin@gmail.com", "scrypt:32768:8:1$NpJdo0T9CYT9txvD$85a4f4c1b0b1e0599520eba9db3dbcb1b70af0c3b51e2f762856e4ee4e433c0d194ae00f2bd331500cb77d5a65dd14219b27111813cc51a2a0db1291a4d712d1", 3);
    
COMMIT;