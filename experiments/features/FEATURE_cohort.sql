/* DEPRECATED
drop table wake._cohort

create table wake._cohort as

with entrance as (
   select   cast(current_grade as int), 
   			academic_year,student_id,
   			row_number() over w as rn,count(*) over w as ct
   from wake.school_enrollment 
   where current_grade in ('9', '09', '10', '11', '12') and active_status = True
   window w as (partition by student_id order by academic_year asc range between unbounded preceding and unbounded following)
), filtered_entrance as (
select * from entrance where rn=1)

select s.id, fe.academic_year+13-cast(fe.current_grade as int) as cohort
   from wake.student s
       left outer join filtered_entrance fe on s.id=fe.student_id
*/



drop table if exists wake._cohort_temp;
create table wake._cohort_temp as
select  student_id as sid,
		academic_year,
		case when (grade_level is not null) then grade_level
		else cast(current_grade_level as int) end as grade,
		active_status,
		current_status
from wake.school_enrollment
where (current_grade_level in ('9', '09', '10', '11', '12') or grade_level between 9 and 12);

drop table if exists wake._cohort_temp2;
create table wake._cohort_temp2 as
select  sid,
		academic_year as first_academic_year,
		grade as first_grade
from (
select  sid,
		academic_year,
		grade,
		active_status,
		current_status,
        row_number() over (partition by sid order by academic_year asc nulls last) as rn
from wake._cohort_temp
where active_status = true) s
where s.rn = 1;

drop table if exists wake._cohort_transferout_temp;
create table wake._cohort_transferout_temp as
select * from
wake._cohort_temp2 left join (
select sid as ssid,
	   academic_year as yr,
	   grade as gr,
	   current_status as st
from wake._cohort_temp) s
on wake._cohort_temp2.sid = s.ssid
where yr >= first_academic_year and gr >= first_grade and st = '2';

drop table if exists wake._cohort cascade;
create table wake._cohort as
select  sid as student_id,
		first_academic_year - first_grade + 13 as cohort
from wake._cohort_temp2
where sid not in (select sid from wake._cohort_transferout_temp);


drop table if exists wake._cohort_temp;
drop table if exists wake._cohort_temp2;
drop table if exists wake._cohort_transferout_temp;

