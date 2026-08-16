from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from base.models import Espessura, Material, Orcamento, Tamanho, TipoBase


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
            fator_base=Decimal("1.00"),
        )

    def login_staff(self):
        self.client.force_login(self.staff_user)

    def test_admin_routes_require_authentication(self):
        protected_urls = [
            reverse("admin_dashboard"),
            reverse("admin_tamanho_list"),
            reverse("admin_espessura_list"),
            reverse("admin_material_list"),
            reverse("admin_tipo_base_list"),
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
            reverse("admin_tamanho_list"),
            reverse("admin_espessura_list"),
            reverse("admin_material_list"),
            reverse("admin_tipo_base_list"),
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
