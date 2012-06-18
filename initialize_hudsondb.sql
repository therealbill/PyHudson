CREATE TABLE hudson_jobs (
	jobid	serial ,
	jobname	varchar(128) primary key,
	description	text
);

CREATE TABLE hudson_views (
	viewid		serial ,
	viewname	varchar(128) primary key,
	description	text
);

CREATE TABLE jobresults(
	jobname		varchar references hudson_jobs,
	viewname	varchar references hudson_views,
	started		timestamp,
	ended		timestamp,
	result		varchar(24)
);

CREATE TABLE result_daily (
	jobsrun	int,
	jobs_success	int,
	jobs_failure	int,
	jobs_aborted	int,
	jobs_queued	int,
	datestamp	date
	
);

CREATE TABLE result_weekly (
	jobsrun	int,
	jobs_success	int,
	jobs_failure	int,
	jobs_aborted	int,
	jobs_queued	int,
	datestamp	date
);

CREATE TABLE result_monthly (
	jobsrun	int,
	jobs_success	int,
	jobs_failure	int,
	jobs_aborted	int,
	jobs_queued	int,
	datestamp	date
);

CREATE TABLE result_quarterly (
	jobsrun	int,
	jobs_success	int,
	jobs_failure	int,
	jobs_aborted	int,
	jobs_queued	int,
	datestamp	date
);

CREATE TABLE result_annually (
	jobsrun	int,
	jobs_success	int,
	jobs_failure	int,
	jobs_aborted	int,
	jobs_queued	int,
	datestamp	date
);
