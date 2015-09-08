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

