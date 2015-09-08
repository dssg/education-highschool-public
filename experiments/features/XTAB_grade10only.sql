
/*number of students with grade 10 but not 11 or 12 records but outcome label*/
drop view if exists wake._g10only cascade;
create view wake._g10only as
select distinct wake._g10.student_id, cohort
from wake._g10
left join (select distinct student_id from wake._cohort_by_year where grade_level between 11 and 12) s
on wake._g10.student_id = s.student_id
where s.student_id is null;


drop table if exists wake._g10only_outcome;
create table wake._g10only_outcome as
select  distinct student_id, 
		cohort as inferred_cohort,
		grad_on_time,
		grad_not_on_time,
		dropout_ever,
		case when (outcome_label is null) then 1
			 else 0 end as outcome_not_observed
from wake._g10only 
left join (
	select  student_id as id,
			grad_early + grad_on_time as grad_on_time,
			grad_not_on_time,
			dropout_ever,
			outcome_label 
	from wake._label) s
on wake._g10only.student_id = s.id;

select  distinct inferred_cohort,
		count(*) over (partition by inferred_cohort) as students_in_grade_10_but_not_11to12,
		sum(grad_on_time) over (partition by inferred_cohort) as which_grad_on_time,
		sum(grad_not_on_time) over (partition by inferred_cohort) as which_grad_not_on_time,
		sum(dropout_ever) over (partition by inferred_cohort) as which_dropout_ever,
		sum(outcome_not_observed) over (partition by inferred_cohort) as outcome_not_observed
from wake._g10only_outcome
order by inferred_cohort desc;
