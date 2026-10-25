from django.urls import path
from . import views as v

urlpatterns = [
    path("health/", v.health),
    path("auth/csrf/", v.csrf),
    path("auth/login/", v.staff_login),
    path("auth/logout/", v.staff_logout),
    path("auth/me/", v.me),
    path("cards/", v.create_card),
    path("cards/current/", v.current_card),
    path("cards/history/", v.card_history),
    path("staff/lookup/", v.lookup),
    path("staff/purchase/", v.purchase),
    path("staff/redeem/", v.redeem),
    path("staff/operations/", v.operations),
    path("manager/summary/", v.summary),
    path("manager/staff/", v.staff_members),
    path("manager/staff/<int:user_id>/", v.staff_status),
    path("manager/branches/", v.branches),
    path("manager/operations/<uuid:operation_id>/reverse/", v.reverse),
]
