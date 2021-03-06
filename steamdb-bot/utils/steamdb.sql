CREATE TABLE IF NOT EXISTS `cache` ( `id` TEXT NOT NULL UNIQUE, `data` BLOB, `date` FLOAT, PRIMARY KEY(`id`) );
CREATE TABLE IF NOT EXISTS `log` ( `user_id` NUMERIC NOT NULL, `username` TEXT, `first_name` TEXT, `last_name` TEXT, `language_code` TEXT, `text` TEXT, `chat_id` NUMERIC, `chat_type` TEXT, `message_id` NUMERIC, `date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP );
CREATE TABLE IF NOT EXISTS `steam` ( `steam_id` NUMERIC NOT NULL UNIQUE, `query` TEXT, `added` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, `hits` INTEGER NOT NULL DEFAULT 1, PRIMARY KEY(`steam_id`) );
