/* wake._cohort_by_year_feature: start populating with time-dependent features */
/* requires wake._cohort_by_year table */
drop table if exists wake._cohort_by_year_feature;
create table wake._cohort_by_year_feature as
select student_id, 
	   cohort,
	   academic_year, 
	   grade_level
from  wake._cohort_by_year;


/* update wake._cohort_by_year_feature: adding countdown */
drop table if exists wake._cohort_by_year_feature_temp;
create table wake._cohort_by_year_feature_temp as
select *,
	   cohort - academic_year as countdown
from wake._cohort_by_year_feature;
drop table if exists wake._cohort_by_year_feature;
alter table wake._cohort_by_year_feature_temp rename to _cohort_by_year_feature;


/* absences */
drop table if exists wake._cohort_by_year_feature_temp;
create table wake._cohort_by_year_feature_temp as
select * from wake._cohort_by_year_feature
left join (
select 	student_id as id, 
		academic_year as yr, 
	  	case when (academic_year >= 2004 and days_absent is not null) then days_absent
	   		 when (academic_year >= 2004 and days_absent is null) then 0
	   		 else null end as days_absent,
	   	case when (academic_year >= 2004 and excused_absence is not null) then excused_absence
	   		 when (academic_year >= 2004 and excused_absence is null) then 0
	   		 else null end as excused_absence,
	    case when (academic_year >= 2004 and unexcused_absence is not null) then unexcused_absence
	   		 when (academic_year >= 2004 and unexcused_absence is null) then 0
	   		 else null end as unexcused_absence
from wake.school_attendance) t
on (wake._cohort_by_year_feature.student_id=t.id and wake._cohort_by_year_feature.academic_year=t.yr);
alter table wake._cohort_by_year_feature_temp drop column id;
alter table wake._cohort_by_year_feature_temp drop column yr;
drop table if exists wake._cohort_by_year_feature;
alter table wake._cohort_by_year_feature_temp rename to _cohort_by_year_feature;


/* suspension */
drop table if exists wake._cohort_by_year_feature_temp;
drop view if exists wake._disc_working cascade;
create view wake._disc_working as
select  student_id as id, 
	    date_part('year', date_trunc('year', incident_date + interval '184 days')) - 1 as yr,
	    suspension_length,
	    primary_policy_violation,
	  	case when (	"Acts of Terror" is true or
					"Bomb Threat" is true or					
					"Bomb Threat: Aiding/Abetting" is true or
					"Fire Setting/Incendiary Material" is true or
					"Threat/False Threat" is true ) then 1
		else 0 end as terror,
		case when ( "Assault Involving Weapon/Dangerous Instrument/Substances" is true or
					"Assault Involving a Weapon(Grade 6-12)" is true or
					"Assault Involving a Weapon/Dangerous Instrument/Substances" is true or
					"Assault on Employee/Adult(13 or Older)-Serious Injury" is true or
					"Assault on Employee/Adult(Grade 6-12)-First Violation" is true or
					"Assault on School Personnel or Other Adult" is true or
					"Assault on Student" is true or
					"Assault on Student(13 or Older)-Witnessed by School Official" is true or
					"Assault on Student(Grade 6-12)-First Violation" is true or
					"Assault on Student(Grade K-5)-First Violation" is true or
					"Assault on Student: Actual Serious Injury" is true or
					"Fighting/Assault-Multiple on One (Grade 6-12)" is true or
					"Fighting/Physical Aggression" is true or
					"Instigation of Fight/Physical Aggression" is true or
					"Physical Aggression/Fighting" is true ) then 1
		else 0 end as assault,
		case when ( "Cheating" is true or
					"Class/Activity Disturbance" is true or
					"School / Class Attendance" is true or
					"School Disturbance" is true ) then 1
		else 0 end as disc_academic,
		case when ( "Gang and Gang Related Activity" is true or
					"Gang/Gang Related Activity" is true ) then 1
		else 0 end as gang,
		case when (	"Assault Involving Weapon/Dangerous Instrument/Substances" is true or
					"Assault Involving a Weapon(Grade 6-12)" is true or
					"Assault Involving a Weapon/Dangerous Instrument/Substances" is true or
					"Bomb Threat" is true or					
					"Bomb Threat: Aiding/Abetting" is true or
					"Firearm(14 or older) Possess or Handle on School Property" is true or
					"Firearm/Destructive Device K-12" is true or
					"Firearm/Explosive Device(K-12) on School Property" is true ) then 1
		else 0 end as weapon,
		case when (	"Narcotics/Alcohol/Controlled Substances/Chemicals/Drug Parapher" is true or
					"Possess/Distribute/Use of Alcohol/Drug/Paraphernalia" is true or
					"Possession/Use Drugs/Alcohol or Paraphernalia-ACE" is true or
					"Possession/Use Drugs/Alcohol or Paraphernalia-Alternative Offer" is true or
					"Possession/Use Drugs/Alcohol or Paraphernalia-Repeat Violation" is true or
					"Sale/Distribution of Drugs/Alcohol" is true or
					"Sale/Distribution of NCCSA Schedule I/II Drugs(14 or older)" is true ) then 1
		else 0 end as drug,
		violence_category_code,
		suspension_type
from wake.discipline_temp;

drop view if exists wake._disc_working2 cascade;
create view wake._disc_working2 as
select distinct id, yr,
	   count(*) over w as susp_count,
	   sum(suspension_length) over w as total_susp_days,
	   min(suspension_length) over w as min_susp_days,
	   max(suspension_length) over w as max_susp_days,
	   sum(terror) over w as terror,
	   sum(assault) over w as assault,
	   sum(academic) over w as academic,
	   sum(gang) over w as gang,
	   sum(weapon) over w as weapon,
	   sum(drug) over w as drug,
	   sum(case when (terror = 0 and 
	   				  assault = 0 and
	   				  academic = 0 and
	   				  gang = 0 and
	   				  weapon = 0 and
	   				  drug = 0) then 1 else 0 end) over w as other
from wake._disc_working
window w as (partition by id, yr);

create table wake._cohort_by_year_feature_temp as
select *,
	   case when (academic_year between 2007 and 2013 and susp_count is not null) then susp_count
	   		when (academic_year between 2007 and 2013 and susp_count is null) then 0
	   		else null end as suspension_count,
	   case when (academic_year between 2007 and 2013 and total_susp_days is not null) then total_susp_days
	   		when (academic_year between 2007 and 2013 and total_susp_days is null) then 0
	   		else null end as suspension_days,
	   case when (academic_year between 2007 and 2013 and min_susp_days is not null) then min_susp_days
	   		when (academic_year between 2007 and 2013 and min_susp_days is null) then 0
	   		else null end as min_suspension_days,
	   case when (academic_year between 2007 and 2013 and max_susp_days is not null) then max_susp_days
	   		when (academic_year between 2007 and 2013 and max_susp_days is null) then 0
	   		else null end as max_suspension_days,
	   case when (academic_year between 2007 and 2013 and terror > 0) then 1
	   		when (academic_year between 2007 and 2013) then 0
	   		else null end as disc_terror,
	   case when (academic_year between 2007 and 2013 and assault > 0) then 1
	   		when (academic_year between 2007 and 2013) then 0
	   		else null end as disc_assault,
	   case when (academic_year between 2007 and 2013 and academic > 0) then 1
	   		when (academic_year between 2007 and 2013) then 0
	   		else null end as disc_academic,
	   case when (academic_year between 2007 and 2013 and gang > 0) then 1
	   		when (academic_year between 2007 and 2013) then 0
	   		else null end as disc_gang,
	   case when (academic_year between 2007 and 2013 and weapon > 0) then 1
	   		when (academic_year between 2007 and 2013) then 0
	   		else null end as disc_weapon,
	   case when (academic_year between 2007 and 2013 and drug > 0) then 1
	   		when (academic_year between 2007 and 2013) then 0
	   		else null end as disc_drug,
	   case when (academic_year between 2007 and 2013 and other > 0) then 1
	   		when (academic_year between 2007 and 2013) then 0
	   		else null end as disc_other
from wake._cohort_by_year_feature left join (
select * from wake._disc_working2) t
on (wake._cohort_by_year_feature.student_id=t.id and wake._cohort_by_year_feature.academic_year=t.yr);
alter table wake._cohort_by_year_feature_temp drop column id;
alter table wake._cohort_by_year_feature_temp drop column yr;
drop table if exists wake._cohort_by_year_feature;
alter table wake._cohort_by_year_feature_temp rename to _cohort_by_year_feature;
drop view if exists wake._disc_working cascade;
drop view if exists wake._disc_working2 cascade;


/* course work info */
drop view if exists wake._course_working cascade;
create view wake._course_working as
select 	*,
		cast(grade_level as int) as grade,
		case when (mark in ('A-', 'A', 'A+') or 
				   (case when mark ~ E'^\\d+$' then mark::integer else 0 end) >= 90) then 1
			 else 0 end as mark_is_a,
		case when (mark in ('B-', 'B', 'B+') or 
				   (case when mark ~ E'^\\d+$' then mark::integer else 0 end) between 80 and 89) then 1
			 else 0 end as mark_is_b,
		case when (mark in ('C-', 'C', 'C+') or 
				   (case when mark ~ E'^\\d+$' then mark::integer else 0 end) between 70 and 79) then 1
			 else 0 end as mark_is_c,
		case when (mark in ('D-', 'D', 'D+') or 
				   (case when mark ~ E'^\\d+$' then mark::integer else 0 end) between 60 and 69) then 1
			 else 0 end as mark_is_d,
		case when mark = 'F' then 1 else 0 end as mark_is_f
from wake.course_enrollment left join (
select  code, 
		school_id as sid, 
		name as course_name,
		case when (upper(name) like '%HONOR%') then 1
			 else 0 end as course_honors,
		case when (upper(name) like '%ENGL%' and upper(name) like '%HONOR%') then 1
			 else 0 end as course_eng_honors,		
		case when (upper(name) similar to '%(MATH|ALGEBRA|GEOMETRY)%') then 1
			 else 0 end as course_math,
		case when (upper(name) like '%ADV%' and upper(name) similar to '%(SCIENCE|PHYSIC|CHEM|BIO)%') then 1
			 else 0 end as course_adv_sci
from wake.course) t
on wake.course_enrollment.course_code = t.code and wake.course_enrollment.school_id = t.sid
where grade_level not in ('PK', 'KI');


drop view if exists wake._course_working2 cascade;
create view wake._course_working2 as
select distinct student_id as id, academic_year as yr,
       count(*) over w as courses_taken,
       sum(course_honors) over w as course_honors,
	   sum(course_eng_honors) over w as course_eng_honors,
	   sum(course_math) over w as course_math,
       sum(course_adv_sci) over w as course_adv_sci,
       sum(mark_is_a) over w as mark_is_a,
 	   sum(mark_is_b) over w as mark_is_b,
       sum(mark_is_c) over w as mark_is_c,
 	   sum(mark_is_d) over w as mark_is_d,
       sum(mark_is_f) over w as mark_is_f
from wake._course_working
window w as (partition by student_id, academic_year);



drop table if exists wake._cohort_by_year_feature_temp;
create table wake._cohort_by_year_feature_temp as
select *,
	   case when (mark_is_a + mark_is_b + mark_is_c + mark_is_d + mark_is_f) > 0 
	        then (mark_is_a * 4 + mark_is_b * 3 + mark_is_c * 2 + mark_is_d)/(mark_is_a + mark_is_b + mark_is_c + mark_is_d + mark_is_f)::float
	   else null end as avg_gpa
from wake._cohort_by_year_feature left join (
select * from wake._course_working2) t
on (wake._cohort_by_year_feature.student_id=t.id and wake._cohort_by_year_feature.academic_year=t.yr);
alter table wake._cohort_by_year_feature_temp drop column id;
alter table wake._cohort_by_year_feature_temp drop column yr;
drop table if exists wake._cohort_by_year_feature;
alter table wake._cohort_by_year_feature_temp rename to _cohort_by_year_feature;
drop view if exists wake._course_working cascade;
drop view if exists wake._course_working2 cascade;










/* update wake._cohort_by_year_feature: adding school info from school table */

drop table if exists wake._cohort_by_year_feature_temp;
create table wake._cohort_by_year_feature_temp as
select *
from wake._cohort_by_year_feature left join (
	select student_id as id,
		   academic_year as yr,
		   current_school_id
	from wake.school_enrollment) s
	on (wake._cohort_by_year_feature.student_id=s.id and wake._cohort_by_year_feature.academic_year=s.yr);
alter table wake._cohort_by_year_feature_temp drop column id;
alter table wake._cohort_by_year_feature_temp drop column yr;
drop table if exists wake._cohort_by_year_feature;
alter table wake._cohort_by_year_feature_temp rename to _cohort_by_year_feature;


drop table if exists wake._cohort_by_year_feature_temp;
create table wake._cohort_by_year_feature_temp as		
select * from wake._cohort_by_year_feature left join (
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
   	 from wake.school) s
	on (wake._cohort_by_year_feature.current_school_id=s.school_id);
alter table wake._cohort_by_year_feature_temp drop column school_id;
drop table if exists wake._cohort_by_year_feature;
alter table wake._cohort_by_year_feature_temp rename to _cohort_by_year_feature;