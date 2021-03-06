from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import Http404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

from .forms import SignUpForm
from .models import Products, Substitutes

IMG = 'https://authentic-visit.jp/wp-content/uploads/2017/12/gregoire-jeanneau-1451361.jpg'

def index(request):
    context = {
    "page_title" : "Accueil"
    }
    return render(request, 'openfoodfacts/index.html')


def search(request):
    query = request.GET.get('query')

    # query match product_name
    query_prod = Products.objects.filter(product_name__iexact=query).first()

    # query don't match exactly but can match product_name
    if not query_prod:
        query_prod = Products.objects.filter(product_name__icontains=query).first()

    # query doesn't match at all
    if not query_prod:
        raise Http404
    else:
        products_list = Products.objects.filter(category=query_prod.category)
        products_list = products_list.filter(nutriscore__lte=query_prod.nutriscore)
        products_list = products_list.order_by('nutriscore')
        products_list = products_list.exclude(pk=query_prod.id_product)


        if request.user.is_authenticated:
            # Remove products already in the user list
            for product in products_list:
                listed = Substitutes.objects.filter(
                    origin=query_prod.id_product,
                    replacement=product.id_product,
                    user=request.user
                    )
                if listed:
                    products_list = products_list.exclude(pk=product.id_product)

    # user want to save a product
    if request.user.is_authenticated and request.method == 'POST':
        origin = request.POST.get('origin')
        replacement = request.POST.get('replacement')

        origin = Products.objects.get(pk=origin)
        replacement = Products.objects.get(pk=replacement)

        Substitutes.objects.create(
            origin=origin,
            replacement=replacement,
            user=request.user
            )
        products_list = products_list.exclude(pk=replacement.id_product)

    # Slices pages
    paginator = Paginator(products_list, 9)
    page = request.GET.get('page')

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    context = {
        'products': products,
        'paginate': True,
        'query': query,
        'title': query_prod.product_name,
        'img': query_prod.img,
        'query_prod': query_prod.id_product,
        "page_title": "Résultats"
    }
    return render(request, 'openfoodfacts/search.html', context)


def detail(request, id_product):
    product = get_object_or_404(Products, pk=id_product)

    fat_index_img = ""
    saturated_fat_index_img = ""
    salt_index_img = ""
    sugar_index_img = ""
    url = "https://static.openfoodfacts.org/images/misc/"

    if product.fat:
        if product.fat < 3:
            fat_index_img = url + "low_30.png"
        elif 3 <= product.fat < 20:
            fat_index_img = url + "moderate_30.png"
        else:
            fat_index_img = url + "high_30.png"

    if product.saturated_fat:
        if product.saturated_fat < 1.5:
            saturated_fat_index_img = url + "low_30.png"
        elif 1.5 <= product.saturated_fat < 5:
            saturated_fat_index_img = url + "moderate_30.png"
        else:
            saturated_fat_index_img = url + "high_30.png"

    if product.salt:
        if product.salt < 0.3:
            salt_index_img = url + "low_30.png"
        elif 0.3 <= product.salt < 1.5:
            salt_index_img = url + "moderate_30.png"
        else:
            salt_index_img = url + "high_30.png"

    if product.sugar:
        if product.sugar < 5:
            sugar_index_img = url + "low_30.png"
        elif 5 <= product.sugar < 12.5:
            sugar_index_img = url + "moderate_30.png"
        else:
            sugar_index_img = url + "high_30.png"

    context = {
        "product": product.product_name,
        "img": product.img,
        "nutriscore": product.nutriscore,
        "fat": product.fat,
        "saturated_fat": product.saturated_fat,
        "salt": product.salt,
        "sugar": product.sugar,
        "fat_index_img": fat_index_img,
        "saturated_fat_index_img": saturated_fat_index_img,
        "salt_index_img": salt_index_img,
        "sugar_index_img": sugar_index_img,
        "redirection": product.url,
        "page_title" : product.product_name
    }
    return render(request, 'openfoodfacts/detail.html', context)


def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('/openfoodfacts/account')
    else:
        form = SignUpForm()

    context = {
        "form": form,
        "title": "S'enregistrer",
        "img": IMG,
        "page_title": "S'enregistrer"
    }
    return render(request, 'openfoodfacts/sign_up.html', context)


@login_required
def account(request):
    context = {
        "user": request.user,
        "img": IMG,
        "page_title": 'Votre compte'
    }
    return render(request, 'openfoodfacts/account.html', context)


def contacts(request):
    context = {
        "title": 'Contacts',
        "img": IMG,
        'page_title': 'Nous contacter'
        }
    return render(request, 'openfoodfacts/contacts.html', context)


def legals(request):
    context = {
        "title": "Mentions légales",
        "img": IMG,
        "page_title": "Mentions légales"
    }
    return render(request, 'openfoodfacts/legals.html', context)


@login_required
def saved(request):
    products_saved = Substitutes.objects.filter(user=request.user)

    if request.method == 'POST':
        origin = request.POST.get('origin')
        replacement = request.POST.get('replacement')

        origin = Products.objects.get(pk=origin)
        replacement = Products.objects.get(pk=replacement)

        Substitutes.objects.get(
            origin=origin,
            replacement=replacement,
            user=request.user
            ).delete()

    # Slices pages
    paginator = Paginator(products_saved, 5)
    page = request.GET.get('page')

    try:
        products_saved = paginator.page(page)
    except PageNotAnInteger:
        products_saved = paginator.page(1)
    except EmptyPage:
        products_saved = paginator.page(paginator.num_pages)


    context = {
        "title": "Vos aliments sauvegardés",
        "img": IMG,
        "products_saved": products_saved,
        "paginate": True,
        "page_title": "Vos aliments sauvegardés"
    }
    return render(request, 'openfoodfacts/saved.html', context)
