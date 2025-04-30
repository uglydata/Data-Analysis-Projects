--2025.04.30. v1
/*
	Text Formatting in SQL
	- Capitalization and Formatting of Text

	Examples of Regex and Array Functions for Text Formatting
*/

----------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------------------

with user_content as (
	select 1 as id, 'hello world of SQL' as  content_text
	union all
	select 2 as id, 'the QUICK-brown fox L' as  content_text
	union all
	select 3 as id, 'modern-day DATA science ' as  content_text
	union all
	select 4 as id, 'web-based FRONT-end developmentL' as  content_text
)
, use_regex as (
select
    id
    , content_text as original_text
    , regexp_replace(INITCAP(content_text), '(-)([a-z])', 
                      E'\\1\\U\\2', 'g') as converted_text                  
from user_content
)
, use_arrays as (
	select 
    	id 
    	, content_text as original_text
  		, INITCAP(array_to_string(
	    ARRAY(
	      select INITCAP(word)
	      from unnest(string_to_array(content_text, '-')) as word
	    ),
	    '-'
	  )) as converted_text
from user_content
)
select 'regex' as t, * from use_regex
union all
select 'array' as t, * from use_arrays