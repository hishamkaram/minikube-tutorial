from django.http.response import HttpResponse

# Create your views here.


def index(request):
    return HttpResponse(b'Hello World!', status=200)
