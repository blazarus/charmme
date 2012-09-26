drop table if exists users;
create table users (
	username varchar primary key,
	info text,
	update_time timestamp,
	linkedin_id
);

drop table if exists recommendations;
create table recommendations (
	yourself varchar references users(username),
	recommendation integer references users(username),
	has_met boolean,
	update_time timestamp,
	UNIQUE (yourself, recommendation)
);

drop table if exists sponsor_recs;
create table sponsor_recs (
	yourself varchar references users(username),
	sponsor_rec integer references users(username),
	has_met boolean,
	update_time timestamp,
	UNIQUE (yourself, sponsor_rec)
);
