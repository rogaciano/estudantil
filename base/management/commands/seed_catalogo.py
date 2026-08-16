from decimal import Decimal

from django.core.management.base import BaseCommand

from base.models import (
    DescontoQuantidade,
    Espessura,
    FatorBaseTamanho,
    Material,
    Tamanho,
    TipoBase,
)


class Command(BaseCommand):
    help = "Popula o catalogo inicial de tamanhos, espessuras, materiais e bases."

    def handle(self, *args, **options):
        tamanhos = [
            {"nome": "A6", "base_mm": 105, "altura_mm": 148},
            {"nome": "A5", "base_mm": 148, "altura_mm": 210},
            {"nome": "A4", "base_mm": 210, "altura_mm": 297},
            {"nome": "A3", "base_mm": 297, "altura_mm": 420},
        ]
        espessuras = [2, 3, 4]
        materiais = [
            {"tipo": "Acrílico Transparente", "preco_m2": Decimal("250.00")},
            {"tipo": "Acrílico de Cor", "preco_m2": Decimal("300.00")},
        ]
        tipos_bases = [
            {"nome_base": "Base Simples", "fator_padrao": Decimal("1.00")},
            {"nome_base": "Base Reforçada", "fator_padrao": Decimal("1.50")},
        ]
        descontos_quantidade = [
            {"quantidade_min": 1, "quantidade_max": 10, "fator_desconto": Decimal("1.00")},
            {"quantidade_min": 11, "quantidade_max": 20, "fator_desconto": Decimal("0.95")},
            {"quantidade_min": 21, "quantidade_max": None, "fator_desconto": Decimal("0.90")},
        ]

        for tamanho in tamanhos:
            Tamanho.objects.update_or_create(nome=tamanho["nome"], defaults=tamanho)

        for milimetros in espessuras:
            Espessura.objects.update_or_create(milimetros=milimetros)

        for material in materiais:
            Material.objects.update_or_create(tipo=material["tipo"], defaults=material)

        for tipo_base in tipos_bases:
            tipo_base_obj, _ = TipoBase.objects.update_or_create(
                nome_base=tipo_base["nome_base"],
            )
            for tamanho_obj in Tamanho.objects.all():
                FatorBaseTamanho.objects.update_or_create(
                    tipo_base=tipo_base_obj,
                    tamanho=tamanho_obj,
                    defaults={"fator_base": tipo_base["fator_padrao"]},
                )

        for desconto in descontos_quantidade:
            DescontoQuantidade.objects.update_or_create(
                quantidade_min=desconto["quantidade_min"],
                quantidade_max=desconto["quantidade_max"],
                defaults={"fator_desconto": desconto["fator_desconto"]},
            )

        self.stdout.write(self.style.SUCCESS("Catalogo inicial populado com sucesso."))
