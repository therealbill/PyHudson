What It Is
==========

A command line and library interface to Hudson's JSON/REST API to create
reports or run jobs. Sure, you can go to the web interface or maybe use curl,
but this one adds neat features such as "ru nall failed jobs" or run all jobs
for a specific view. 

What is Was
===========
A quick means to generate and track reportas and run results outside of Hudson
due to limitations of space and the way Hudson stores things. And so it can be
trended and tracked.


What It Shall Be
================
A more defined and feature-rich interface and library. I'd like to integrate
some interaction with Redis ad an option to PostgreSQL, create a Django app
that shows the result sin a pretty web interface, and write some hooks that can
be run in Hudson jobs to provide additional information.

It shall also be better documented. Not that it is seriously lacking except in
this readme. But it can be better. I would also like to validate it against
Jenkins.



