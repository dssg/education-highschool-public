select  academic_year, 
		active_grade_12_students,
		inferred_cohort_size
from (
	select  academic_year,
			count(distinct student_id) as active_grade_12_students
	from wake.school_enrollment
	where (current_grade_level = '12' or grade_level = 12) and active_status = true
	group by academic_year
	) t
left join (
	select  cohort, 
			count(*) as inferred_cohort_size
	from wake._cohort
	group by cohort
	) s
on t.academic_year + 1 = s.cohort
order by academic_year desc;