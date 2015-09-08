/*
Working file to work out cohort alignment and missing outcomes labels for WCPSS
This is Siobhan's working document.  As the cohort and outcome assignment gets changed a lot of this
will be useless.  Will move items of interest to features generation when data is clean.
*/

/* Looking at the enrollment and outcomes info to figure out what is going on with our missing students*/

select *
from wake.school_enrollment
where current_school_id = 998
order by student_id, academic_year asc;
*/

select distinct current_school_number_locator
from wake.school_enrollment;

select distinct current_school_id
from wake.school_enrollment
where current_school_number_locator = 'GRD' or current_school_number_locator = 'OUT';

select current_school_id, current_grade_level, active_status, academic_year, withdraw_code
from wake.school_enrollment
where (current_school_id = 998 or current_school_id = 997) and active_status = 'true'
order by student_id, academic_year asc;
*/

select distinct student_id
from wake._cohort
where cohort is null;

/*looking at years in school by cohort, academic year, grade level*/
select cohort, count(cohort), 
        academic_year, 
        grade_level, 
        current_grade_level, 
        (academic_year - cohort + 5) as years_spent_inhs
from (select * 
from school_enrollment 
left join wake._cohort
on school_enrollment.student_id = wake._cohort.student_id) t
where (current_school_id != 998 and current_school_id != 997) and active_status = 'true' and grade_level in ('9', '09', '10', '11', '12', '13')
group by cohort, academic_year, grade_level, current_grade_level, years_spent_inhs
order by cohort desc, academic_year asc, grade_level asc, years_spent_inhs asc;


/* looking at the cohort grade level by academic year -- "current_grade_level" should not be used */
select cohort, count(cohort), academic_year, grade_level, current_grade_level
from (select * 
from school_enrollment 
left join wake._cohort
on school_enrollment.student_id = wake._cohort.student_id) t
where (current_school_id != 998 and current_school_id != 997) and active_status = 'true' and grade_level in ('9', '09', '10', '11', '12', '13')
group by cohort, academic_year, grade_level, current_grade_level
order by cohort desc, academic_year asc, grade_level asc;

/* current_status label */
SELECT current_status, count(current_status)
FROM wake.school_enrollment
group by current_status;

SELECT count(current_status)
FROM wake.school_enrollment
where current_status like '%W%';

SELECT count(student_id)
FROM wake.school_enrollment
where current_status like '%0%' and current_status like '%2%';

SELECT count(distinct student_id)
FROM wake.school_enrollment
where current_status like '%2%';

SELECT count(distinct student_id)
FROM wake.school_enrollment
where current_status like '%0%';

/* has an out code from school enrollment */
select distinct has_out_code 
from wake.school_enrollment
group by has_out_code;

select count(has_out_code)
from wake.school_enrollment
group by has_out_code;

select count(has_out_code) from
(select has_out_code 
from wake.school_enrollment
group by has_out_code
) t;

/* has a withdraw code */
select distinct withdraw_code
from wake.school_enrollment;

select count(withdraw_code)
from wake.school_enrollment
group by withdraw_code;

/* looking at the _st enrollment table and what is there */
select hs_years_in_district, number_of_schools, number_of_enrollments, count (distinct student_id)
from wake._st_enrollment
group by hs_years_in_district, number_of_enrollments, number_of_schools
order by hs_years_in_district asc, number_of_schools asc;

/*high schools*/
select id, name
from wake.school
where name like '%HS%';

/* diagnosing enrollment weirdness  _st enrollment table */
select academic_year, 
      hs_years_in_district, 
      number_of_schools, 
      number_of_enrollments, 
      count (distinct student_id)
from
      (select 
            school_enrollment.student_id, 
            school_enrollment.academic_year, 
            _st_enrollment.hs_years_in_district, 
            _st_enrollment.number_of_schools, 
            _st_enrollment.number_of_enrollments
      from wake.school_enrollment
left join wake._st_enrollment
on school_enrollment.student_id = _st_enrollment.student_id) t
group by t.academic_year, t.hs_years_in_district, t.number_of_enrollments, t.number_of_schools
order by t.academic_year, t.hs_years_in_district asc, t.number_of_schools asc;

select t.academic_year, 
      t.name, 
      t.number_of_enrollments, 
      count (distinct student_id)
from 
      (select school_enrollment.student_id, 
              school_enrollment.academic_year, 
              school_enrollment.current_school_id, 
              _st_enrollment.hs_years_in_district, 
              _st_enrollment.number_of_schools, 
              _st_enrollment.number_of_enrollments
              from wake.school_enrollment
              left join wake._st_enrollment
              on school_enrollment.student_id = _st_enrollment.student_id) s
left join s 
on s.current_school_id = school.id) t
where name like '%HS%'
group by t.academic_year, t.name, t.number_of_enrollments, 
order by t.academic_year asc;

select school.id, school.name, school_enrollment.academic_year
from wake.school
left join wake.school_enrollment
on school_enrollment.current_school_id = school.id
where name like '%HS%'
group by id, academic_year, name
order by id asc, academic_year asc;

/* student movement */
select academic_year, current_grade,  next_grade, count(*)
from wake.school_enrollment
where current_grade = next_grade
group by academic_year, current_grade, next_grade;

select academic_year, count(*) 
from wake.school_enrollment
where current_grade < next_grade
group by academic_year;

select distinct current_grade
from wake.school_enrollment;

/*years of course enrollment*/
select DISTINCT(academic_year) from wake.course_enrollment order by academic_year asc;

/*years of academic enrollment enrollment*/
select academic_year, count(active_status)
from wake.school_enrollment
where active_status = true
group by academic_year, active_status
order by academic_year asc;

/*reason for end of year withdrawal from outcomes table */
select reason_code, count(student_id)
from wake.outcome
group by grade_level, reason_code_description, reason_code
order by grade_level asc;


/*apparently grade level and withdrawal reason description are missing from outcomes table */
select distinct grade_level
from wake.outcome;

/*feature table generation outcomes */
/* _label_12regular: requires _grad_label_12regular and outcome, outcome labels for students (either grade 12 regular graduates, ever dropout or no record can be found ) */
drop table if exists wake._label_12regular;
create table wake._label_12regular as
select student_id,
       cohort, 
       case when (academic_year + 1 - cohort <= 0) then 1
       else 0 end as on_time_grad,
       case when (academic_year + 1 - cohort = 1) then 1
       else 0 end as late_grad_1year,
       case when (academic_year + 1 - cohort > 1) then 1
       else 0 end as late_grad_2ormoreyears,
       case when (id is not null) then 1
       else 0 end as ever_dropout,
       case when (academic_year is null and withdraw_date is null) then 1
       else 0 end as no_record_found
from (select * from wake._grad_label_12regular) s
left join (
select student_id as id,
       withdraw_date from wake.outcome
) t
on s.student_id = t.id;

/* table of cohorts and outcomes */
select  distinct cohort - 1 as cohort,
		sum() over (partition by cohort) as grad_early,
        sum(on_time_grad) over (partition by cohort) as grad_on_time,
        sum(late_grad_1year) over (partition by cohort) as grad_late_1yr,
        sum(late_grad_2ormoreyears) over (partition by cohort) as grad_late_2ormoreyrs,
        sum(ever_dropout) over (partition by cohort) as ever_dropout,
        sum(no_record_found) over (partition by cohort) as no_record,
        total_students
from wake._label_12regular
left join (select cohort as ch, "count" as total_students from wake._cohort_count) s
on cohort - 1 = ch
order by cohort desc;

/*, current_status, current_grade, next_school_id, next_grade, next_school_id,grade_level, withdraw_code, academic_year*/

/*SELECT distinct classification, grade, diploma_certificate
FROM wake.graduates
WHERE upper(graduates.classification) like '%GRADUAT%'
*/

/*total number of unique students in graduation table 
select count(*) from 
(select distinct student_id from wake.graduates) t

*/

/*total number of unique students that could have graduated*/
/*
select count(*) from
(select * from wake._cohort
where cohort is not null and cohort < 2016 and cohort > 2005) t

*/

select academic_year, 
        name, 
        count (distinct student_id) as number_of_enrollments, 
        count (active_status) as active_status,
        count (current_grade_level=last_grade_level) as currentgrade_sameas_lastgrade,
        count (current_grade_level!=last_grade_level) as currentgrade_diff_from_lastgrade,
        count (current_grade_level=next_grade) as currentgrade_sameas_nextgrade,
        count (current_year_round_track) as round_track_flag
from 
    (select *
    from wake.school
    left join wake.school_enrollment
    on school_enrollment.current_school_id = school.id
    where name like '%HS%') s
group by academic_year, name
order by name, academic_year;

select  student_id as sid,
        academic_year,
        case when (grade_level is not null) then grade_level
        else cast(current_grade_level as int) end as grade,
        active_status,
        current_status
from wake.school_enrollment
where (current_grade_level in ('9', '09', '10', '11', '12') or grade_level between 9 and 12);

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
where      (name like '%HS%') and 
        (last_grade_level in ('08', '09', '10', '11', '12') or last_grade_level is null) and
        (current_grade_level in ('9', '09', '10', '11', '12') or grade_level between 9 and 12) and
        (next_grade in ('9', '09', '10', '11', '12') or next_grade is null)
) t
order by school_name, academic_year

select  student_id,
        name as school_name,
        academic_year, 
        active_status,
        cast(last_grade_level as int) as last_grade,
        case when (grade_level is not null) then grade_level
             else cast(current_grade_level as int) end as current_grade,
        cast(next_grade as int) as next_grade
from
wake.school_enrollment left join
wake.school on wake.school_enrollment.current_school_id = wake.school.id
where  (name like '%HS%') and 
        (last_grade_level in ('08', '09', '10', '11', '12') or last_grade_level is null) and
        (current_grade_level in ('9', '09', '10', '11', '12') or grade_level between 9 and 12) and
        (next_grade in ('9', '09', '10', '11', '12') or next_grade is null)  


select *
from wake.student
where id = 35 or id = 12
order by id;

select  student_id,
       name as school_name,
       academic_year, 
       active_status,
       cast(last_grade_level as int) as last_grade,
       case when (grade_level is not null) then grade_level
            else cast(current_grade_level as int) end as current_grade,
       cast(next_grade as int) as next_grade
from
wake.school_enrollment left join
wake.school on wake.school_enrollment.current_school_id = wake.school.id
where  student_id = 35 or student_id = 12
order by student_id, academic_year asc, school_name;

select *
from wake.course_enrollment
where student_id = 35 or student_id = 12
order by student_id, academic_year asc;
*/