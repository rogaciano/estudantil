from django.test import TestCase
from django.urls import reverse

from base.models import (
    DescontoQuantidade,
    Espessura,
    FatorBaseTamanho,
    Material,
    Orcamento,
    Tamanho,
    TipoBase,
)


class PublicOrcamentoFlowTests(TestCase):
    def setUp(self):
        self.tamanho_a4 = Tamanho.objects.create(
            nome="A4",
            base_mm=210,
            altura_mm=297,
        )
        self.tamanho_a3 = Tamanho.objects.create(
            nome="A3",
            base_mm=297,
            altura_mm=420,
        )
        self.espessura = Espessura.objects.create(milimetros=3)
        self.material = Material.objects.create(
            tipo="Acrílico Transparente",
            preco_m2="250.00",
        )
        self.tipo_base = TipoBase.objects.create(
            nome_base="Base Reforçada",
        )
        FatorBaseTamanho.objects.create(
            tipo_base=self.tipo_base,
            tamanho=self.tamanho_a4,
            fator_base="1.50",
        )
        FatorBaseTamanho.objects.create(
            tipo_base=self.tipo_base,
            tamanho=self.tamanho_a3,
            fator_base="1.80",
        )
        DescontoQuantidade.objects.create(
            quantidade_min=1,
            quantidade_max=10,
            fator_desconto="1.00",
        )
        DescontoQuantidade.objects.create(
            quantidade_min=11,
            quantidade_max=20,
            fator_desconto="0.95",
        )
        DescontoQuantidade.objects.create(
            quantidade_min=21,
            quantidade_max=None,
            fator_desconto="0.90",
        )
        self.payload = {
            "nome_orcamento": "Totem Recepção",
            "data_orcamento": "2026-08-15",
            "tamanho": str(self.tamanho_a4.id),
            "espessura": str(self.espessura.id),
            "material": str(self.material.id),
            "tipo_base": str(self.tipo_base.id),
            "quantidade": "1",
        }

    def test_home_configura_htmx_para_priorizar_estado_atual_do_formulario(self):
        response = self.client.get(reverse("public_home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'hx-sync="this:replace"', html=False)

    def test_calculo_htmx_retorna_total_formatado(self):
        response = self.client.post(
            reverse("public_orcamento_calcular"),
            data=self.payload,
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="resultado-orcamento"', html=False)
        self.assertContains(response, "R$ 70,17")
        self.assertContains(response, "Valor unitário na faixa")
        self.assertContains(response, "1 unidade")
        self.assertContains(response, "0,062370 m²")
        self.assertContains(response, "Salvar orçamento")

    def test_calculo_htmx_reflete_tamanho_atual_do_formulario(self):
        payload_a3 = {
            **self.payload,
            "tamanho": str(self.tamanho_a3.id),
        }

        response = self.client.post(
            reverse("public_orcamento_calcular"),
            data=payload_a3,
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "R$ 168,40")
        self.assertContains(response, "0,124740 m²")
        self.assertNotContains(response, "R$ 70,17")
        self.assertNotContains(response, "0,062370 m²")

    def test_calculo_htmx_aplica_desconto_por_faixa_e_mostra_proxima_faixa(self):
        payload_com_faixa = {
            **self.payload,
            "quantidade": "15",
        }

        response = self.client.post(
            reverse("public_orcamento_calcular"),
            data=payload_com_faixa,
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "15 unidades")
        self.assertContains(response, "11 a 20 unidades")
        self.assertContains(response, "R$ 66,66")
        self.assertContains(response, "R$ 999,90")
        self.assertContains(response, "Ao entrar na faixa")
        self.assertContains(response, "21+ unidades")
        self.assertContains(response, "R$ 63,15")

    def test_calculo_htmx_exibe_erros_amigaveis(self):
        response = self.client.post(
            reverse("public_orcamento_calcular"),
            data={"data_orcamento": "2026-08-15"},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Não foi possível processar o orçamento")
        self.assertContains(response, "Nome do orçamento")
        self.assertContains(response, "Tamanho")
        self.assertContains(response, "Espessura")
        self.assertContains(response, "Material")
        self.assertContains(response, "Tipo de base")
        self.assertContains(response, "Quantidade")

    def test_salvamento_htmx_persiste_orcamento_com_snapshot(self):
        response = self.client.post(
            reverse("public_orcamento_salvar"),
            data=self.payload,
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Orcamento.objects.count(), 1)

        orcamento = Orcamento.objects.get()
        self.assertEqual(orcamento.nome_orcamento, "Totem Recepção")
        self.assertEqual(str(orcamento.data_orcamento), "2026-08-15")
        self.assertEqual(orcamento.quantidade, 1)
        self.assertEqual(str(orcamento.valor_total), "70.17")
        self.assertEqual(
            orcamento.detalhes_json,
            {
                "data_orcamento": "2026-08-15",
                "tamanho": {
                    "id": self.tamanho_a4.id,
                    "nome": "A4",
                    "base_mm": 210,
                    "altura_mm": 297,
                },
                "espessura": {
                    "id": self.espessura.id,
                    "milimetros": 3,
                },
                "material": {
                    "id": self.material.id,
                    "tipo": "Acrílico Transparente",
                    "preco_m2": "250.00",
                },
                "tipo_base": {
                    "id": self.tipo_base.id,
                    "nome_base": "Base Reforçada",
                    "fator_base": "1.50",
                    "fator_base_tamanho_id": self.tipo_base.fatores_por_tamanho.get(
                        tamanho=self.tamanho_a4
                    ).id,
                },
                "quantidade": 1,
                "desconto_quantidade": {
                    "faixa": "1 a 10 unidades",
                    "fator_desconto": "1.00",
                    "percentual_desconto": "0.00",
                },
                "calculo": {
                    "area_m2": "0.062370",
                    "valor_unitario_base": "70.17",
                    "valor_unitario_base_brl": "R$ 70,17",
                    "valor_unitario_com_desconto": "70.17",
                    "valor_unitario_com_desconto_brl": "R$ 70,17",
                    "subtotal_sem_desconto": "70.17",
                    "subtotal_sem_desconto_brl": "R$ 70,17",
                    "valor_total": "70.17",
                    "valor_total_brl": "R$ 70,17",
                },
            },
        )
        self.assertContains(response, "registrado com sucesso")
        self.assertContains(response, "R$ 70,17")
