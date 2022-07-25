from django.contrib import admin
from .models import *


admin.site.register(User)
admin.site.register(Posts)
admin.site.register(Likes)
admin.site.register(Followers)


# Register your models here.
