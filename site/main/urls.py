"""
 This file was created on October 15th, 2016
 by Deborah Venuti and James Riley

 Last updated on: November 16th, 2016
 Updated by: Deborah Venuti
"""

from django.conf.urls import url
from django.contrib.auth.views import logout

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^about$', views.about, name='about'),
    url(r'^profile$', views.profile, name='profile'),
    url(r'^encrypt$', views.encrypt, name='encrypt'),
    url(r'^decrypt$', views.decrypt, name='decrypt'),
    url(r'^signin$', views.signin, name='signin'),
    url(r'^signout$', logout, {'next_page': '/'}, name='signout'),
    url(r'^register$', views.register, name='register'),
    url(r'^settings$', views.settings, name='settings')
]