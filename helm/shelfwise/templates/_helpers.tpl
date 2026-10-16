{{- define "shelfwise.fullname" -}}
{{- if contains .Chart.Name .Release.Name -}}
{{- .Release.Name | trunc 50 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 50 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "shelfwise.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: shelfwise
{{- end -}}

{{/* Selector labels for one component: include "shelfwise.selectorLabels" (list . "backend") */}}
{{- define "shelfwise.selectorLabels" -}}
{{- $root := index . 0 -}}
app.kubernetes.io/name: {{ $root.Chart.Name }}
app.kubernetes.io/instance: {{ $root.Release.Name }}
app.kubernetes.io/component: {{ index . 1 }}
{{- end -}}

{{- define "shelfwise.image" -}}
{{- $img := index . 0 -}}
{{- $root := index . 1 -}}
{{- printf "%s:%s" $img.repository (default $root.Chart.AppVersion $img.tag) -}}
{{- end -}}

{{- define "shelfwise.backendName" -}}{{ include "shelfwise.fullname" . }}-backend{{- end -}}
{{- define "shelfwise.frontendName" -}}{{ include "shelfwise.fullname" . }}-frontend{{- end -}}
{{- define "shelfwise.postgresName" -}}{{ include "shelfwise.fullname" . }}-postgres{{- end -}}
{{- define "shelfwise.secretName" -}}{{ .Values.postgres.existingSecret | default (printf "%s-db" (include "shelfwise.fullname" .)) }}{{- end -}}

{{/*
Postgres password: an explicit value wins; otherwise reuse the one already in the
cluster so upgrades don't lock the app out of its own database; otherwise generate one.
*/}}
{{- define "shelfwise.postgresPassword" -}}
{{- if .Values.postgres.password -}}
{{- .Values.postgres.password -}}
{{- else -}}
{{- $existing := lookup "v1" "Secret" .Release.Namespace (include "shelfwise.secretName" .) -}}
{{- if and $existing $existing.data (index $existing.data "POSTGRES_PASSWORD") -}}
{{- index $existing.data "POSTGRES_PASSWORD" | b64dec -}}
{{- else -}}
{{- randAlphaNum 24 -}}
{{- end -}}
{{- end -}}
{{- end -}}
