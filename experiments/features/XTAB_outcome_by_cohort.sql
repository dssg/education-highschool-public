/* outcome labels by cohort crosstab */
select  distinct cohort as cohort,
		sum(grad_early) over (partition by cohort) as grad_early,
		sum(grad_on_time) over (partition by cohort) as grad_on_time,
		sum(grad_late_1year) over (partition by cohort) as grad_late_1yr,
		sum(grad_late_2plusyears) over (partition by cohort) as grad_late_2plyrs,
		sum(dropout_hs) over (partition by cohort) as dropout_hs,
		sum(dropout_late) over (partition by cohort) as dropout_late,
		sum(no_record_found) over (partition by cohort) as no_record,
		total_students
from wake._label_12regular
left join (
	select cohort as ch, count(*) as total_students from wake._cohort
	where cohort is not null
	group by cohort) s
on cohort = ch
order by cohort desc;