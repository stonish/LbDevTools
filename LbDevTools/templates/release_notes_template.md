{% set categories = [
    'selection', 'hlt1', 'hlt2', 'Configuration',
    'Decoding', 'Tracking', 'PV finding', 'Muon', 'Calo', 'RICH', 'Jets',
    'PID', 'Composites', 'Filters', 'Functors',
    'Event model', 'Persistency',
    'MC checking', 'Monitoring', 'Luminosity',
    'Core', 'Conditions', 'Utilities',
    'Simulation',  'Tuples', 'Accelerators',
    'Flavour tagging',
    'Build',
    ] -%}
{% set used_mrs = [] -%}
{% set used_dep_mrs = [] -%}
{% set highlight_mrs = select_mrs(get_dep_mrs(), ['highlight']) -%}
{% macro section(labels, mrs=merge_requests, used=used_mrs, indent='', highlight='highlight') -%}
{% for mr in order_by_label(select_mrs(mrs, labels, used), categories) -%}
  {% set mr_labels = categories|select("in", mr.labels)|list -%}
{{indent}}- {% if mr_labels %}{{mr_labels|map('label_ref')|join(' ')}} | {% endif -%}
    {{mr.title|sentence}}, {{mr|mr_ref(project_fullname)}} (@{{mr.author.username}}){% if mr.issue_refs %} [{{mr.issue_refs|join(',')}}]{% endif %}{% if highlight in mr.labels %} :star:{% endif %}
{# {{mr.description|mdindent(2)}} -#}
{% endfor -%}
{% endmacro -%}
{{date}} {{project}} {{version}}
===

This version uses
{{project_deps[:-1]|join(',\n')}} and
{{project_deps|last}}.

This version is released on `master` branch.
Built relative to {{project}} [{{project_prev_tag}}](../-/tags/{{project_prev_tag}}), with the following changes:

### New features ~"new feature"

{{ section(['new feature']) -}}
- Upstream project highlights :star:
{{ section(['new feature'], mrs=highlight_mrs, used=used_dep_mrs, indent='  ', highlight=None) }}

### Fixes ~"bug fix" ~workaround

{{ section(['bug fix', 'workaround']) -}}
- Upstream project highlights :star:
{{ section(['bug fix', 'workaround'], mrs=highlight_mrs, used=used_dep_mrs, indent='  ', highlight=None) }}

### Enhancements ~enhancement

{{ section(['enhancement']) -}}
- Upstream project highlights :star:
{{ section(['enhancement'], mrs=highlight_mrs, used=used_dep_mrs, indent='  ', highlight=None) }}

### Code cleanups and changes to tests ~modernisation ~cleanup ~testing

{{ section(['cleanup', 'modernisation', 'testing']) -}}
- Upstream project highlights :star:
{{ section(['cleanup'], mrs=highlight_mrs, used=used_dep_mrs, indent='  ', highlight=None) }}

### Documentation ~Documentation

{# Collect documentation independently, may lead to repeated entries -#}
{{ section(['Documentation'], used=None) -}}
{# Mark as used such documentation does not appear under Other -#}
{% set dummy = section(['Documentation']) -%}

### Other

{{ section([[]]) }}
