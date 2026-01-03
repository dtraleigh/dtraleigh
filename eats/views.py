import django
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, F, ExpressionWrapper, fields
from eats.models import *
from eats.forms import *
from itertools import chain
from django.db.models.functions import TruncYear
from datetime import date, timedelta


def home(request):
    """Create the list of businesses that should be shown on the main site and the districts"""
    district_list = District.objects.all().order_by("name")

    # Get only open businesses. Basically, if it has a closing date equal or lt today, it's open or coming soon.
    open_and_coming_soon_businesses = Business.objects.filter(~Q(close_date__lt=datetime.datetime.today())).order_by(
        "name")

    # Get only open Vendors. Basically, if it has a closing date equal or lt today, it's open or coming soon.
    open_and_coming_soon_vendors = Vendor.objects.filter(
        Q(open_date__lte=datetime.datetime.today()) &
        (Q(close_date=None) | Q(close_date__gt=datetime.datetime.today()))
    ).order_by("name")

    return render(request, "index.html",
                  {"business_list": open_and_coming_soon_businesses,
                   "vendor_list": open_and_coming_soon_vendors,
                   "district_list": district_list})


def home_test(request):
    """For testing and tinkering"""
    district_list = District.objects.all().order_by("name")

    # Get only open businesses. Basically, if it has a closing date equal or lt today, it's open or coming soon.
    open_and_coming_soon_businesses = Business.objects.filter(~Q(close_date__lt=datetime.datetime.today())).order_by(
        "name")

    # Get only open Vendors. Basically, if it has a closing date equal or lt today, it's open or coming soon.
    open_and_coming_soon_vendors = Vendor.objects.filter(
        Q(open_date__lte=datetime.datetime.today()) &
        (Q(close_date=None) | Q(close_date__gt=datetime.datetime.today()))
    ).order_by("name")

    return render(request, "index_test.html",
                  {"business_list": open_and_coming_soon_businesses,
                   "vendor_list": open_and_coming_soon_vendors,
                   "district_list": district_list})


def tips_main(request):
    """Page for showing tips to visitors"""
    all_tips = Tip.objects.filter((Q(open_date=None) |
                                   Q(open_date__gt=datetime.datetime.today())) &
                                  Q(added=False)).order_by("-date")
    today = datetime.date.today()

    return render(request, "tips_main.html", {"all_tips": all_tips,
                                              "today": today})


def eats_login(request):
    """This is the login page for the management view. (not the django admin page)"""
    message = "Log in"

    if request.POST:
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                message = "Login successful."
                login(request, user)

                return HttpResponseRedirect("/eats/manage/main/")
            else:
                message = "Account is disabled."
        else:
            message = "Invalid login."

    return render(request, "login.html", {"message": message})


def eats_logout(request):
    logout(request)

    return HttpResponseRedirect("/eats/manage/")


@login_required(login_url="/eats/manage/")
def main(request):
    """This is the main manage page."""
    all_businesses = Business.objects.all().order_by("-date_added")
    all_vendors = Vendor.objects.all().order_by("-date_added")
    all_places = sorted(chain(all_businesses, all_vendors), key=lambda place: place.date_added, reverse=True)

    recent_snapshot = Snapshot.objects.latest("date")

    total_open = recent_snapshot.local_business_count + recent_snapshot.not_local_business_count

    local_percent = (recent_snapshot.local_business_count / total_open) * 100

    return render(request, "main.html", {"all_places": all_places,
                                         "recent_snapshot": recent_snapshot,
                                         "local_percent": round(local_percent, 1)})


@login_required(login_url="/eats/manage/")
def add_business(request):
    """This page has a form for adding a new business."""
    if request.method == "POST":
        form = EditBusinessForm(request.POST)

        if "cancel-button" in request.POST:
            messages.info(request, "Canceled adding new business.")

            return HttpResponseRedirect("/eats/manage/main/")

        if form.is_valid():
            new_business_name = form.cleaned_data["name"]
            form.save()
            messages.success(request, f"New business, {new_business_name}, added.")

            return HttpResponseRedirect("/eats/manage/main/")
    else:
        # form = new_business_form(initial={"link": "http://", })
        form = NewBusinessForm()

    return render(request, "business_add.html", {"form": form})


@login_required(login_url="/eats/manage/")
def edit_business(request, biz_id):
    """This page should show the edit business form"""
    business_to_edit = Business.objects.get(id=biz_id)

    if request.method == "POST":
        form = EditBusinessForm(request.POST, instance=business_to_edit)

        if "cancel-button" in request.POST:
            messages.info(request, f"Canceled edit to {business_to_edit.name}.")

            return HttpResponseRedirect("/eats/manage/main/")

        if form.is_valid():
            form.save()
            messages.success(request, f"Details for {business_to_edit.name} updated.")

            if "save-logout-button" in request.POST:
                return HttpResponseRedirect("/eats/manage/main/logout/")
            else:
                return HttpResponseRedirect("/eats/manage/main/")
    else:
        form = EditBusinessForm(instance=business_to_edit)

    return render(request, "business_edit.html", {"form": form})


@login_required(login_url="/eats/manage/")
def add_vendor(request):
    """This page has a form for adding a new vendor."""
    if request.method == "POST":
        form = EditVendorForm(request.POST)

        if "cancel-button" in request.POST:
            messages.info(request, "Canceled adding new vendor.")

            return HttpResponseRedirect("/eats/manage/main/")

        if form.is_valid():
            new_vendor_name = form.cleaned_data["name"]
            form.save()
            messages.success(request, f"New vendor, {new_vendor_name}, added.")

            return HttpResponseRedirect("/eats/manage/main/")
    else:
        # form = new_vendor_form(initial={"link": "http://", })
        form = NewVendorForm()
        form.fields["food_hall"].queryset = Business.objects.filter(is_food_hall=True)

    return render(request, "vendor_add.html", {"form": form})


@login_required(login_url="/eats/manage/")
def edit_vendor(request, vendor_id):
    """This page should show the edit vendor form"""
    vendor_to_edit = Vendor.objects.get(id=vendor_id)

    if request.method == "POST":
        form = EditVendorForm(request.POST, instance=vendor_to_edit)

        if "cancel-button" in request.POST:
            messages.info(request, f"Canceled edit to {vendor_to_edit.name}.")

            return HttpResponseRedirect("/eats/manage/main/")

        if form.is_valid():
            form.save()
            messages.success(request, f"Details for {vendor_to_edit.name} updated.")

            if "save-logout-button" in request.POST:
                return HttpResponseRedirect("/eats/manage/main/logout/")
            else:
                return HttpResponseRedirect("/eats/manage/main/")
    else:
        form = EditVendorForm(instance=vendor_to_edit)
        form.fields["food_hall"].queryset = Business.objects.filter(is_food_hall=True)

    return render(request, "vendor_edit.html", {"form": form})


@login_required(login_url="/eats/manage/")
def tips_page(request):
    """This page shows and manages all the tips."""
    tip_list = Tip.objects.all()
    district_list = District.objects.all()
    today = datetime.date.today()
    open_businesses = Business.objects.filter(Q(open_date__lte=datetime.datetime.today()) &
                                              (Q(close_date=None) | Q(close_date__gt=datetime.datetime.today()))
                                              )

    if request.method == "POST":
        tip_form = NewTipForm(request.POST)

        if "cancel-button" in request.POST:
            messages.info(request, "Canceled adding new tip.")

            return HttpResponseRedirect("/eats/manage/tips/")

        if tip_form.is_valid():
            new_tip_name = tip_form.cleaned_data["name"]
            tip_form.save()
            messages.success(request, f"New tip, {new_tip_name}, added.")

            return HttpResponseRedirect("/eats/manage/tips/")
    else:
        tip_form = NewTipForm()
        tip_form.fields["food_hall"].queryset = Business.objects.filter(is_food_hall=True)

    return render(request, "tips.html", {"tip_list": tip_list,
                                         "district_list": district_list,
                                         "tip_form": tip_form,
                                         "today": today,
                                         "open_businesses": open_businesses})


@login_required(login_url="/eats/manage/")
def edit_tips_page(request, tip_id):
    the_tip = Tip.objects.get(id=tip_id)

    if request.method == "POST":
        tip_form = EditTipForm(request.POST, instance=the_tip)

        if "cancel-button" in request.POST:
            messages.info(request, "Canceled editing the tip.")

            return HttpResponseRedirect("/eats/manage/tips/")

        if "delete-button" in request.POST:
            the_tip.delete()
            messages.info(request, "Tip has been deleted.")

            return HttpResponseRedirect("/eats/manage/tips/")

        if tip_form.is_valid():
            tip_form.save()

            if "create-biz" in request.POST:
                new_biz = Business.objects.create(name=the_tip.name,
                                                  district=the_tip.district,
                                                  link=the_tip.link,
                                                  description=the_tip.description,
                                                  has_outdoor_seating=the_tip.has_outdoor_seating,
                                                  is_temp_closed=the_tip.is_temp_closed,
                                                  is_eats=the_tip.is_eats,
                                                  is_drinks=the_tip.is_drinks,
                                                  is_coffee=the_tip.is_coffee,
                                                  not_local=the_tip.not_local,
                                                  open_date=the_tip.open_date)
                the_tip.added = True
                the_tip.save()

                messages.info(request, f"New business {new_biz.name} created.")

            if "create-vendor" in request.POST:
                new_vendor = Vendor.objects.create(name=the_tip.name,
                                                   food_hall=the_tip.food_hall,
                                                   link=the_tip.link,
                                                   description=the_tip.description,
                                                   is_temp_closed=the_tip.is_temp_closed,
                                                   not_local=the_tip.not_local,
                                                   open_date=the_tip.open_date)
                the_tip.added = True
                the_tip.save()

                messages.info(request, f"New vendor {new_vendor.name} created.")

            messages.success(request, f"Tip, {the_tip.name}, edited.")

            return HttpResponseRedirect("/eats/manage/tips/")
    else:
        tip_form = EditTipForm(instance=the_tip)
        tip_form.fields["food_hall"].queryset = Business.objects.filter(is_food_hall=True)

    return render(request, "edit_tips.html", {"tip_form": tip_form})


@login_required(login_url="/eats/manage/")
def ref_link_page(request):
    ref_link_list = ReferenceLink.objects.all().order_by("-date_created")

    if request.method == "POST":
        link_form = CreateRefLinkForm(request.POST)

        if "cancel-button" in request.POST:
            messages.info(request, "Canceled creating reference link.")

            return HttpResponseRedirect("/eats/manage/tips/")

        if link_form.is_valid():
            new_headline = link_form.cleaned_data["headline"]
            link_form.save()
            messages.success(request, f"Reference Link, {new_headline}, added.")

            if "save-and-add" in request.POST:
                return HttpResponseRedirect("/eats/manage/tips/reference_link/")
            else:
                return HttpResponseRedirect("/eats/manage/tips/")

    else:
        link_form = CreateRefLinkForm()

    return render(request, "ref_link.html", {"ref_link_list": ref_link_list,
                                             "link_form": link_form})


@login_required(login_url="/eats/manage/")
def edit_ref_link_page(request, ref_id):
    ref_link = ReferenceLink.objects.get(id=ref_id)

    if request.method == "POST":
        link_form = CreateRefLinkForm(request.POST, instance=ref_link)

        if "cancel-button" in request.POST:
            messages.info(request, "Canceled editing reference link.")

            return HttpResponseRedirect("/eats/manage/tips/reference_link/")

        if link_form.is_valid():
            new_headline = link_form.cleaned_data["headline"]
            link_form.save()
            messages.success(request, f"Reference Link {new_headline}, edited.")

            return HttpResponseRedirect("/eats/manage/tips/reference_link/")

    else:
        link_form = CreateRefLinkForm(initial={"url_link": ref_link.url_link,
                                               "description": ref_link.description,
                                               "headline": ref_link.headline,
                                               "date_published": ref_link.date_published
                                               })

    return render(request, "edit_ref_link.html", {"ref_link": ref_link,
                                                  "link_form": link_form})


def stats(request):
    """Generate comprehensive statistics view for downtown businesses"""

    # Current snapshot
    snapshot = {
        'total_open': Business.objects.filter(close_date__isnull=True).count(),
        'total_closed': Business.objects.filter(close_date__isnull=False).count(),
        'eats_open': Business.objects.filter(close_date__isnull=True, is_eats=True).count(),
        'drinks_open': Business.objects.filter(close_date__isnull=True, is_drinks=True).count(),
        'coffee_open': Business.objects.filter(close_date__isnull=True, is_coffee=True).count(),
    }

    # Calculate net growth per year
    years = range(2016, date.today().year + 1)
    yearly_data = []

    for year in years:
        # Exclude initial data load for openings in 2016
        if year == 2016:
            openings = Business.objects.filter(
                open_date__year=year
            ).exclude(open_date=date(2016, 3, 14)).count()
        else:
            openings = Business.objects.filter(open_date__year=year).count()

        closings = Business.objects.filter(close_date__year=year).count()
        net = openings - closings

        yearly_data.append({
            'year': year,
            'openings': openings,
            'closings': closings,
            'net_growth': net
        })

    # Running total of open businesses at end of each year
    running_total = []
    for year in years:
        year_end = date(year, 12, 31)

        # Businesses that opened on or before year end AND
        # (never closed OR closed after year end)
        open_at_year_end = Business.objects.filter(
            Q(open_date__lte=year_end) &
            (Q(close_date__isnull=True) | Q(close_date__gt=year_end))
        ).count()

        running_total.append({
            'year': year,
            'open_businesses': open_at_year_end
        })

    # Openings by year by category (excluding initial load)
    eats_by_year = list(Business.objects
                        .filter(is_eats=True)
                        .exclude(open_date=date(2016, 3, 14))
                        .annotate(year=TruncYear('open_date'))
                        .values('year')
                        .annotate(count=Count('id'))
                        .order_by('year'))

    drinks_by_year = list(Business.objects
                          .filter(is_drinks=True)
                          .exclude(open_date=date(2016, 3, 14))
                          .annotate(year=TruncYear('open_date'))
                          .values('year')
                          .annotate(count=Count('id'))
                          .order_by('year'))

    coffee_by_year = list(Business.objects
                          .filter(is_coffee=True)
                          .exclude(open_date=date(2016, 3, 14))
                          .annotate(year=TruncYear('open_date'))
                          .values('year')
                          .annotate(count=Count('id'))
                          .order_by('year'))

    # Closings by year by category
    eats_closings_by_year = list(Business.objects
                                 .filter(is_eats=True, close_date__isnull=False)
                                 .annotate(year=TruncYear('close_date'))
                                 .values('year')
                                 .annotate(count=Count('id'))
                                 .order_by('year'))

    drinks_closings_by_year = list(Business.objects
                                   .filter(is_drinks=True, close_date__isnull=False)
                                   .annotate(year=TruncYear('close_date'))
                                   .values('year')
                                   .annotate(count=Count('id'))
                                   .order_by('year'))

    coffee_closings_by_year = list(Business.objects
                                   .filter(is_coffee=True, close_date__isnull=False)
                                   .annotate(year=TruncYear('close_date'))
                                   .values('year')
                                   .annotate(count=Count('id'))
                                   .order_by('year'))

    # District-level analysis
    districts_data = []
    for district in District.objects.all():
        district_yearly = []

        for year in years:
            if year == 2016:
                openings = Business.objects.filter(
                    district=district,
                    open_date__year=year
                ).exclude(open_date=date(2016, 3, 14)).count()
            else:
                openings = Business.objects.filter(
                    district=district,
                    open_date__year=year
                ).count()

            closings = Business.objects.filter(
                district=district,
                close_date__year=year
            ).count()

            district_yearly.append({
                'year': year,
                'openings': openings,
                'closings': closings,
                'net': openings - closings
            })

        districts_data.append({
            'district': district,
            'currently_open': Business.objects.filter(
                district=district, close_date__isnull=True
            ).count(),
            'total_opened': Business.objects.filter(
                district=district
            ).exclude(open_date=date(2016, 3, 14)).count(),
            'total_closed': Business.objects.filter(
                district=district, close_date__isnull=False
            ).count(),
            'yearly_data': district_yearly
        })

    # Recent trends (last 12 months)
    one_year_ago = date.today() - timedelta(days=365)
    recent_trends = {
        'openings': Business.objects.filter(open_date__gte=one_year_ago).count(),
        'closings': Business.objects.filter(close_date__gte=one_year_ago).count(),
        'eats_openings': Business.objects.filter(open_date__gte=one_year_ago, is_eats=True).count(),
        'eats_closings': Business.objects.filter(close_date__gte=one_year_ago, is_eats=True).count(),
        'drinks_openings': Business.objects.filter(open_date__gte=one_year_ago, is_drinks=True).count(),
        'drinks_closings': Business.objects.filter(close_date__gte=one_year_ago, is_drinks=True).count(),
        'coffee_openings': Business.objects.filter(open_date__gte=one_year_ago, is_coffee=True).count(),
        'coffee_closings': Business.objects.filter(close_date__gte=one_year_ago, is_coffee=True).count(),
    }

    # Business longevity (for closed businesses, excluding initial load)
    closed_businesses = Business.objects.filter(
        close_date__isnull=False
    ).exclude(
        open_date=date(2016, 3, 14)
    ).annotate(
        days_open=ExpressionWrapper(
            F('close_date') - F('open_date'),
            output_field=fields.DurationField()
        )
    )

    if closed_businesses.count() > 0:
        avg_days = sum([b.days_open.days for b in closed_businesses]) / closed_businesses.count()
        avg_longevity = {
            'days': round(avg_days, 1),
            'years': round(avg_days / 365.25, 2)
        }
    else:
        avg_longevity = None

    context = {
        'snapshot': snapshot,
        'yearly_data': yearly_data,
        'running_total': running_total,
        'eats_by_year': eats_by_year,
        'drinks_by_year': drinks_by_year,
        'coffee_by_year': coffee_by_year,
        'eats_closings_by_year': eats_closings_by_year,
        'drinks_closings_by_year': drinks_closings_by_year,
        'coffee_closings_by_year': coffee_closings_by_year,
        'districts_data': districts_data,
        'recent_trends': recent_trends,
        'avg_longevity': avg_longevity,
    }

    return render(request, 'stats.html', context)


def district_stats(request, district_id):
    """Generate statistics view for a specific district"""

    district = District.objects.get(id=district_id)

    # Current snapshot for this district
    snapshot = {
        'total_open': Business.objects.filter(district=district, close_date__isnull=True).count(),
        'total_closed': Business.objects.filter(district=district, close_date__isnull=False).count(),
        'eats_open': Business.objects.filter(district=district, close_date__isnull=True, is_eats=True).count(),
        'drinks_open': Business.objects.filter(district=district, close_date__isnull=True, is_drinks=True).count(),
        'coffee_open': Business.objects.filter(district=district, close_date__isnull=True, is_coffee=True).count(),
    }

    # Calculate net growth per year for this district
    years = range(2016, date.today().year + 1)
    yearly_data = []

    for year in years:
        # Exclude initial data load for openings in 2016
        if year == 2016:
            openings = Business.objects.filter(
                district=district,
                open_date__year=year
            ).exclude(open_date=date(2016, 3, 14)).count()
        else:
            openings = Business.objects.filter(
                district=district,
                open_date__year=year
            ).count()

        closings = Business.objects.filter(
            district=district,
            close_date__year=year
        ).count()
        net = openings - closings

        yearly_data.append({
            'year': year,
            'openings': openings,
            'closings': closings,
            'net_growth': net
        })

    # Running total of open businesses at end of each year
    running_total = []
    for year in years:
        year_end = date(year, 12, 31)

        open_at_year_end = Business.objects.filter(
            district=district,
            open_date__lte=year_end
        ).filter(
            Q(close_date__isnull=True) | Q(close_date__gt=year_end)
        ).count()

        running_total.append({
            'year': year,
            'open_businesses': open_at_year_end
        })

    # Openings by year by category (excluding initial load)
    eats_by_year = list(Business.objects
                        .filter(district=district, is_eats=True)
                        .exclude(open_date=date(2016, 3, 14))
                        .annotate(year=TruncYear('open_date'))
                        .values('year')
                        .annotate(count=Count('id'))
                        .order_by('year'))

    drinks_by_year = list(Business.objects
                          .filter(district=district, is_drinks=True)
                          .exclude(open_date=date(2016, 3, 14))
                          .annotate(year=TruncYear('open_date'))
                          .values('year')
                          .annotate(count=Count('id'))
                          .order_by('year'))

    coffee_by_year = list(Business.objects
                          .filter(district=district, is_coffee=True)
                          .exclude(open_date=date(2016, 3, 14))
                          .annotate(year=TruncYear('open_date'))
                          .values('year')
                          .annotate(count=Count('id'))
                          .order_by('year'))

    # Closings by year by category
    eats_closings_by_year = list(Business.objects
                                 .filter(district=district, is_eats=True, close_date__isnull=False)
                                 .annotate(year=TruncYear('close_date'))
                                 .values('year')
                                 .annotate(count=Count('id'))
                                 .order_by('year'))

    drinks_closings_by_year = list(Business.objects
                                   .filter(district=district, is_drinks=True, close_date__isnull=False)
                                   .annotate(year=TruncYear('close_date'))
                                   .values('year')
                                   .annotate(count=Count('id'))
                                   .order_by('year'))

    coffee_closings_by_year = list(Business.objects
                                   .filter(district=district, is_coffee=True, close_date__isnull=False)
                                   .annotate(year=TruncYear('close_date'))
                                   .values('year')
                                   .annotate(count=Count('id'))
                                   .order_by('year'))

    # Recent trends (last 12 months)
    one_year_ago = date.today() - timedelta(days=365)
    recent_trends = {
        'openings': Business.objects.filter(district=district, open_date__gte=one_year_ago).count(),
        'closings': Business.objects.filter(district=district, close_date__gte=one_year_ago).count(),
        'eats_openings': Business.objects.filter(district=district, open_date__gte=one_year_ago, is_eats=True).count(),
        'eats_closings': Business.objects.filter(district=district, close_date__gte=one_year_ago, is_eats=True).count(),
        'drinks_openings': Business.objects.filter(district=district, open_date__gte=one_year_ago,
                                                   is_drinks=True).count(),
        'drinks_closings': Business.objects.filter(district=district, close_date__gte=one_year_ago,
                                                   is_drinks=True).count(),
        'coffee_openings': Business.objects.filter(district=district, open_date__gte=one_year_ago,
                                                   is_coffee=True).count(),
        'coffee_closings': Business.objects.filter(district=district, close_date__gte=one_year_ago,
                                                   is_coffee=True).count(),
    }

    # Business longevity (for closed businesses in this district, excluding initial load)
    closed_businesses = Business.objects.filter(
        district=district,
        close_date__isnull=False
    ).exclude(
        open_date=date(2016, 3, 14)
    ).annotate(
        days_open=ExpressionWrapper(
            F('close_date') - F('open_date'),
            output_field=fields.DurationField()
        )
    )

    if closed_businesses.count() > 0:
        avg_days = sum([b.days_open.days for b in closed_businesses]) / closed_businesses.count()
        avg_longevity = {
            'days': round(avg_days, 1),
            'years': round(avg_days / 365.25, 2)
        }
    else:
        avg_longevity = None

    # List of all currently open businesses in this district
    open_businesses = Business.objects.filter(
        district=district,
        close_date__isnull=True
    ).order_by('name')

    # List of all closed businesses in this district
    closed_businesses_list = Business.objects.filter(
        district=district,
        close_date__isnull=False
    ).order_by('-close_date')

    context = {
        'district': district,
        'snapshot': snapshot,
        'yearly_data': yearly_data,
        'running_total': running_total,
        'eats_by_year': eats_by_year,
        'drinks_by_year': drinks_by_year,
        'coffee_by_year': coffee_by_year,
        'eats_closings_by_year': eats_closings_by_year,
        'drinks_closings_by_year': drinks_closings_by_year,
        'coffee_closings_by_year': coffee_closings_by_year,
        'recent_trends': recent_trends,
        'avg_longevity': avg_longevity,
        'open_businesses': open_businesses,
        'closed_businesses_list': closed_businesses_list,
    }

    return render(request, 'district_stats.html', context)