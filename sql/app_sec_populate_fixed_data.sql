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
    
COMMIT;