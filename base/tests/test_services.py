from decimal import Decimal

from django.test import SimpleTestCase

from base.services.orcamentos import calcular_orcamento, formatar_brl


class OrcamentoServiceTests(SimpleTestCase):
    def test_calcula_valor_total_convertendo_mm_para_metros(self):
        resultado = calcular_orcamento(
            base_mm=210,
            altura_mm=297,
            espessura_mm=3,
            preco_m2=Decimal("250.00"),
            fator_base=Decimal("1.50"),
        )

        self.assertEqual(resultado.area_m2, Decimal("0.062370"))
        self.assertEqual(resultado.valor_total, Decimal("70.17"))
        self.assertEqual(resultado.valor_total_brl, "R$ 70,17")

    def test_formata_valor_em_brl_com_milhar_e_centavos(self):
        self.assertEqual(formatar_brl(Decimal("1234.5")), "R$ 1.234,50")
