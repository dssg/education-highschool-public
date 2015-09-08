/* wake._cohort_feature: start populating with static features */
/* requires wake._cohort table */



drop table if exists wake._cohort_feature;
create table wake._cohort_feature as
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
from wake._cohort 
left join (select id,
				  gender,
	   			  race_original,
	              race_ethnicity,
	 			  home_language_code,
			      special_ed_ever
		   from wake.student_fixed) t
on  wake._cohort.student_id=t.id
left join (select id, 
				  date_of_birth,
				  date_first_entered_wcpss,
				  date_entered_into_us
		   from wake.student) s
on  wake._cohort.student_id=s.id
where cohort is not null;


/* update wake._cohort_feature: relative age to cohort */
drop table if exists wake._cohort_feature_temp;
create table wake._cohort_feature_temp as
select *,
	   extract(epoch from (to_date(to_char(cohort, '9999'), 'yyyy') + interval '14 months') -
		(date_of_birth + interval '20 years'))/(60*60*24*365) as rel_age_to_cohort
from wake._cohort_feature;
drop table if exists wake._cohort_feature;
alter table wake._cohort_feature_temp rename to _cohort_feature;

create table wake._cohort_feature_temp as
select *,
	   case when (rel_age_to_cohort between 1 and 3) then 1
	   		else 0 end as rel_age_to_cohort_1to3_years_older   
from wake._cohort_feature;
drop table if exists wake._cohort_feature;
alter table wake._cohort_feature_temp rename to _cohort_feature;



/* update wake._cohort_feature: number of home languages ever reported */
create table wake._cohort_feature_temp as
select *,
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
from wake._cohort_feature;
drop table if exists wake._cohort_feature;
alter table wake._cohort_feature_temp rename to _cohort_feature;

create table wake._cohort_feature_temp as
select *,
	   home_language_2more+home_language_3more+home_language_4more+home_language_5more+home_language_6more+1 as home_language_count
from wake._cohort_feature;
drop table if exists wake._cohort_feature;
alter table wake._cohort_feature_temp rename to _cohort_feature;


/* update wake._cohort_feature: number of races ever reported */
create table wake._cohort_feature_temp as
select *,
	   case when (race like '%\_%') then 1
      		else 0 end as race_2more
from wake._cohort_feature;
drop table if exists wake._cohort_feature;
alter table wake._cohort_feature_temp rename to _cohort_feature;


/* update wake._cohort_feature: hispanic */
create table wake._cohort_feature_temp as
select *,
	   case when (race like '%H%') then 1
      		else 0 end as race_is_hispanic,
       case when (race_ethnicity like '%H%') then 1
      		else 0 end as race_ethnicity_is_hispanic
from wake._cohort_feature;
drop table if exists wake._cohort_feature;
alter table wake._cohort_feature_temp rename to _cohort_feature;

