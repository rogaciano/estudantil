from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from base.models import (
    DescontoQuantidade,
    Espessura,
    FatorBaseTamanho,
    Material,
    Orcamento,
    Tamanho,
    TipoBase,
)


class AdminViewsTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.staff_user = user_model.objects.create_user(
            username="admin",
            password="senha-forte-123",
            is_staff=True,
        )
        self.regular_user = user_model.objects.create_user(
            username="visitante",
            password="senha-forte-123",
        )
        self.tamanho = Tamanho.objects.create(nome="A4", base_mm=210, altura_mm=297)
        self.espessura = Espessura.objects.create(milimetros=3)
        self.material = Material.objects.create(
            tipo="Acrílico Transparente",
            preco_m2=Decimal("250.00"),
        )
        self.tipo_base = TipoBase.objects.create(
            nome_base="Base Simples",
        )
        self.fator_base_tamanho = FatorBaseTamanho.objects.create(
            tipo_base=self.tipo_base,
            tamanho=self.tamanho,
            fator_base=Decimal("1.00"),
        )
        self.desconto = DescontoQuantidade.objects.create(
            quantidade_min=1,
            quantidade_max=10,
            fator_desconto=Decimal("1.00"),
        )

    def login_staff(self):
        self.client.force_login(self.staff_user)

    def test_admin_routes_require_authentication(self):
        protected_urls = [
            reverse("admin_dashboard"),
            reverse("admin_orcamento_list"),
            reverse("admin_tamanho_list"),
            reverse("admin_espessura_list"),
            reverse("admin_material_list"),
            reverse("admin_tipo_base_list"),
            reverse("admin_fator_base_tamanho_list"),
            reverse("admin_desconto_quantidade_list"),
        ]

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(
                    response,
                    f"{reverse('admin_login')}?next={url}",
                )

    def test_admin_login_rejects_non_staff_user(self):
        response = self.client.post(
            reverse("admin_login"),
            {"username": "visitante", "password": "senha-forte-123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Somente usuários administradores podem acessar esta área.",
        )

    def test_staff_user_can_access_dashboard_and_catalogs(self):
        self.login_staff()

        urls = [
            reverse("admin_dashboard"),
            reverse("admin_orcamento_list"),
            reverse("admin_tamanho_list"),
            reverse("admin_espessura_list"),
            reverse("admin_material_list"),
            reverse("admin_tipo_base_list"),
            reverse("admin_fator_base_tamanho_list"),
            reverse("admin_desconto_quantidade_list"),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_staff_user_can_create_update_and_delete_tamanho(self):
        self.login_staff()

        create_response = self.client.post(
            reverse("admin_tamanho_create"),
            {"nome": "A3", "base_mm": 297, "altura_mm": 420},
            follow=True,
        )
        self.assertContains(create_response, "Tamanho criado com sucesso.")
        novo_tamanho = Tamanho.objects.get(nome="A3")
        self.assertEqual(novo_tamanho.base_mm, 297)

        update_response = self.client.post(
            reverse("admin_tamanho_update", args=[novo_tamanho.pk]),
            {"nome": "A3 revisado", "base_mm": 300, "altura_mm": 420},
            follow=True,
        )
        self.assertContains(update_response, "Tamanho atualizado com sucesso.")
        novo_tamanho.refresh_from_db()
        self.assertEqual(novo_tamanho.nome, "A3 revisado")
        self.assertEqual(novo_tamanho.base_mm, 300)

        delete_response = self.client.post(
            reverse("admin_tamanho_delete", args=[novo_tamanho.pk]),
            follow=True,
        )
        self.assertContains(delete_response, "excluído com sucesso")
        self.assertFalse(Tamanho.objects.filter(pk=novo_tamanho.pk).exists())

    def test_delete_protected_catalog_entry_shows_error_message(self):
        self.login_staff()
        Orcamento.objects.create(
            nome_orcamento="Totem recepção",
            data_orcamento=timezone.localdate(),
            tamanho=self.tamanho,
            espessura=self.espessura,
            material=self.material,
            tipo_base=self.tipo_base,
            quantidade=1,
            valor_total=Decimal("70.17"),
            detalhes_json={"snapshot": True},
        )

        response = self.client.post(
            reverse("admin_material_delete", args=[self.material.pk]),
            follow=True,
        )

        self.assertContains(
            response,
            "Este material está vinculado a orçamentos e não pode ser excluído.",
        )
        self.assertTrue(Material.objects.filter(pk=self.material.pk).exists())

    def test_staff_user_can_manage_fator_base_por_tamanho(self):
        self.login_staff()
        novo_tamanho = Tamanho.objects.create(nome="A3", base_mm=297, altura_mm=420)

        create_response = self.client.post(
            reverse("admin_fator_base_tamanho_create"),
            {
                "tipo_base": self.tipo_base.pk,
                "tamanho": novo_tamanho.pk,
                "fator_base": "1.35",
            },
            follow=True,
        )
        self.assertContains(create_response, "Fator por tamanho criado com sucesso.")
        fator = FatorBaseTamanho.objects.get(tipo_base=self.tipo_base, tamanho=novo_tamanho)
        self.assertEqual(fator.fator_base, Decimal("1.35"))

        update_response = self.client.post(
            reverse("admin_fator_base_tamanho_update", args=[fator.pk]),
            {
                "tipo_base": self.tipo_base.pk,
                "tamanho": novo_tamanho.pk,
                "fator_base": "1.40",
            },
            follow=True,
        )
        self.assertContains(update_response, "Fator por tamanho atualizado com sucesso.")
        fator.refresh_from_db()
        self.assertEqual(fator.fator_base, Decimal("1.40"))

    def test_staff_user_can_manage_desconto_por_quantidade(self):
        self.login_staff()

        create_response = self.client.post(
            reverse("admin_desconto_quantidade_create"),
            {
                "quantidade_min": 31,
                "quantidade_max": 40,
                "fator_desconto": "0.88",
            },
            follow=True,
        )
        self.assertContains(create_response, "Desconto por quantidade criado com sucesso.")
        desconto = DescontoQuantidade.objects.get(quantidade_min=31, quantidade_max=40)
        self.assertEqual(desconto.fator_desconto, Decimal("0.88"))

        update_response = self.client.post(
            reverse("admin_desconto_quantidade_update", args=[desconto.pk]),
            {
                "quantidade_min": 31,
                "quantidade_max": 45,
                "fator_desconto": "0.93",
            },
            follow=True,
        )
        self.assertContains(update_response, "Desconto por quantidade atualizado com sucesso.")
        desconto.refresh_from_db()
        self.assertEqual(desconto.quantidade_max, 45)
        self.assertEqual(desconto.fator_desconto, Decimal("0.93"))

    def test_admin_orcamentos_list_supports_filter(self):
        self.login_staff()
        Orcamento.objects.create(
            nome_orcamento="Totem Recepção",
            data_orcamento=timezone.localdate(),
            tamanho=self.tamanho,
            espessura=self.espessura,
            material=self.material,
            tipo_base=self.tipo_base,
            quantidade=1,
            valor_total=Decimal("70.17"),
            detalhes_json={
                "calculo": {"valor_total_brl": "R$ 70,17"},
                "desconto_quantidade": {"faixa": "1 a 10 unidades"},
            },
        )
        Orcamento.objects.create(
            nome_orcamento="Display de Mesa",
            data_orcamento=timezone.localdate(),
            tamanho=self.tamanho,
            espessura=self.espessura,
            material=self.material,
            tipo_base=self.tipo_base,
            quantidade=2,
            valor_total=Decimal("140.34"),
            detalhes_json={
                "calculo": {"valor_total_brl": "R$ 140,34"},
                "desconto_quantidade": {"faixa": "1 a 10 unidades"},
            },
        )

        response = self.client.get(reverse("admin_orcamento_list"), {"q": "Recepção"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Totem Recepção")
        self.assertNotContains(response, "Display de Mesa")
        self.assertContains(response, 'value="Recepção"', html=False)

    def test_admin_orcamentos_list_supports_pagination(self):
        self.login_staff()
        for index in range(15):
            Orcamento.objects.create(
                nome_orcamento=f"Orçamento {index:02d}",
                data_orcamento=timezone.localdate(),
                tamanho=self.tamanho,
                espessura=self.espessura,
                material=self.material,
                tipo_base=self.tipo_base,
                quantidade=1,
                valor_total=Decimal("70.17"),
                detalhes_json={
                    "calculo": {"valor_total_brl": "R$ 70,17"},
                    "desconto_quantidade": {"faixa": "1 a 10 unidades"},
                },
            )

        first_page = self.client.get(reverse("admin_orcamento_list"))
        second_page = self.client.get(reverse("admin_orcamento_list"), {"page": 2})

        self.assertContains(first_page, "Página 1 de 2")
        self.assertContains(first_page, "Orçamento 14")
        self.assertContains(first_page, "Orçamento 03")
        self.assertNotContains(first_page, "Orçamento 02")

        self.assertContains(second_page, "Página 2 de 2")
        self.assertContains(second_page, "Orçamento 02")
        self.assertContains(second_page, "Orçamento 00")
