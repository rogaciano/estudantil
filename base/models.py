from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Tamanho(models.Model):
    nome = models.CharField(max_length=50, unique=True)
    base_mm = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    altura_mm = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        db_table = "tamanhos"
        ordering = ["base_mm", "altura_mm"]

    def __str__(self) -> str:
        return f"{self.nome} ({self.base_mm}x{self.altura_mm})"


class Espessura(models.Model):
    milimetros = models.PositiveIntegerField(
        unique=True,
        validators=[MinValueValidator(1)],
    )

    class Meta:
        db_table = "espessuras"
        ordering = ["milimetros"]

    def __str__(self) -> str:
        return f"{self.milimetros} mm"


class Material(models.Model):
    tipo = models.CharField(max_length=100, unique=True)
    preco_m2 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    class Meta:
        db_table = "materiais"
        ordering = ["tipo"]

    def __str__(self) -> str:
        return f"{self.tipo} ({self.preco_m2})"


class TipoBase(models.Model):
    nome_base = models.CharField(max_length=100, unique=True)
    fator_base = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )

    class Meta:
        db_table = "tipos_bases"
        ordering = ["nome_base"]

    def __str__(self) -> str:
        return f"{self.nome_base} ({self.fator_base})"


class Orcamento(models.Model):
    nome_orcamento = models.CharField(max_length=120)
    data_orcamento = models.DateField(default=timezone.localdate)
    tamanho = models.ForeignKey(
        Tamanho,
        on_delete=models.PROTECT,
        related_name="orcamentos",
    )
    espessura = models.ForeignKey(
        Espessura,
        on_delete=models.PROTECT,
        related_name="orcamentos",
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name="orcamentos",
    )
    tipo_base = models.ForeignKey(
        TipoBase,
        on_delete=models.PROTECT,
        related_name="orcamentos",
    )
    valor_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    detalhes_json = models.JSONField(default=dict)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orcamentos"
        ordering = ["-data_orcamento", "-id"]

    def __str__(self) -> str:
        return f"{self.nome_orcamento} - {self.data_orcamento}"
