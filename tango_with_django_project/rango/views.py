from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return HttpResponse("<a href='/rango/about/'>About Page</a></br>" + "<br>Rango says hey there world!</br>")

def about(request):
    return HttpResponse("Rango says here is the about page." +
        "<br></br><br>This tutorial has been put together by Mohammed Nayhall Baqai, 2086029</br>" +
        " <a href='/rango'>Go back</a>")
