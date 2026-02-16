from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import ORMUser

class ORMUserCreatrionForm(UserCreationForm):
    class Meta:
        model = ORMUser
        fields = ('email', 'username',)

class ORMUserChangeForm(UserChangeForm):
    class Meta:
        model = ORMUser
        fields = ('email', 'username',)