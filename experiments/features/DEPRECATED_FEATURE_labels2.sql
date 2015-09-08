/* DEPRECATED; SEE _label_12regular instead */
DROP TABLE IF EXISTS wake._labels2;

CREATE TABLE wake._labels2 AS WITH 
  lenrollment AS (
    SELECT academic_year,
            student_id,
            row_number() over w AS rn,
            count(*) over w AS ct
    FROM wake.school_enrollment
    WHERE active_status = TRUE 
    window w AS (
      partition BY student_id
      ORDER BY academic_year DESC range BETWEEN unbounded preceding AND unbounded following
    )
  ), 
  filtered_lenrollment AS (
    SELECT *
    FROM lenrollment
    WHERE rn = 1
  ),
  dropout AS (
    SELECT student_id,
           withdraw_date,
           row_number() over dw AS rn,
           count(*) over dw AS ct
     FROM wake.outcome window dw AS (partition BY student_id
     ORDER BY withdraw_date DESC range BETWEEN unbounded preceding AND unbounded following)
  ),
  filtered_dropout AS (
    SELECT *
    FROM dropout
    WHERE rn = 1
  )

SELECT c.student_id,
       CASE
           WHEN (fl.academic_year > c.cohort) THEN 1
           ELSE 0
       END AS s_spring_enrollment,
       CASE
           WHEN (fl.academic_year >= c.cohort) THEN 1
           ELSE 0
       END AS late_enrollment,
       CASE
           WHEN (fl.academic_year >= c.cohort AND EXTRACT (YEAR FROM fd.withdraw_date) >= fl.academic_year) THEN 1
           ELSE 0
       END AS late_dropout,
       CASE
           WHEN (fl.academic_year <= EXTRACT (YEAR FROM fd.withdraw_date) AND EXTRACT (YEAR FROM fd.withdraw_date) <= c.cohort) THEN 1
           ELSE 0
       END AS hs_dropout,
       CASE
           WHEN fd.student_id IS NOT NULL THEN 1
           ELSE 0
       END AS ever_dropout,
       CASE
           WHEN (EXTRACT (YEAR FROM fd.withdraw_date) < fl.academic_year AND fl.academic_year < c.cohort) THEN 1
           ELSE 0
       END AS grad_and_dropout,
       CASE
           WHEN (EXTRACT (YEAR FROM fd.withdraw_date) < fl.academic_year OR fl.academic_year > c.cohort) THEN 1
           ELSE 0
       END AS not_grad_ontime
FROM wake._cohort c
LEFT OUTER JOIN filtered_lenrollment fl ON c.student_id = fl.student_id
LEFT OUTER JOIN filtered_dropout fd ON c.student_id = fd.student_id
