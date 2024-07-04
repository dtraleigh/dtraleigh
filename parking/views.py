from django.shortcuts import render


def main(request):

    return render(request, "parking_main.html", {})
