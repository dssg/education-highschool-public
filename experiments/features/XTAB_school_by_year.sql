
select distinct school_name, academic_year,
	   count(*) over (partition by school_name, academic_year) as num_total,
	   sum(case when active_status is true then 1 else 0 end) over (partition by school_name, academic_year) as num_active,
	   sum(case when last_grade is null then 1 else 0 end) over (partition by school_name, academic_year) as last_grade_missing,
	   sum(case when next_grade is null then 1 else 0 end) over (partition by school_name, academic_year) as next_grade_missing,
	   sum(case when current_grade=last_grade then 1 else 0 end) over (partition by school_name, academic_year) as currentgrade_sameas_lastgrade,
	   sum(case when current_grade!=last_grade then 1 else 0 end) over (partition by school_name, academic_year) as currentgrade_diff_from_lastgrade,
       sum(case when current_grade=next_grade then 1 else 0 end) over (partition by school_name, academic_year) as currentgrade_sameas_nextgrade,
       sum(case when current_year_round_track is not null then 1 else 0 end) over (partition by school_name, academic_year)  as round_track_flag
from
(select student_id,
		name as school_name,
		academic_year, 
		active_status,
		cast(last_grade_level as int) as last_grade,
		case when (grade_level is not null) then grade_level
			 else cast(current_grade_level as int) end as current_grade,
		cast(next_grade as int) as next_grade,
		current_year_round_track
from
wake.school_enrollment left join
wake.school on wake.school_enrollment.current_school_id = wake.school.id
where  	(name like '%HS%') and 
		(last_grade_level in ('08', '09', '10', '11', '12') or last_grade_level is null) and
		(current_grade_level in ('9', '09', '10', '11', '12') or grade_level between 9 and 12) and
		(next_grade in ('9', '09', '10', '11', '12') or next_grade is null)
) t
order by school_name, academic_year
		