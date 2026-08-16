from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from ..models import FatorBaseTamanho, Orcamento


METROS_POR_MILIMETRO = Decimal("1000")


@dataclass(frozen=True)
class ResultadoCalculoOrcamento:
    area_m2: Decimal
    valor_total: Decimal
    valor_total_brl: str


class FatorBaseNaoConfiguradoError(Exception):
    pass


def formatar_brl(valor: Decimal) -> str:
    valor = valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    sinal = "-" if valor < 0 else ""
    valor_abs = abs(valor)
    inteiro, decimal = f"{valor_abs:.2f}".split(".")
    grupos = []

    while inteiro:
        grupos.append(inteiro[-3:])
        inteiro = inteiro[:-3]

    inteiro_formatado = ".".join(reversed(grupos)) or "0"
    return f"{sinal}R$ {inteiro_formatado},{decimal}"


def calcular_orcamento(*, base_mm: int, altura_mm: int, espessura_mm: int, preco_m2: Decimal, fator_base: Decimal) -> ResultadoCalculoOrcamento:
    base_m = Decimal(base_mm) / METROS_POR_MILIMETRO
    altura_m = Decimal(altura_mm) / METROS_POR_MILIMETRO
    area_m2 = base_m * altura_m
    valor_total = (area_m2 * Decimal(espessura_mm) * preco_m2 * fator_base).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    return ResultadoCalculoOrcamento(
        area_m2=area_m2.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP),
        valor_total=valor_total,
        valor_total_brl=formatar_brl(valor_total),
    )


def calcular_orcamento_catalogo(*, tamanho, espessura, material, tipo_base) -> ResultadoCalculoOrcamento:
    fator_relacao = obter_fator_base_por_tamanho(tipo_base=tipo_base, tamanho=tamanho)
    return calcular_orcamento(
        base_mm=tamanho.base_mm,
        altura_mm=tamanho.altura_mm,
        espessura_mm=espessura.milimetros,
        preco_m2=material.preco_m2,
        fator_base=fator_relacao.fator_base,
    )


def obter_fator_base_por_tamanho(*, tipo_base, tamanho) -> FatorBaseTamanho:
    try:
        return FatorBaseTamanho.objects.select_related("tipo_base", "tamanho").get(
            tipo_base=tipo_base,
            tamanho=tamanho,
        )
    except FatorBaseTamanho.DoesNotExist as exc:
        raise FatorBaseNaoConfiguradoError(
            "Não existe fator configurado para o tipo de base no tamanho selecionado."
        ) from exc


def montar_snapshot_orcamento(*, tamanho, espessura, material, tipo_base, resultado: ResultadoCalculoOrcamento, data_orcamento) -> dict:
    fator_relacao = obter_fator_base_por_tamanho(tipo_base=tipo_base, tamanho=tamanho)
    return {
        "data_orcamento": data_orcamento.isoformat(),
        "tamanho": {
            "id": tamanho.id,
            "nome": tamanho.nome,
            "base_mm": tamanho.base_mm,
            "altura_mm": tamanho.altura_mm,
        },
        "espessura": {
            "id": espessura.id,
            "milimetros": espessura.milimetros,
        },
        "material": {
            "id": material.id,
            "tipo": material.tipo,
            "preco_m2": f"{material.preco_m2:.2f}",
        },
        "tipo_base": {
            "id": tipo_base.id,
            "nome_base": tipo_base.nome_base,
            "fator_base": f"{fator_relacao.fator_base:.2f}",
            "fator_base_tamanho_id": fator_relacao.id,
        },
        "calculo": {
            "area_m2": f"{resultado.area_m2:.6f}",
            "valor_total": f"{resultado.valor_total:.2f}",
            "valor_total_brl": resultado.valor_total_brl,
        },
    }


def registrar_orcamento_calculado(*, nome_orcamento, data_orcamento, tamanho, espessura, material, tipo_base):
    resultado = calcular_orcamento_catalogo(
        tamanho=tamanho,
        espessura=espessura,
        material=material,
        tipo_base=tipo_base,
    )
    orcamento = Orcamento.objects.create(
        nome_orcamento=nome_orcamento,
        data_orcamento=data_orcamento,
        tamanho=tamanho,
        espessura=espessura,
        material=material,
        tipo_base=tipo_base,
        valor_total=resultado.valor_total,
        detalhes_json=montar_snapshot_orcamento(
            tamanho=tamanho,
            espessura=espessura,
            material=material,
            tipo_base=tipo_base,
            resultado=resultado,
            data_orcamento=data_orcamento,
        ),
    )
    return orcamento, resultado
