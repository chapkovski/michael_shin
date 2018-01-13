
# from django.views.generic import TemplateView

import sandbox.views as v

# urls.py
from django.conf.urls import url
from otree.urls import urlpatterns



print('i am in otree ext')
urlpatterns.append(url(r'^vignette$', v.VignetteView.as_view(), name='vignette_customization'),)