from .models import ArticlePost
from django import forms
class ArticlePostForm(forms.ModelForm):
    class Meta:
        model = ArticlePost
        fields = ('title','body','tags','avatar')
