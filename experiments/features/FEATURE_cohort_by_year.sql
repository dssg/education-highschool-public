
/* _cohort_by_year: unique pairs of (student_id, academic_year) in which they're actively enrolled */
/* requires _cohort table */

drop table if exists wake._cohort_by_year;
create table wake._cohort_by_year as 
select  student_id, 
		cohort, 
		academic_year, 
		case when (grade_level is not null) then grade_level
		else cast(current_grade_level as int) end as grade_level 
from wake.school_enrollment 
inner join (
	select  student_id as id, 
			cohort 
	from wake._cohort 
	where cohort is not null) t
on wake.school_enrollment.student_id=t.id
where  (current_grade_level in ('1', '2', '3', '4', '5', '6', '7', '8', '9', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12') 
		or grade_level between 1 and 12)
	   and active_status = true;

