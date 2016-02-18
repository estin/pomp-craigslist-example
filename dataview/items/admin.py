from django import forms
from django.db.models import Count
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.template import Template, Context


from dataview.items.models import CraigsListItem


class ListFilterBase(admin.SimpleListFilter):

    def lookups(self, request, model_admin):
        qs = CraigsListItem.objects \
            .values(self.parameter_name) \
            .annotate(count=Count(self.parameter_name)) \
            .order_by('-count', self.parameter_name)

        return (
            (
                i[self.parameter_name],
                ('{%s} ({count})' % self.parameter_name).format(**i),
            ) for i in qs if i[self.parameter_name]
        )

    def queryset(self, request, queryset):
        city_code = self.value()
        if city_code:
            return queryset.filter(**{self.parameter_name: self.value()})
        return queryset


class CityCodeListFilter(ListFilterBase):
    title = 'city code'
    parameter_name = 'city_code'


class SessionIdListFilter(ListFilterBase):
    title = 'session id'
    parameter_name = 'session_id'


class PhotosWidget(forms.Widget):
    template = Template("""
    <div id="id_{{field_name}}">
        <ol>
            {% for img in photos %}
            <li>
                <a href="{{ img }}" target="_blank">{{ img }}</a>
            </li>
            {% endfor %}
        </ol>
    </div>
    """)

    template = Template("""
        <table widht="80%"><tr>
        {% for img in photos %}
        <td>
            <a href="{{ img }}" width="33%" target="_blank">
                <img src="{{ img }}"/>
            </a>
        </td>
        {% if forloop.last %}
            </tr>
        {% else %}
            {% if forloop.counter|divisibleby:"2" %}
            </tr><tr>
            {% endif %}
        {% endif %}
        {% endfor %}
        </table>
    """)

    def render(self, name, value, attrs=None):
        return mark_safe(self.template.render(Context({
            'field_name': name,
            'photos': value.split(',')
        })))


class CraigsListItemForm(forms.ModelForm):
    class Meta:
        model = CraigsListItem
        fields = '__all__'
        widgets = {
            'photos': PhotosWidget(),
        }


class CraigsListItemAdmin(admin.ModelAdmin):
    form = CraigsListItemForm
    list_display = (
        'id', 'ts_created', 'ts_imported',
        'session_id', 'city_code', 'title', 'price',
    )
    list_filter = (SessionIdListFilter, CityCodeListFilter, )


admin.site.register(CraigsListItem, CraigsListItemAdmin)
