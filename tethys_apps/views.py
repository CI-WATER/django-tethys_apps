from django.shortcuts import render

from tethys_apps.harvesters.app_harvester import SingletonAppHarvester


def library(request):
    """
    Handle the library view
    """
    harvester = SingletonAppHarvester()
    context = {'apps': harvester.apps}
    return render(request, 'tethys_apps/app_library.html', context)
