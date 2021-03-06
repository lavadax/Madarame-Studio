"""
Checkout page views for the madarame_studio project
"""
import json
import stripe
from django.shortcuts import (render, redirect, reverse,
                              get_object_or_404, HttpResponse)
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
from products.models import Product
from basket.contexts import basket_contents
from profiles.forms import UserProfileForm
from profiles.models import UserProfile
from .models import Order, OrderLineItem
from .forms import OrderForm, CheckOrderForm


def check_order(request):
    """
    A view for anonymous users to check order confirmations
    """
    if request.method == "POST":
        order_number = request.POST["order_number"]
        try:
            order = get_object_or_404(Order, order_number=order_number)
            messages.info(request, (
                f"This is a past confirmation for order number {order_number}."
                " A confirmation email was sent on the order date."
            ))
            template = "checkout/checkout_success.html"
            context = {
                "order": order,
                "anon": True,
            }
            return render(request, template, context)
        except Exception:
            messages.error(request, (
                        "That order number is not in our database.\
                Please check that the number matches the \
                order number in your email."))
            return redirect(reverse("check_order"))
    else:
        template = "checkout/check_order.html"
        form = CheckOrderForm()
        context = {
            "form": form,
        }
        return render(request, template, context)


@require_POST
def cache_checkout_data(request):
    """
    Send payment intent to Stripe or inform user of error
    """
    try:
        pid = request.POST.get("client_secret").split("_secret")[0]
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.PaymentIntent.modify(pid, metadata={
            "basket": json.dumps(request.session.get("basket", {})),
            "save_info": request.POST.get("save_info"),
            "username": request.user,
        })
        return HttpResponse(status=200)
    except Exception as error:
        messages.error(request, "Sorry, your payment cannot be \
            processed right now. Please try again later.")
        return HttpResponse(content=error, status=400)


def checkout(request):
    """
    Create new order from basket on POST, or show order summary on GET
    """
    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    stripe_secret_key = settings.STRIPE_SECRET_KEY

    if request.method == "POST":
        basket = request.session.get("basket", {})

        form_data = {
                "full_name": request.POST["full_name"],
                "email": request.POST["email"],
                "phone_number": request.POST["phone_number"],
                "address_line_1": request.POST["address_line_1"],
                "address_line_2": request.POST["address_line_2"],
                "town_city": request.POST["town_city"],
                "county_state": request.POST["county_state"],
                "zip_code": request.POST["zip_code"],
                "country": request.POST["country"],
            }
        order_form = OrderForm(form_data)
        if order_form.is_valid():
            order = order_form.save(commit=False)
            pid = request.POST.get("client_secret").split("_secret")[0]
            order.stripe_pid = pid
            order.original_basket = json.dumps(basket)
            order.save()
            for item_id, item_data in basket.items():
                try:
                    product = Product.objects.get(id=item_id)
                    if isinstance(item_data, int):
                        order_line_item = OrderLineItem(
                            order=order,
                            product=product,
                            quantity=item_data,
                        )
                        order_line_item.save()
                    else:
                        for size, quantity in item_data[
                                    "items_by_size"].items():
                            order_line_item = OrderLineItem(
                                order=order,
                                product=product,
                                quantity=quantity,
                                product_size=size,
                            )
                            order_line_item.save()
                except Product.DoesNotExist:
                    messages.error(request, (
                        "One of the products in your basket wasn't found \
                        in our database. "
                        "Please call us for assistance!")
                    )
                    order.delete()
                    return redirect(reverse("view_basket"))

            # Save the info to the user's profile if all is well
            request.session["save_info"] = "save-info" in request.POST
            return redirect(reverse("checkout_success", args=[
                order.order_number]))
        else:
            messages.error(request, "There was an error with your form. \
                Please double check your information.")
    else:
        basket = request.session.get("basket", {})
        if not basket:
            messages.error(request, "There's nothing in your basket \
                at the moment")
            return redirect(reverse("products"))

        current_basket = basket_contents(request)
        total = current_basket["grand_total"]
        stripe_total = round(total * 100)
        stripe.api_key = stripe_secret_key
        intent = stripe.PaymentIntent.create(
            amount=stripe_total,
            currency=settings.STRIPE_CURRENCY,
        )

        # Attempt to prefill the form with any info
        # the user maintains in their profile
        if request.user.is_authenticated:
            try:
                profile = UserProfile.objects.get(user=request.user)
                order_form = OrderForm(initial={
                    "full_name": profile.user.get_full_name(),
                    "email": profile.user.email,
                    "phone_number": profile.default_phone_number,
                    "country": profile.default_country,
                    "zip_code": profile.default_zip_code,
                    "town_city": profile.default_town_city,
                    "address_line_1": profile.default_address_line_1,
                    "address_line_2": profile.default_address_line_2,
                    "county_state": profile.default_county_state,
                })
            except UserProfile.DoesNotExist:
                order_form = OrderForm()
        else:
            order_form = OrderForm()
    if not stripe_public_key:
        messages.warning(request, "Stripe public key is missing. \
            Did you forget to set it in your environment?")

    template = "checkout/checkout.html"
    context = {
        "order_form": order_form,
        "stripe_public_key": stripe_public_key,
        "client_secret": intent.client_secret
    }

    return render(request, template, context)


def checkout_success(request, order_number):
    """
    Handle successful checkouts
    """
    save_info = request.session.get("save_info")
    order = get_object_or_404(Order, order_number=order_number)
    if request.user.is_authenticated:
        profile = UserProfile.objects.get(user=request.user)
        # Attach the user's profile to the order
        order.user_profile = profile
        order.save()

        # Save the user's info
        if save_info:
            profile_data = {
                'default_phone_number': order.phone_number,
                'default_country': order.country,
                'default_zip_code': order.zip_code,
                'default_town_city': order.town_city,
                'default_address_line_1': order.address_line_1,
                'default_address_line_2': order.address_line_2,
                'default_county_state': order.county_state,
            }
            user_profile_form = UserProfileForm(profile_data, instance=profile)
            if user_profile_form.is_valid():
                user_profile_form.save()

    messages.success(request, f"Order successfully processed! \
        Your order number is {order_number}. A confirmation \
        email will be sent to {order.email}.")

    if "basket" in request.session:
        del request.session["basket"]

    template = "checkout/checkout_success.html"
    context = {
        "order": order,
    }

    return render(request, template, context)
