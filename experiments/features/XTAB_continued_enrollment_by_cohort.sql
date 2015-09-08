drop view if exists wake._g9 cascade;
create view wake._g9 as
select distinct student_id, cohort from wake._cohort_by_year
where grade_level = 9;

drop view if exists wake._g10 cascade;
create view wake._g10 as
select distinct student_id, cohort from wake._cohort_by_year
where grade_level = 10;

drop view if exists wake._g11 cascade;
create view wake._g11 as
select distinct student_id, cohort from wake._cohort_by_year
where grade_level = 11;

drop view if exists wake._g12 cascade;
create view wake._g12 as
select distinct student_id, cohort from wake._cohort_by_year
where grade_level = 12;

/* enroll 9/10/11/12 only */
drop view if exists wake._enroll9_and_outcome;
create view wake._enroll9_and_outcome as
select 	wake._g9.cohort as cohort, 
		count(*) as students_enroll9_and_outcome
from wake._g9
inner join wake._label
on wake._g9.student_id = wake._label.student_id
where wake._label.outcome_label is not null
group by wake._g9.cohort
order by wake._g9.cohort desc;


drop view if exists wake._enroll10_and_outcome;
create view wake._enroll10_and_outcome as
select 	wake._g10.cohort as cohort, 
		count(*) as students_enroll10_and_outcome
from wake._g10 
inner join wake._label
on wake._g10.student_id = wake._label.student_id
where wake._label.outcome_label is not null
group by wake._g10.cohort
order by wake._g10.cohort desc;


drop view if exists wake._enroll11_and_outcome;
create view wake._enroll11_and_outcome as
select 	wake._g11.cohort as cohort, 
		count(*) as students_enroll11_and_outcome
from wake._g11
inner join wake._label
on wake._g11.student_id = wake._label.student_id
where wake._label.outcome_label is not null
group by wake._g11.cohort
order by wake._g11.cohort desc;


drop view if exists wake._enroll12_and_outcome;
create view wake._enroll12_and_outcome as
select 	wake._g12.cohort as cohort, 
		count(*) as students_enroll12_and_outcome
from wake._g12
inner join wake._label
on wake._g12.student_id = wake._label.student_id
where wake._label.outcome_label is not null
group by wake._g12.cohort
order by wake._g12.cohort desc;

/* enroll two consecutive years */
drop view if exists wake._enroll9to10_and_outcome;
create view wake._enroll9to10_and_outcome as
select 	wake._g9.cohort as cohort, 
		count(*) as students_enroll9to10_and_outcome
from wake._g9 
inner join wake._g10
on wake._g9.student_id = wake._g10.student_id
inner join wake._label
on wake._g9.student_id = wake._label.student_id
where wake._label.outcome_label is not null
group by wake._g9.cohort
order by wake._g9.cohort desc;



drop view if exists wake._enroll9to11_and_outcome;
create view wake._enroll9to11_and_outcome as
select 	wake._g9.cohort as cohort, 
		count(*) as students_enroll9to11_and_outcome
from wake._g9 
inner join wake._g10
on wake._g9.student_id = wake._g10.student_id
inner join wake._g11
on wake._g9.student_id = wake._g11.student_id
inner join wake._label
on wake._g9.student_id = wake._label.student_id
where wake._label.outcome_label is not null
group by wake._g9.cohort
order by wake._g9.cohort desc;



drop view if exists wake._enroll9to12_and_outcome;
create view wake._enroll9to12_and_outcome as
select 	wake._g9.cohort as cohort, 
		count(*) as students_enroll9to12_and_outcome
from wake._g9 
inner join wake._g10
on wake._g9.student_id = wake._g10.student_id
inner join wake._g11
on wake._g9.student_id = wake._g11.student_id
inner join wake._g12
on wake._g9.student_id = wake._g12.student_id
inner join wake._label
on wake._g9.student_id = wake._label.student_id
where wake._label.outcome_label is not null
group by wake._g9.cohort
order by wake._g9.cohort desc;


drop view if exists wake._enroll10to11_and_outcome;
create view wake._enroll10to11_and_outcome as
select 	wake._g10.cohort as cohort, 
		count(*) as students_enroll10to11_and_outcome
from wake._g10 
inner join wake._g11
on wake._g10.student_id = wake._g11.student_id
inner join wake._label
on wake._g10.student_id = wake._label.student_id
where wake._label.outcome_label is not null
group by wake._g10.cohort
order by wake._g10.cohort desc;


drop view if exists wake._enroll10to12_and_outcome;
create view wake._enroll10to12_and_outcome as
select 	wake._g10.cohort as cohort, 
		count(*) as students_enroll10to12_and_outcome
from wake._g10 
inner join wake._g11
on wake._g10.student_id = wake._g11.student_id
inner join wake._g12
on wake._g10.student_id = wake._g12.student_id
inner join wake._label
on wake._g10.student_id = wake._label.student_id
where wake._label.outcome_label is not null
group by wake._g10.cohort
order by wake._g10.cohort desc;



select  s.cohort as cohort_yr, 
		total_outcome,
		students_enroll9_and_outcome as enrol_9,
		students_enroll10_and_outcome as enrol_10,
		students_enroll11_and_outcome as enrol_11,
		students_enroll12_and_outcome as enrol_12,
		students_enroll9to10_and_outcome as enrol_9thru10,
		students_enroll9to11_and_outcome as enrol_9thru11,
		students_enroll9to12_and_outcome as enrol_9thru12,
		students_enroll10to11_and_outcome as enrol_10thru11,
		students_enroll10to12_and_outcome as enrol_10thru12
from (
select 	cohort, 
		count(*) as total_outcome
from wake._label
where outcome_label is not null
group by cohort) s
left join wake._enroll9_and_outcome
on s.cohort = wake._enroll9_and_outcome.cohort
left join wake._enroll10_and_outcome
on s.cohort = wake._enroll10_and_outcome.cohort
left join wake._enroll11_and_outcome
on s.cohort = wake._enroll11_and_outcome.cohort
left join wake._enroll12_and_outcome
on s.cohort = wake._enroll12_and_outcome.cohort
left join wake._enroll9to10_and_outcome
on s.cohort = wake._enroll9to10_and_outcome.cohort
left join wake._enroll9to11_and_outcome
on s.cohort = wake._enroll9to11_and_outcome.cohort
left join wake._enroll9to12_and_outcome
on s.cohort = wake._enroll9to12_and_outcome.cohort
left join wake._enroll10to11_and_outcome
on s.cohort = wake._enroll10to11_and_outcome.cohort
left join wake._enroll10to12_and_outcome
on s.cohort = wake._enroll10to12_and_outcome.cohort
order by cohort_yr desc;