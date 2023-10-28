from django.shortcuts import render


def main(request):
    return render(request, "parcel_main.html", {})
