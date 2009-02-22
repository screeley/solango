from django import forms
import solango
from solango.solr import get_model_from_key

def model_choices():
    models = [('','---All---')]
    models.extend([(model_key, get_model_from_key(model_key)._meta.verbose_name_plural)
             for model_key in solango.registry.keys()])
    return models

class SearchForm(forms.Form):
    q = forms.CharField(required=False)
    
    def clean_q(self):
        q = self.cleaned_data.get("q")
        if not q:
            raise forms.ValidationError("You cannot query for an empty string")
        return q
