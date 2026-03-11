from django.shortcuts import resolve_url
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class NextUrlRedirectMixin:
    def get_success_url(self):
        next_url = (
                self.request.POST.get("next")
                or self.request.GET.get("next")
        )

        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url

        return resolve_url(self.success_url)


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return self.request.user.is_staff
