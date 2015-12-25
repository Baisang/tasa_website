drop table if exists events;
create table events (
  id integer primary key autoincrement,
  title text not null,
  time text not null,
  location text not null,
  link text not null,
  image_url text not null,
  unix_time int not null
);

drop table if exists officers;
create table officers (
	id integer primary key autoincrement,
	name text not null,
	year integer not null,
	major text not null,
	quote text not null,
	description text not null,
	image_url text not null,
	position text not null,
	href text not null
);