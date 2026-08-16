from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from .forms import (
    AdminAuthenticationForm,
    EspessuraForm,
    MaterialForm,
    OrcamentoPublicoForm,
    TamanhoForm,
    TipoBaseForm,
)
from .models import Espessura, Material, Tamanho, TipoBase
from .services.orcamentos import calcular_orcamento_catalogo, registrar_orcamento_calculado


def get_admin_sections():
    return [
        {
            "key": "tamanhos",
            "label": "Tamanhos",
            "description": "Dimensões disponíveis para cálculo.",
            "url_name": "admin_tamanho_list",
        },
        {
            "key": "espessuras",
            "label": "Espessuras",
            "description": "Camadas em milímetros usadas no orçamento.",
            "url_name": "admin_espessura_list",
        },
        {
            "key": "materiais",
            "label": "Materiais",
            "description": "Tabela de preço por metro quadrado.",
            "url_name": "admin_material_list",
        },
        {
            "key": "tipos-base",
            "label": "Tipos de base",
            "description": "Fatores multiplicadores aplicados ao total.",
            "url_name": "admin_tipo_base_list",
        },
    ]


class PublicHomeView(TemplateView):
    template_name = "public/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data_orcamento = timezone.localdate()
        context.update(
            {
                "data_orcamento": data_orcamento,
                "form": OrcamentoPublicoForm(
                    initial={"data_orcamento": data_orcamento}
                ),
            }
        )
        return context


class OrcamentoHtmxBaseView(View):
    template_name = "public/partials/orcamento_resultado.html"

    def render_resultado(self, request, *, form, resultado=None, orcamento=None):
        return render(
            request,
            self.template_name,
            {
                "form": form,
                "resultado": resultado,
                "orcamento": orcamento,
            },
        )


class OrcamentoCalcularView(OrcamentoHtmxBaseView):
    def post(self, request, *args, **kwargs):
        form = OrcamentoPublicoForm(request.POST)
        resultado = None
        if form.is_valid():
            resultado = calcular_orcamento_catalogo(
                tamanho=form.cleaned_data["tamanho"],
                espessura=form.cleaned_data["espessura"],
                material=form.cleaned_data["material"],
                tipo_base=form.cleaned_data["tipo_base"],
            )
        return self.render_resultado(request, form=form, resultado=resultado)


class OrcamentoSalvarView(OrcamentoHtmxBaseView):
    def post(self, request, *args, **kwargs):
        form = OrcamentoPublicoForm(request.POST)
        resultado = None
        orcamento = None
        if form.is_valid():
            orcamento, resultado = registrar_orcamento_calculado(
                nome_orcamento=form.cleaned_data["nome_orcamento"],
                data_orcamento=form.cleaned_data["data_orcamento"],
                tamanho=form.cleaned_data["tamanho"],
                espessura=form.cleaned_data["espessura"],
                material=form.cleaned_data["material"],
                tipo_base=form.cleaned_data["tipo_base"],
            )
        return self.render_resultado(
            request,
            form=form,
            resultado=resultado,
            orcamento=orcamento,
        )


class AdminStaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = "admin_login"

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(
                self.request,
                "Sua conta não tem permissão para acessar a área administrativa.",
            )
            return redirect("public_home")
        return super().handle_no_permission()


class AdminBaseContextMixin:
    section_key = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["admin_sections"] = get_admin_sections()
        context["current_section"] = self.section_key
        return context


class AdminLoginView(LoginView):
    template_name = "admin/login.html"
    authentication_form = AdminAuthenticationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.is_staff:
                return redirect(self.get_success_url())
            messages.error(
                request,
                "Sua conta autenticada não possui acesso administrativo.",
            )
            return redirect("public_home")
        return super().dispatch(request, *args, **kwargs)


class AdminLogoutView(LogoutView):
    next_page = "admin_login"


class AdminDashboardView(AdminStaffRequiredMixin, AdminBaseContextMixin, TemplateView):
    template_name = "admin/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cards"] = [
            {
                "label": "Tamanhos",
                "description": "Cadastre e ajuste dimensões das placas.",
                "count": Tamanho.objects.count(),
                "url_name": "admin_tamanho_list",
            },
            {
                "label": "Espessuras",
                "description": "Mantenha as opções de espessura usadas na fórmula.",
                "count": Espessura.objects.count(),
                "url_name": "admin_espessura_list",
            },
            {
                "label": "Materiais",
                "description": "Atualize os preços por metro quadrado.",
                "count": Material.objects.count(),
                "url_name": "admin_material_list",
            },
            {
                "label": "Tipos de base",
                "description": "Gerencie os fatores aplicados ao cálculo final.",
                "count": TipoBase.objects.count(),
                "url_name": "admin_tipo_base_list",
            },
        ]
        return context


class AdminCatalogMixin(AdminStaffRequiredMixin, AdminBaseContextMixin):
    resource_name_plural = ""
    resource_name_singular = ""
    section_key = ""
    list_url_name = ""
    create_url_name = ""
    edit_url_name = ""
    delete_url_name = ""

    def get_success_url(self):
        return reverse_lazy(self.list_url_name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "resource_name_plural": self.resource_name_plural,
                "resource_name_singular": self.resource_name_singular,
                "list_url_name": self.list_url_name,
                "create_url_name": self.create_url_name,
                "edit_url_name": self.edit_url_name,
                "delete_url_name": self.delete_url_name,
            }
        )
        return context


class AdminCatalogListView(AdminCatalogMixin, ListView):
    template_name = "admin/catalog_list.html"
    context_object_name = "objects"
    columns = []

    def get_table_rows(self):
        return [
            {
                "object": obj,
                "cells": self.get_row_cells(obj),
            }
            for obj in self.object_list
        ]

    def get_row_cells(self, obj):
        raise NotImplementedError

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["columns"] = self.columns
        context["rows"] = self.get_table_rows()
        return context


class AdminCatalogFormMixin(AdminCatalogMixin):
    template_name = "admin/catalog_form.html"
    submit_label = "Salvar"
    page_title = ""
    success_message = ""

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, self.success_message)
        return response

    def form_invalid(self, form):
        messages.error(
            self.request,
            "Revise os campos destacados e tente novamente.",
        )
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = self.page_title
        context["submit_label"] = self.submit_label
        return context


class AdminCatalogDeleteView(AdminCatalogMixin, DeleteView):
    template_name = "admin/catalog_confirm_delete.html"
    success_message = ""
    protected_message = ""

    def form_valid(self, form):
        object_label = str(self.object)
        try:
            response = super().form_valid(form)
        except ProtectedError:
            messages.error(self.request, self.protected_message)
            return redirect(self.get_success_url())

        messages.success(self.request, self.success_message.format(item=object_label))
        return response


class TamanhoListView(AdminCatalogListView):
    model = Tamanho
    resource_name_plural = "Tamanhos"
    resource_name_singular = "tamanho"
    section_key = "tamanhos"
    list_url_name = "admin_tamanho_list"
    create_url_name = "admin_tamanho_create"
    edit_url_name = "admin_tamanho_update"
    delete_url_name = "admin_tamanho_delete"
    columns = ["Nome", "Base", "Altura"]

    def get_row_cells(self, obj):
        return [obj.nome, f"{obj.base_mm} mm", f"{obj.altura_mm} mm"]


class TamanhoCreateView(AdminCatalogFormMixin, CreateView):
    model = Tamanho
    form_class = TamanhoForm
    resource_name_plural = "Tamanhos"
    resource_name_singular = "tamanho"
    section_key = "tamanhos"
    list_url_name = "admin_tamanho_list"
    create_url_name = "admin_tamanho_create"
    edit_url_name = "admin_tamanho_update"
    delete_url_name = "admin_tamanho_delete"
    page_title = "Novo tamanho"
    submit_label = "Criar tamanho"
    success_message = "Tamanho criado com sucesso."


class TamanhoUpdateView(AdminCatalogFormMixin, UpdateView):
    model = Tamanho
    form_class = TamanhoForm
    resource_name_plural = "Tamanhos"
    resource_name_singular = "tamanho"
    section_key = "tamanhos"
    list_url_name = "admin_tamanho_list"
    create_url_name = "admin_tamanho_create"
    edit_url_name = "admin_tamanho_update"
    delete_url_name = "admin_tamanho_delete"
    page_title = "Editar tamanho"
    submit_label = "Salvar alterações"
    success_message = "Tamanho atualizado com sucesso."


class TamanhoDeleteView(AdminCatalogDeleteView):
    model = Tamanho
    resource_name_plural = "Tamanhos"
    resource_name_singular = "tamanho"
    section_key = "tamanhos"
    list_url_name = "admin_tamanho_list"
    create_url_name = "admin_tamanho_create"
    edit_url_name = "admin_tamanho_update"
    delete_url_name = "admin_tamanho_delete"
    success_message = "Tamanho \"{item}\" excluído com sucesso."
    protected_message = (
        "Este tamanho está vinculado a orçamentos e não pode ser excluído."
    )


class EspessuraListView(AdminCatalogListView):
    model = Espessura
    resource_name_plural = "Espessuras"
    resource_name_singular = "espessura"
    section_key = "espessuras"
    list_url_name = "admin_espessura_list"
    create_url_name = "admin_espessura_create"
    edit_url_name = "admin_espessura_update"
    delete_url_name = "admin_espessura_delete"
    columns = ["Espessura"]

    def get_row_cells(self, obj):
        return [f"{obj.milimetros} mm"]


class EspessuraCreateView(AdminCatalogFormMixin, CreateView):
    model = Espessura
    form_class = EspessuraForm
    resource_name_plural = "Espessuras"
    resource_name_singular = "espessura"
    section_key = "espessuras"
    list_url_name = "admin_espessura_list"
    create_url_name = "admin_espessura_create"
    edit_url_name = "admin_espessura_update"
    delete_url_name = "admin_espessura_delete"
    page_title = "Nova espessura"
    submit_label = "Criar espessura"
    success_message = "Espessura criada com sucesso."


class EspessuraUpdateView(AdminCatalogFormMixin, UpdateView):
    model = Espessura
    form_class = EspessuraForm
    resource_name_plural = "Espessuras"
    resource_name_singular = "espessura"
    section_key = "espessuras"
    list_url_name = "admin_espessura_list"
    create_url_name = "admin_espessura_create"
    edit_url_name = "admin_espessura_update"
    delete_url_name = "admin_espessura_delete"
    page_title = "Editar espessura"
    submit_label = "Salvar alterações"
    success_message = "Espessura atualizada com sucesso."


class EspessuraDeleteView(AdminCatalogDeleteView):
    model = Espessura
    resource_name_plural = "Espessuras"
    resource_name_singular = "espessura"
    section_key = "espessuras"
    list_url_name = "admin_espessura_list"
    create_url_name = "admin_espessura_create"
    edit_url_name = "admin_espessura_update"
    delete_url_name = "admin_espessura_delete"
    success_message = "Espessura \"{item}\" excluída com sucesso."
    protected_message = (
        "Esta espessura está vinculada a orçamentos e não pode ser excluída."
    )


class MaterialListView(AdminCatalogListView):
    model = Material
    resource_name_plural = "Materiais"
    resource_name_singular = "material"
    section_key = "materiais"
    list_url_name = "admin_material_list"
    create_url_name = "admin_material_create"
    edit_url_name = "admin_material_update"
    delete_url_name = "admin_material_delete"
    columns = ["Material", "Preço por m²"]

    def get_row_cells(self, obj):
        return [obj.tipo, f"R$ {obj.preco_m2:.2f}".replace(".", ",")]


class MaterialCreateView(AdminCatalogFormMixin, CreateView):
    model = Material
    form_class = MaterialForm
    resource_name_plural = "Materiais"
    resource_name_singular = "material"
    section_key = "materiais"
    list_url_name = "admin_material_list"
    create_url_name = "admin_material_create"
    edit_url_name = "admin_material_update"
    delete_url_name = "admin_material_delete"
    page_title = "Novo material"
    submit_label = "Criar material"
    success_message = "Material criado com sucesso."


class MaterialUpdateView(AdminCatalogFormMixin, UpdateView):
    model = Material
    form_class = MaterialForm
    resource_name_plural = "Materiais"
    resource_name_singular = "material"
    section_key = "materiais"
    list_url_name = "admin_material_list"
    create_url_name = "admin_material_create"
    edit_url_name = "admin_material_update"
    delete_url_name = "admin_material_delete"
    page_title = "Editar material"
    submit_label = "Salvar alterações"
    success_message = "Material atualizado com sucesso."


class MaterialDeleteView(AdminCatalogDeleteView):
    model = Material
    resource_name_plural = "Materiais"
    resource_name_singular = "material"
    section_key = "materiais"
    list_url_name = "admin_material_list"
    create_url_name = "admin_material_create"
    edit_url_name = "admin_material_update"
    delete_url_name = "admin_material_delete"
    success_message = "Material \"{item}\" excluído com sucesso."
    protected_message = (
        "Este material está vinculado a orçamentos e não pode ser excluído."
    )


class TipoBaseListView(AdminCatalogListView):
    model = TipoBase
    resource_name_plural = "Tipos de base"
    resource_name_singular = "tipo de base"
    section_key = "tipos-base"
    list_url_name = "admin_tipo_base_list"
    create_url_name = "admin_tipo_base_create"
    edit_url_name = "admin_tipo_base_update"
    delete_url_name = "admin_tipo_base_delete"
    columns = ["Tipo de base", "Fator"]

    def get_row_cells(self, obj):
        return [obj.nome_base, f"{obj.fator_base:.2f}".replace(".", ",")]


class TipoBaseCreateView(AdminCatalogFormMixin, CreateView):
    model = TipoBase
    form_class = TipoBaseForm
    resource_name_plural = "Tipos de base"
    resource_name_singular = "tipo de base"
    section_key = "tipos-base"
    list_url_name = "admin_tipo_base_list"
    create_url_name = "admin_tipo_base_create"
    edit_url_name = "admin_tipo_base_update"
    delete_url_name = "admin_tipo_base_delete"
    page_title = "Novo tipo de base"
    submit_label = "Criar tipo de base"
    success_message = "Tipo de base criado com sucesso."


class TipoBaseUpdateView(AdminCatalogFormMixin, UpdateView):
    model = TipoBase
    form_class = TipoBaseForm
    resource_name_plural = "Tipos de base"
    resource_name_singular = "tipo de base"
    section_key = "tipos-base"
    list_url_name = "admin_tipo_base_list"
    create_url_name = "admin_tipo_base_create"
    edit_url_name = "admin_tipo_base_update"
    delete_url_name = "admin_tipo_base_delete"
    page_title = "Editar tipo de base"
    submit_label = "Salvar alterações"
    success_message = "Tipo de base atualizado com sucesso."


class TipoBaseDeleteView(AdminCatalogDeleteView):
    model = TipoBase
    resource_name_plural = "Tipos de base"
    resource_name_singular = "tipo de base"
    section_key = "tipos-base"
    list_url_name = "admin_tipo_base_list"
    create_url_name = "admin_tipo_base_create"
    edit_url_name = "admin_tipo_base_update"
    delete_url_name = "admin_tipo_base_delete"
    success_message = "Tipo de base \"{item}\" excluído com sucesso."
    protected_message = (
        "Este tipo de base está vinculado a orçamentos e não pode ser excluído."
    )
