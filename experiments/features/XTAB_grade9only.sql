/*number of students with ONLY grade 9 records but outcome label*/
drop view if exists wake._g9only cascade;
create view wake._g9only as
select distinct wake._g9.student_id, cohort
from wake._g9
left join (select distinct student_id from wake._cohort_by_year where grade_level between 10 and 12) s
on wake._g9.student_id = s.student_id
where s.student_id is null;


drop table if exists wake._g9only_outcome;
create table wake._g9only_outcome as
select  distinct student_id, 
		cohort as inferred_cohort,
		grad_on_time,
		grad_not_on_time,
		dropout_ever,
		case when (outcome_label is null) then 1
			 else 0 end as outcome_not_observed
from wake._g9only 
left join (
	select  student_id as id,
			grad_early + grad_on_time as grad_on_time,
			grad_not_on_time,
			dropout_ever,
			outcome_label 
	from wake._label) s
on wake._g9only.student_id = s.id;


select  distinct inferred_cohort,
		count(*) over (partition by inferred_cohort) as students_with_only_grade_9_records,
		sum(grad_on_time) over (partition by inferred_cohort) as which_grad_on_time,
		sum(grad_not_on_time) over (partition by inferred_cohort) as which_grad_not_on_time,
		sum(dropout_ever) over (partition by inferred_cohort) as which_dropout_ever,
		sum(outcome_not_observed) over (partition by inferred_cohort) as outcome_not_observed
from wake._g9only_outcome
order by inferred_cohort desc;
