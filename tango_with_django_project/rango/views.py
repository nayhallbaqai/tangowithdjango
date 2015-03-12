from django.shortcuts import render

from rango.models import Category
from rango.models import Page
from rango.models import UserProfile
from django.contrib.auth.models import User

from rango.forms import CategoryForm
from rango.forms import PageForm
from rango.forms import UserForm, UserProfileForm
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from datetime import datetime
from rango.bing_search import run_query
from django.shortcuts import redirect


def index(request):
    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]

    context_dict = {'categories': category_list, 'pages': page_list}

    visits = request.session.get('visits')
    if not visits:
        visits = 1
    reset_last_visit_time = False

    last_visit = request.session.get('last_visit')
    if last_visit:
        last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")

        if (datetime.now() - last_visit_time).seconds > 0:
            # ...reassign the value of the cookie to +1 of what it was before...
            visits = visits + 1
            # ...and update the last visit cookie, too.
            reset_last_visit_time = True
    else:
        # Cookie last_visit doesn't exist, so create it to the current date/time.
        reset_last_visit_time = True

    if reset_last_visit_time:
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = visits
    context_dict['visits'] = visits

    response = render(request, 'rango/index.html', context_dict)

    return response


def about(request):
    context_dict = {}
    if request.session.get('visits'):
        visits = request.session.get('visits')
    else:
        visits = 0
    context_dict['boldname'] = "Mohammed Nayhall Baqai, 2086029B"
    context_dict['visits'] = visits
    return render(request, 'rango/about.html', context_dict)


def category(request, category_name_slug):
    # Create a context dictionary which we can pass to the template rendering engine.
    context_dict = {}
    context_dict['result_list'] = None
    context_dict['query'] = None
    if request.method == 'POST':
        query = request.POST['query'].strip()
        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)
            context_dict['result_list'] = result_list
            context_dict['query'] = query

    try:
        # Can we find a category name slug with the given name?
        # If we can't, the .get() method raises a DoesNotExist exception.
        # So the .get() method returns one model instance or raises an exception.
        category = Category.objects.get(slug=category_name_slug)
        context_dict['category_name'] = category.name

        context_dict['category_name_slug'] = category_name_slug
        # Retrieve all of the associated pages.
        # Note that filter returns >= 1 model instance.
        pages = Page.objects.filter(category=category).order_by('-views')

        # Adds our results list to the template context under name pages.
        context_dict['pages'] = pages
        # We also add the category object from the database to the context dictionary.
        # We'll use this in the template to verify that the category exists.
        context_dict['category'] = category
    except Category.DoesNotExist:
        # We get here if we didn't find the specified category.
        # Don't do anything - the template displays the "no category" message for us.
        pass

    if not context_dict['query']:
        context_dict['query'] = category.name

    # Go render the response and return it to the client.
    return render(request, 'rango/category.html', context_dict)


@login_required
def add_category(request):
    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Have we been provided with a valid form?
        if form.is_valid():
            # Save the new category to the database.
            form.save(commit=True)

            # Now call the index() view.
            # The user will be shown the homepage.
            return index(request)
        else:
            # The supplied form contained errors - just print them to the terminal.
            print form.errors
    else:
        # If the request was not a POST, display the form to enter details.
        form = CategoryForm()

    # Bad form (or form details), no form supplied...
    # Render the form with error messages (if any).
    return render(request, 'rango/add_category.html', {'form': form})


@login_required
def add_page(request, category_name_slug):
    try:
        cat = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        cat = None

    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            if cat:
                page = form.save(commit=False)
                page.category = cat
                page.views = 0
                page.save()
                # probably better to use a redirect here.
                return category(request, category_name_slug)
        else:
            print form.errors
    else:
        form = PageForm()

    context_dict = {'form': form, 'category': cat}

    return render(request, 'rango/add_page.html', context_dict)


@login_required
def restricted(request):
    return render(request, 'rango/restricted.html')


def search(request):
    result_list = []
    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)

    return render(request, 'rango/search.html', {'result_list': result_list})


def track_url(request):
    page_id = None
    url = '/rango/'
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                page = Page.objects.get(id=page_id)
                page.views += 1
                page.save()
                url = page.url
            except:
                pass
    return redirect(url)


def profile(request, username):
    context_dict = {}
    user = User.objects.get(username=username)
    profile = UserProfile.objects.get(user=user)
    context_dict['user_name'] = user.username
    context_dict['user_email'] = user.email
    context_dict['userprofile'] = profile
    return render(request, 'rango/profile.html', context_dict)

def search_users(request):
    user_name = UserProfile.objects.all()
    return render(request, 'rango/search_users.html', {'users': user_name})

def register_profile(request):
    if request.method == 'POST':
        user_profile_form = UserProfileForm(request.POST)
        if user_profile_form.is_valid():
            if request.user.is_authenticated():
                user_profile = user_profile_form.save(commit = False)
                user = User.objects.get(id=request.user.id)
                user_profile.user = request.user
            if 'picture' in request.FILES:
                user_profile.picture = request.FILES['picture']
                user_profile.website = user_profile_form.cleaned_data['website']
                user_profile.save()
            return redirect('/rango/')
    else:
        user_profile_form = UserProfileForm()
    return render(request,'rango/profile_registration.html', {'profile_form': user_profile_form})

@login_required
def edit_profile(request):
    context_dict = {}
    if request.method == 'POST':
        user_profile_form = UserProfileForm(data=request.POST, instance=request.user.userprofile)
        if user_profile_form.is_valid():
            if request.user.is_authenticated():
                user_profile = UserProfile.objects.get(user_id=request.user.id)
                if 'picture' in request.FILES:
                    user_profile.picture = request.FILES['picture']
                if 'website' in user_profile_form.cleaned_data:
                    user_profile.website = user_profile_form.cleaned_data['website']

                user_profile.save()

            profile = UserProfile.objects.get(user=request.user)
            context_dict['user_name'] = request.user.username
            context_dict['user_email'] = request.user.email
            context_dict['userprofile'] = profile
            return render(request, 'rango/profile.html', context_dict)
    else:
        user_profile_form = UserProfileForm(instance=request.user.userprofile)
    return render(request,'rango/edit_profile.html',{'profile_form':user_profile_form})
