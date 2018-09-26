{% set used = [] -%}
{% macro section(labels) -%}
{% for mr in select_mrs(merge_requests, labels, used) %}
- {{mr.title}}, !{{mr.iid}} (@{{mr.author.username}}) {{find_tasks(mr)}}  
  {{mr.description|mdindent(2)}}
{% endfor %}
{%- endmacro %}

{{date}} {{project}} {{version}}
========================================

Short release description
----------------------------------------

Based on ...
This version is released on ... branch.

### Line developments
{{ section(['line']) }}

### New features
{{ section(['new feature']) }}

### Enhancements
{{ section(['enhancement']) }}

### Bug fixes
{{ section(['bug fix']) }}

### Cleanup and testing
{{ section(['cleanup', 'testing']) }}

### Other
{{ section([[]]) }}
