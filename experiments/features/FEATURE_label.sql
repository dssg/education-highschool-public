/* _grad_label: requires _cohort, same size as _cohort, contains info regarding grade-12 regular graduation */ 
drop view if exists wake._grad_label;
create view wake._grad_label as
select distinct student_id, cohort, academic_year as academic_year, classification from
(select * from wake._cohort where cohort is not null) s
left join (
select student_id as id, academic_year, classification from wake.graduates
where classification in ('12 Grade Regular Program Graduate', '12th Grade Regular Program', '1')
) t
on s.student_id = t.id;


/* _label: requires _grad_label and outcome, outcome labels for students (either grade 12 regular graduates, ever dropout or no record can be found ) */
drop table if exists wake._label;
create table wake._label as
select student_id,
	   cohort, 
	   case when (academic_year + 1 - cohort < 0) then 1
	   		else 0 end as grad_early,
	   case when (academic_year + 1 - cohort = 0) then 1
	   		else 0 end as grad_on_time,
	   case when (academic_year + 1 - cohort = 1) then 1
	  		else 0 end as grad_late_1year,
	   case when (academic_year + 1 - cohort > 1) then 1
	   		else 0 end as grad_late_2plusyears,
	   case when (academic_year + 1 - cohort >= 1) then 1
	   		else 0 end as grad_not_on_time,	
	   case when (id is not null and extract (year from (withdraw_date + interval '184 days')) <= cohort) then 1
	   		else 0 end as dropout_hs,
 	   case when (id is not null and extract (year from (withdraw_date + interval '184 days')) > cohort) then 1
	   		else 0 end as dropout_late,
	   case when (id is not null) then 1
	   		else 0 end as dropout_ever,
	   case when (academic_year is null and withdraw_date is null) then 1
	   		else 0 end as no_record_found,
	   case when (id is not null) then 1
	   		when (academic_year + 1 - cohort <= 0) then 0
	   		else null end as outcome_label
from (select * from wake._grad_label) s
left join (
select student_id as id,
	   withdraw_date from wake.outcome
) t
on s.student_id = t.id;
drop view if exists wake._grad_label;

