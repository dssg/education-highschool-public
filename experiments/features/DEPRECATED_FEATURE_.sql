/* DEPRECATED */
/* VIEW wake_cohort: list of unique student ids with their first grade-9 enrollment year*/
drop view if exists wake_cohort;
CREATE VIEW wake_cohort as (
select t.student_id, t.academic_year as first_enroll_grade_9 from
(select school_enrollment.*, row_number() over (partition by student_id order by academic_year asc nulls last
                              ) as seqnum 
       from school_enrollment
       where grade_level=9
       ) t
       where seqnum = 1);


/* grade distribution */
select first_enroll_grade_9, count(*) 
from wake_cohort
group by first_enroll_grade_9
order by first_enroll_grade_9 desc


/* TABLE act_lookup: code names for ACT tests */
drop table if exists act_lookup;
create table act_lookup (
	code VARCHAR(4),
	name VARCHAR(20)
);
insert into act_lookup values ('ACEN', 'English');
insert into act_lookup values ('ACMA', 'Mathematics');
insert into act_lookup values ('ACRD', 'Reading');
insert into act_lookup values ('ACSC', 'Science');
insert into act_lookup values ('ACCO', 'Composite');
insert into act_lookup values ('ACWR', 'Writing')



/* VIEW wake_act: ACT scores */
drop view if exists wake_act;
create view wake_act as
(select * from (select * from test
where test_id like 'AC%') t
left join act_lookup 
on (t.test_id=act_lookup.code)
)

/* VIEW wake_act_composite: ACT scores */
create view wake_act_composite as
(select * from wake_act 
where name='Composite')



drop table if exists _for_model1;
create table _for_model1 as
select * from wake.wake_cohort 
	left join (
		select 
			wake_act_composite.student_id as act_id, 
			wake_act_composite.academic_year as act_year, 
			wake_act_composite.name as act_subject, 
			wake_act_composite.score as act_score 
		from 
			wake.wake_act_composite) t 
	on 
		wake.wake_cohort.student_id=t.act_id
    left join (
		SELECT 
			student.id,
            student.gender,
            student.race,
            student.home_language_code,
            student.date_of_birth,
            (student.date_first_entered_wcpss - student.date_of_birth) as age_in_days_first_entered_wcpss,
            (student.date_entered_into_us - student.date_of_birth) as age_in_days_entered_into_us,
            outcome.withdraw_code
        FROM wake.student
        LEFT JOIN wake.outcome ON (wake.outcome.student_id=wake.student.id)
        ) s
     on wake.wake_cohort.student_id=s.id



drop table if exists _for_model1;
create table _for_model1 as
select * from wake.wake_cohort 
	left join (
		select 
			wake_act_composite.student_id as act_id, 
			wake_act_composite.academic_year as act_year, 
			wake_act_composite.name as act_subject, 
			wake_act_composite.score as act_score 
		from 
			wake.wake_act_composite) t 
	on 
		wake.wake_cohort.student_id=t.act_id
    left join (
		SELECT 
			student.id,
            student.gender,
            student.race,
            student.home_language_code,
            student.date_of_birth,
            (student.date_first_entered_wcpss - student.date_of_birth) as age_in_days_first_entered_wcpss,
            (student.date_entered_into_us - student.date_of_birth) as age_in_days_entered_into_us,
            outcome.withdraw_code
        FROM wake.student
        LEFT JOIN wake.outcome ON (wake.outcome.student_id=wake.student.id)
        ) s
     on wake.wake_cohort.student_id=s.id
 */

/* relative age to cohort */
select * from _for_model1 left join
(select student_id as sid, extract(epoch from (to_date(to_char(first_enroll_grade_9, '9999'), 'yyyy') + interval '14 months') -
		(date_of_birth + interval '16 years'))/(60*60*24*365) as rel_age_to_cohort
from _for_model1) t
on t.sid = _for_model1.student_id;

/* unexcused absences in grade 9 and 10 */
drop table if exists _for_model3;
create table _for_model3 as
(select * from _for_model2 
left join
(select _for_model1.student_id as said9, school_attendance.unexcused_absence as unexcused_absence_grade_9 from _for_model1 left join school_attendance
		on (_for_model1.student_id = school_attendance.student_id AND _for_model1.first_enroll_grade_9 = school_attendance.academic_year)) sa9
on sa9.said9 = _for_model2.student_id
left join
(select _for_model1.student_id as said10, school_attendance.unexcused_absence as unexcused_absence_grade_10 from _for_model1 left join school_attendance
		on (_for_model1.student_id = school_attendance.student_id AND _for_model1.first_enroll_grade_9+1 = school_attendance.academic_year)) sa10
on sa10.said10 = _for_model2.student_id
)

/* _cohort_by_year: unique pairs of (student_id, academic_year) in which they're actively enrolled */
create table _cohort_by_year as 
select student_id, cohort, academic_year, grade_level from 
school_enrollment inner join (select id, cohort from _cohort where cohort is not null) t
on school_enrollment.student_id=t.id
where grade_level is not null and active_status = true;

/* _cohort_by_year_feature: start populating with time-dependent features */
drop table if exists _cohort_by_year_feature;
create table _cohort_by_year_feature as
select student_id, 
	   cohort,
	   academic_year, 
	   grade_level,
	   case when (academic_year >= 2004 and days_absent is not null) then days_absent
	   		when (academic_year >= 2004 and days_absent is null) then 0
	   		else null end as days_absent,
	   case when (academic_year >= 2004 and excused_absence is not null) then excused_absence
	   		when (academic_year >= 2004 and excused_absence is null) then 0
	   		else null end as excused_absence,
	   case when (academic_year >= 2004 and unexcused_absence is not null) then unexcused_absence
	   		when (academic_year >= 2004 and unexcused_absence is null) then 0
	   		else null end as unexcused_absence,
	   case when (academic_year between 2007 and 2013 and suspension_count is not null) then suspension_count
	   		when (academic_year between 2007 and 2013 and suspension_count is null) then 0
	   		else null end as suspension_count,
	   case when (academic_year between 2007 and 2013 and total_suspension_days is not null) then total_suspension_days
	   		when (academic_year between 2007 and 2013 and total_suspension_days is null) then 0
	   		else null end as total_suspension_days,
	   case when (academic_year between 2007 and 2013 and min_suspension_days is not null) then min_suspension_days
	   		when (academic_year between 2007 and 2013 and min_suspension_days is null) then 0
	   		else null end as min_suspension_days,
	   case when (academic_year between 2007 and 2013 and max_suspension_days is not null) then max_suspension_days
	   		when (academic_year between 2007 and 2013 and max_suspension_days is null) then 0
	   		else null end as max_suspension_days
from  _cohort_by_year 
left join (
select student_id as id, academic_year as yr, days_absent, excused_absence, unexcused_absence 
from school_attendance) t
on (_cohort_by_year.student_id=t.id and _cohort_by_year.academic_year=t.yr)
left join (
select student_id as id, 
	   date_part('year', date_trunc('year', incident_date - interval '9 months')) as yr,
	   count(*) as suspension_count,
	   sum(suspension_length) as total_suspension_days,
	   min(suspension_length) as min_suspension_days,
	   max(suspension_length) as max_suspension_days
from discipline_temp
group by id, yr) s
on (_cohort_by_year.student_id=s.id and _cohort_by_year.academic_year=s.yr);



/* update _cohort_by_year_feature: adding school info */
create table _cohort_by_year_feature_temp as
select *
from _cohort_by_year_feature left join (
	select student_id as id,
		   academic_year as yr,
		   current_school_id
	from school_enrollment) s
	on (_cohort_by_year_feature.student_id=s.id and _cohort_by_year_feature.academic_year=s.yr);
alter table _cohort_by_year_feature_temp drop column id;
alter table _cohort_by_year_feature_temp drop column yr;
drop table if exists _cohort_by_year_feature;
alter table _cohort_by_year_feature_temp rename to _cohort_by_year_feature;


/* update _cohort_by_year_feature: keep adding school info from school table */
create table _cohort_by_year_feature_temp as		
select * from _cohort_by_year_feature left join (
     select id AS school_id,
            area AS school_area,
			grade_span AS school_grade_span,
			case when (grade_span like '%E%') then 1
				 else 0 end as school_is_elementary,
			case when (grade_span like '%M%') then 1
				 else 0 end as school_is_middle,
			case when (grade_span like '%H%') then 1
				 else 0 end as school_is_high,
			performance_composite_2013_14 AS school_performance_composite_2013_14,
			performance_composite_2012_13 AS school_performance_composite_2012_13,
			reading_proficient_2013_14 AS school_reading_proficient_2013_14,
			math_proficient_2013_14 AS school_math_proficient_2013_14,
			science_proficient_2013_14 AS school_science_proficient_2013_14,
			evaas_growth_status_2013_14 AS school_evaas_growth_status_2013_14,
			math_course_rigor_in_hs AS school_math_course_rigor_in_hs,
			four_year_graduation_rate_2013_14 AS school_four_year_graduation_rate_2013_14,
			four_year_graduation_rate_change AS school_four_year_graduation_rate_change,
			five_year_graduation_rate_2013_14 AS school_five_year_graduation_rate_2013_14,
			dropout_rate_2011_12 AS school_dropout_rate_2011_12,
			dropout_rate_2012_13 AS school_dropout_rate_2012_13,
			of_juniors_scoring_17_or_above AS school_of_juniors_scoring_17_or_above,
			high_risk_students_tier_3_or_above AS school_high_risk_students_tier_3_or_above,
			kia_average_rote_count AS school_kia_average_rote_count,
			kia_of_students_who_had_at_least AS school_kia_of_students_who_had_at_least,
			kia_parents_read_to_child_daily AS school_kia_parents_read_to_child_daily,
			of_hs_students_enrolled_in_at AS school_of_hs_students_enrolled_in_at,
			cte_work_keys_reaching_standard AS school_cte_work_keys_reaching_standard,
			act_average_composite_score_junior AS school_act_average_composite_score_junior,
			act_juniors_reaching_benchmark AS school_act_juniors_reaching_benchmark,
			th_day_membership AS school_th_day_membership,
			frl_students AS school_frl_students,
			lep_students AS school_lep_students,
			magnet_students AS school_magnet_students,
			of_special_ed_pre_k_students AS school_of_special_ed_pre_k_students,
			total_pre_k_students AS school_total_pre_k_students,
			special_education_students AS school_special_education_students,
			of_resource_students AS school_of_resource_students,
			of_separate_students AS school_of_separate_students,
			of_speech_identified_students AS school_of_speech_identified_students,
			stability AS school_stability,
			turbulence AS school_turbulence,
			average_daily_membership AS school_average_daily_membership,
			actual_school_campus_capacity AS school_actual_school_campus_capacity,
			crowding AS school_crowding,
			of_mobile_classrooms AS school_of_mobile_classrooms,
			of_students_rating_school_excellent AS school_of_students_rating_school_excellent,
			of_students_who_like_school AS school_of_students_who_like_school,
			of_students_who_feel_safe_at_school AS school_of_students_who_feel_safe_at_school,
			twc_the_faculty_has_an_effective AS school_twc_the_faculty_has_an_effective,
			twc_there_is_an_atmosphere_of_tr AS school_twc_there_is_an_atmosphere_of_tr,
			twc_overall_my_school_is_a_good AS school_twc_overall_my_school_is_a_good,
			of_students_term_suspensions AS school_of_students_term_suspensions,
			of_students_suspended_short_term AS school_of_students_suspended_short_term,
			of_long_term_suspensions AS school_of_long_term_suspensions,
			of_students_suspended_long_term AS school_of_students_suspended_long_term,
			ci_position_allotment AS school_ci_position_allotment,
			academially_gifted_moe AS school_academially_gifted_moe,
			magnet_moe AS school_magnet_moe,
			magnet_coordinators AS school_magnet_coordinators,
			title_i_regular_teachers_moe AS school_title_i_regular_teachers_moe,
			title_i_pre_k_teachers_moe AS school_title_i_pre_k_teachers_moe,
			all_title_i_teachers_assitant_moe AS school_all_title_i_teachers_assitant_moe,
			technology_facilitator AS school_technology_facilitator,
			title_i_math_coach_moe AS school_title_i_math_coach_moe,
			title_i_literacy_coach_moe AS school_title_i_literacy_coach_moe,
			esl_moe AS school_esl_moe,
			literacy_moe AS school_literacy_moe,
			intervention_moe AS school_intervention_moe,
			special_ed_teacher_moe AS school_special_ed_teacher_moe,
			special_ed_ta_moe AS school_special_ed_ta_moe,
			special_ed_pre_k_teacher_moe AS school_special_ed_pre_k_teacher_moe,
			special_ed_pre_k_ta_moe AS school_special_ed_pre_k_ta_moe,
			total_teachers AS school_total_teachers,
			of_certified_teachers AS school_of_certified_teachers,
			of_bts_formerly_ilt AS school_of_bts_formerly_ilt,
			beg_teachers AS school_beg_teachers,
			staff_turnover AS school_staff_turnover,
			teachers_white AS school_teachers_white,
			teachers_black AS school_teachers_black,
			teachers_hispanic AS school_teachers_hispanic,
			teachers_asian AS school_teachers_asian,
			teachers_other AS school_teachers_other,
			of_teachers_non_white AS school_of_teachers_non_white,
			teachers_25_years_or_more AS school_teachers_25_years_or_more,
			teachers_national_board AS school_teachers_national_board,
			teachers_higher_than_4_year_degree AS school_teachers_higher_than_4_year_degree,
			teachers_w_higher_than_4_year_degree AS school_teachers_w_higher_than_4_year_degree,
			magnet AS school_magnet,
			case when (magnet is not null) then true
				 else false end AS school_is_magnet,
			case when (magnet like '%IB%') then true
				 else false end AS school_magnet_is_ib,
			case when (magnet like '%GT%') then true
				 else false end AS school_magnet_is_gifted,
			calendar AS school_calendar,
			case when (pbis is not null) then true
				 else false end AS school_pbis,
			case when (stem is not null) then true
				 else false end AS school_stem,
			case when (global is not null) then true
				 else false end AS school_global,
			case when (ib is not null) then true
				 else false end AS school_ib,
			case when (cis is not null) then true
				 else false end AS school_cis,
			case when (success_maker is not null) then true
				 else false end AS school_success_maker,
			case when (academy_of_reading is not null) then true
				 else false end AS school_academy_of_reading,
			case when (academy_of_math is not null) then true
				 else false end AS school_academy_of_math
   	 from school) s
	on (_cohort_by_year_feature.current_school_id=s.school_id);
alter table _cohort_by_year_feature_temp drop column school_id;
drop table if exists _cohort_by_year_feature;
alter table _cohort_by_year_feature_temp rename to _cohort_by_year_feature;

          

/*       */
/*       */
/*       */
/*       */
/*       */
/*       */
/* _cohort_feature: start populating with static features */

drop table if exists _cohort_feature;
create table _cohort_feature as
select student_id,
	   cohort,
	   date_of_birth,
	   gender,
	   race_original as race,
	   race_ethnicity,
	   home_language_code,
	   special_ed_ever,
	   age(date_first_entered_wcpss, date_of_birth) as age_first_entered_wcpss,
       age(date_entered_into_us, date_of_birth) as age_entered_into_us
from _cohort 
left join (select id,
				  gender,
	   			  race_original,
	              race_ethnicity,
	 			  home_language_code,
			      special_ed_ever
		   from student_fixed) t
on  _cohort.student_id=t.id
left join (select id, 
				  date_of_birth,
				  date_first_entered_wcpss,
				  date_entered_into_us
		   from student) s
on  _cohort.student_id=s.id
where cohort is not null;


/* update _cohort_feature: number of home languages ever reported */
create table _cohort_feature_temp as
select *,
	   home_language_2more+home_language_3more+home_language_4more+home_language_5more+home_language_6more+1 as home_language_count
from _cohort_feature left join (
	select student_id as id,
		   case when (home_language_code like '%\_%') then 1
	      		else 0 end as home_language_2more,
	       case when (home_language_code like '%\_%\_%') then 1
	      		else 0 end as home_language_3more,
	       case when (home_language_code like '%\_%\_%\_%') then 1
	      		else 0 end as home_language_4more,
	       case when (home_language_code like '%\_%\_%\_%\_%') then 1
	      		else 0 end as home_language_5more,
	       case when (home_language_code like '%\_%\_%\_%\_%\_%') then 1
	      		else 0 end as home_language_6more
	from _cohort_feature) s
	on (_cohort_feature.student_id=s.id);

alter table _cohort_feature_temp drop column id;
drop table if exists _cohort_feature;
alter table _cohort_feature_temp rename to _cohort_feature;

/* update _cohort_feature: number of races ever reported */
create table _cohort_feature_temp as
select *
from _cohort_feature left join (
	select student_id as id,
		   case when (race like '%\_%') then 1
	      		else 0 end as race_2more
	from _cohort_feature) s
	on (_cohort_feature.student_id=s.id);
alter table _cohort_feature_temp drop column id;
drop table if exists _cohort_feature;
alter table _cohort_feature_temp rename to _cohort_feature;

          
/* jumps in enrollment */
select count(distinct id) from
(select id,
        academic_year,
        grade_level,
        prev_academic_year,
        prev_grade_level,
		grade_diff-year_diff as jump
from
(select student_id as id,
		academic_year,
		grade_level,
		lag(academic_year) over (partition by student_id order by academic_year asc) as prev_academic_year,
		lag(grade_level) over (partition by student_id order by academic_year asc) as prev_grade_level,
		academic_year-lag(academic_year) over (partition by student_id order by academic_year asc) as year_diff,
		grade_level-lag(grade_level) over (partition by student_id order by academic_year asc) as grade_diff
from _cohort_by_year_feature
where grade_level between 9 and 12) t
) s
where jump > 0;
