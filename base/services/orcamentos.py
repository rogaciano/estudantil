from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from ..models import DescontoQuantidade, FatorBaseTamanho, Orcamento


METROS_POR_MILIMETRO = Decimal("1000")


@dataclass(frozen=True)
class ResultadoCalculoOrcamento:
    area_m2: Decimal
    quantidade: int
    valor_unitario_base: Decimal
    valor_unitario_base_brl: str
    valor_unitario_com_desconto: Decimal
    valor_unitario_com_desconto_brl: str
    subtotal_sem_desconto: Decimal
    subtotal_sem_desconto_brl: str
    fator_desconto: Decimal
    percentual_desconto: Decimal
    faixa_desconto_label: str
    valor_total: Decimal
    valor_total_brl: str
    proxima_faixa_label: str | None = None
    proximo_valor_unitario_brl: str | None = None


class FatorBaseNaoConfiguradoError(Exception):
    pass


class DescontoQuantidadeNaoConfiguradoError(Exception):
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
    valor_unitario_base = (area_m2 * Decimal(espessura_mm) * preco_m2 * fator_base).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    return ResultadoCalculoOrcamento(
        area_m2=area_m2.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP),
        quantidade=1,
        valor_unitario_base=valor_unitario_base,
        valor_unitario_base_brl=formatar_brl(valor_unitario_base),
        valor_unitario_com_desconto=valor_unitario_base,
        valor_unitario_com_desconto_brl=formatar_brl(valor_unitario_base),
        subtotal_sem_desconto=valor_unitario_base,
        subtotal_sem_desconto_brl=formatar_brl(valor_unitario_base),
        fator_desconto=Decimal("1.00"),
        percentual_desconto=Decimal("0.00"),
        faixa_desconto_label="1 unidade",
        valor_total=valor_unitario_base,
        valor_total_brl=formatar_brl(valor_unitario_base),
    )


def calcular_orcamento_com_quantidade(
    *,
    base_mm: int,
    altura_mm: int,
    espessura_mm: int,
    preco_m2: Decimal,
    fator_base: Decimal,
    quantidade: int,
    desconto_quantidade=None,
    proxima_faixa=None,
) -> ResultadoCalculoOrcamento:
    base_m = Decimal(base_mm) / METROS_POR_MILIMETRO
    altura_m = Decimal(altura_mm) / METROS_POR_MILIMETRO
    area_m2 = base_m * altura_m
    valor_unitario_base = (area_m2 * Decimal(espessura_mm) * preco_m2 * fator_base).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    desconto_quantidade = desconto_quantidade or obter_desconto_por_quantidade(
        quantidade=quantidade
    )
    valor_unitario_com_desconto = (
        valor_unitario_base * desconto_quantidade.fator_desconto
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    subtotal_sem_desconto = (
        valor_unitario_base * Decimal(quantidade)
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    valor_total = (valor_unitario_com_desconto * Decimal(quantidade)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    percentual_desconto = (
        (Decimal("1.00") - desconto_quantidade.fator_desconto) * Decimal("100")
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    proxima_faixa_label = None
    proximo_valor_unitario_brl = None
    if proxima_faixa:
        proximo_valor_unitario = (
            valor_unitario_base * proxima_faixa.fator_desconto
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        proxima_faixa_label = formatar_faixa_desconto(proxima_faixa)
        proximo_valor_unitario_brl = formatar_brl(proximo_valor_unitario)

    return ResultadoCalculoOrcamento(
        area_m2=area_m2.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP),
        quantidade=quantidade,
        valor_unitario_base=valor_unitario_base,
        valor_unitario_base_brl=formatar_brl(valor_unitario_base),
        valor_unitario_com_desconto=valor_unitario_com_desconto,
        valor_unitario_com_desconto_brl=formatar_brl(valor_unitario_com_desconto),
        subtotal_sem_desconto=subtotal_sem_desconto,
        subtotal_sem_desconto_brl=formatar_brl(subtotal_sem_desconto),
        fator_desconto=desconto_quantidade.fator_desconto,
        percentual_desconto=percentual_desconto,
        faixa_desconto_label=formatar_faixa_desconto(desconto_quantidade),
        valor_total=valor_total,
        valor_total_brl=formatar_brl(valor_total),
        proxima_faixa_label=proxima_faixa_label,
        proximo_valor_unitario_brl=proximo_valor_unitario_brl,
    )


def calcular_orcamento_catalogo(*, tamanho, espessura, material, tipo_base) -> ResultadoCalculoOrcamento:
    fator_relacao = obter_fator_base_por_tamanho(tipo_base=tipo_base, tamanho=tamanho)
    desconto_quantidade = obter_desconto_por_quantidade(quantidade=1)
    return calcular_orcamento_com_quantidade(
        base_mm=tamanho.base_mm,
        altura_mm=tamanho.altura_mm,
        espessura_mm=espessura.milimetros,
        preco_m2=material.preco_m2,
        fator_base=fator_relacao.fator_base,
        quantidade=1,
        desconto_quantidade=desconto_quantidade,
        proxima_faixa=obter_proxima_faixa_desconto(quantidade=1),
    )


def calcular_orcamento_catalogo_com_quantidade(
    *, tamanho, espessura, material, tipo_base, quantidade: int
) -> ResultadoCalculoOrcamento:
    fator_relacao = obter_fator_base_por_tamanho(tipo_base=tipo_base, tamanho=tamanho)
    desconto_quantidade = obter_desconto_por_quantidade(quantidade=quantidade)
    return calcular_orcamento_com_quantidade(
        base_mm=tamanho.base_mm,
        altura_mm=tamanho.altura_mm,
        espessura_mm=espessura.milimetros,
        preco_m2=material.preco_m2,
        fator_base=fator_relacao.fator_base,
        quantidade=quantidade,
        desconto_quantidade=desconto_quantidade,
        proxima_faixa=obter_proxima_faixa_desconto(quantidade=quantidade),
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


def obter_desconto_por_quantidade(*, quantidade: int) -> DescontoQuantidade:
    for desconto in DescontoQuantidade.objects.order_by("quantidade_min", "id"):
        if quantidade >= desconto.quantidade_min and (
            desconto.quantidade_max is None or quantidade <= desconto.quantidade_max
        ):
            return desconto

    raise DescontoQuantidadeNaoConfiguradoError(
        "Não existe faixa de desconto configurada para a quantidade informada."
    )


def obter_proxima_faixa_desconto(*, quantidade: int) -> DescontoQuantidade | None:
    return (
        DescontoQuantidade.objects.filter(quantidade_min__gt=quantidade)
        .order_by("quantidade_min", "id")
        .first()
    )


def formatar_faixa_desconto(desconto_quantidade: DescontoQuantidade) -> str:
    if desconto_quantidade.quantidade_max:
        return (
            f"{desconto_quantidade.quantidade_min} a "
            f"{desconto_quantidade.quantidade_max} unidades"
        )
    return f"{desconto_quantidade.quantidade_min}+ unidades"


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
        "quantidade": resultado.quantidade,
        "desconto_quantidade": {
            "faixa": resultado.faixa_desconto_label,
            "fator_desconto": f"{resultado.fator_desconto:.2f}",
            "percentual_desconto": f"{resultado.percentual_desconto:.2f}",
        },
        "calculo": {
            "area_m2": f"{resultado.area_m2:.6f}",
            "valor_unitario_base": f"{resultado.valor_unitario_base:.2f}",
            "valor_unitario_base_brl": resultado.valor_unitario_base_brl,
            "valor_unitario_com_desconto": f"{resultado.valor_unitario_com_desconto:.2f}",
            "valor_unitario_com_desconto_brl": resultado.valor_unitario_com_desconto_brl,
            "subtotal_sem_desconto": f"{resultado.subtotal_sem_desconto:.2f}",
            "subtotal_sem_desconto_brl": resultado.subtotal_sem_desconto_brl,
            "valor_total": f"{resultado.valor_total:.2f}",
            "valor_total_brl": resultado.valor_total_brl,
        },
    }


def registrar_orcamento_calculado(
    *,
    nome_orcamento,
    data_orcamento,
    tamanho,
    espessura,
    material,
    tipo_base,
    quantidade,
):
    resultado = calcular_orcamento_catalogo_com_quantidade(
        tamanho=tamanho,
        espessura=espessura,
        material=material,
        tipo_base=tipo_base,
        quantidade=quantidade,
    )
    orcamento = Orcamento.objects.create(
        nome_orcamento=nome_orcamento,
        data_orcamento=data_orcamento,
        tamanho=tamanho,
        espessura=espessura,
        material=material,
        tipo_base=tipo_base,
        quantidade=quantidade,
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
