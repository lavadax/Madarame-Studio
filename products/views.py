"""
Product oriented views for madarame_studio project
"""
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib import messages
from django.db.models import Q
from .models import Product
from .forms import ProductForm

# Create your views here.


def all_products(request):
    """ A view to show all products, including sorting and search queries """

    products = Product.objects.all()
    query = None
    sort = None
    direction = None

    if request.GET:

        if "sort" in request.GET:
            sortkey = request.GET["sort"]
            sort = sortkey
            if sortkey == "price":
                sortkey = "base_price"

            if "direction" in request.GET:
                direction = request.GET["direction"]
                if direction == "desc":
                    sortkey = f"-{sortkey}"
            products = products.order_by(sortkey)

        if "query" in request.GET:
            query = request.GET["query"]
            if not query:
                messages.error(
                    request, "You didn't enter any search criteria!")
                return redirect(reverse("products"))

            queries = Q(
                image_url__icontains=query) | Q(artist__icontains=query)
            products = products.filter(queries)

    current_sorting = f"{sort}_{direction}"

    context = {
        "products": products,
        "query": query,
        "sorting": current_sorting,
    }

    return render(request, "products/products.html", context)


def product_detail(request, product_id):
    """ A view to show individual product details """

    product = get_object_or_404(Product, pk=product_id)

    context = {
        "product": product,
    }

    return render(request, "products/product_detail.html", context)


def add_product(request):
    """ Add a product to the store """
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully added product!")
            return redirect(reverse("add_product"))
        else:
            messages.error(request, "Failed to add product. \
                           Please ensure the form is valid.")
    else:
        form = ProductForm()

    template = "products/add_product.html"
    context = {
        "form": form,
    }

    return render(request, template, context)


def edit_product(request, product_id):
    """ Edit a product in the store """
    product = get_object_or_404(Product, pk=product_id)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully updated product!")
            return redirect(reverse("product_detail", args=[product.id]))
        else:
            messages.error(request, "Failed to update product.\
                                     Please ensure the form is valid.")
    else:
        form = ProductForm(instance=product)
        messages.info(request, f"You are editing {product.sku}")

    template = "products/edit_product.html"
    context = {
        "form": form,
        "product": product,
    }

    return render(request, template, context)
