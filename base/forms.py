from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import DescontoQuantidade, Espessura, FatorBaseTamanho, Material, Tamanho, TipoBase
from .services.orcamentos import FatorBaseNaoConfiguradoError, obter_fator_base_por_tamanho


INPUT_CLASSES = (
    "w-full rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 "
    "text-sm text-slate-100 outline-none ring-0 transition "
    "focus:border-cyan-400"
)


class TailwindFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            current_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{current_class} {INPUT_CLASSES}".strip()


class OrcamentoPublicoForm(forms.Form):
    nome_orcamento = forms.CharField(
        label="Nome do orçamento",
        max_length=120,
        widget=forms.TextInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Ex.: Totem recepção",
            }
        ),
    )
    data_orcamento = forms.DateField(
        initial=timezone.localdate,
        input_formats=["%Y-%m-%d"],
        widget=forms.HiddenInput(),
    )
    tamanho = forms.ModelChoiceField(
        label="Tamanho",
        queryset=Tamanho.objects.none(),
        empty_label="Selecione um tamanho",
        widget=forms.Select(attrs={"class": INPUT_CLASSES}),
    )
    espessura = forms.ModelChoiceField(
        label="Espessura",
        queryset=Espessura.objects.none(),
        empty_label="Selecione uma espessura",
        widget=forms.Select(attrs={"class": INPUT_CLASSES}),
    )
    material = forms.ModelChoiceField(
        label="Material",
        queryset=Material.objects.none(),
        empty_label="Selecione um material",
        widget=forms.Select(attrs={"class": INPUT_CLASSES}),
    )
    tipo_base = forms.ModelChoiceField(
        label="Tipo de base",
        queryset=TipoBase.objects.none(),
        empty_label="Selecione um tipo de base",
        widget=forms.Select(attrs={"class": INPUT_CLASSES}),
    )
    quantidade = forms.IntegerField(
        label="Quantidade",
        min_value=1,
        initial=1,
        widget=forms.NumberInput(
            attrs={
                "class": INPUT_CLASSES,
                "placeholder": "Ex.: 10",
                "min": "1",
                "step": "1",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tamanho"].queryset = Tamanho.objects.all()
        self.fields["espessura"].queryset = Espessura.objects.all()
        self.fields["material"].queryset = Material.objects.all()
        self.fields["tipo_base"].queryset = TipoBase.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        tamanho = cleaned_data.get("tamanho")
        tipo_base = cleaned_data.get("tipo_base")

        if tamanho and tipo_base:
            try:
                obter_fator_base_por_tamanho(tipo_base=tipo_base, tamanho=tamanho)
            except FatorBaseNaoConfiguradoError as exc:
                raise ValidationError(str(exc))

        return cleaned_data


class AdminAuthenticationForm(TailwindFormMixin, AuthenticationForm):
    username = forms.CharField(label="Usuário")
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["autofocus"] = True

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise ValidationError(
                "Somente usuários administradores podem acessar esta área.",
                code="not_staff",
            )


class AdminModelForm(TailwindFormMixin, forms.ModelForm):
    pass


class TamanhoForm(AdminModelForm):
    class Meta:
        model = Tamanho
        fields = ["nome", "base_mm", "altura_mm"]
        labels = {
            "nome": "Nome",
            "base_mm": "Base (mm)",
            "altura_mm": "Altura (mm)",
        }

    def clean_nome(self):
        return self.cleaned_data["nome"].strip()


class EspessuraForm(AdminModelForm):
    class Meta:
        model = Espessura
        fields = ["milimetros"]
        labels = {"milimetros": "Espessura (mm)"}


class MaterialForm(AdminModelForm):
    class Meta:
        model = Material
        fields = ["tipo", "preco_m2"]
        labels = {
            "tipo": "Material",
            "preco_m2": "Preço por m² (R$)",
        }

    def clean_tipo(self):
        return self.cleaned_data["tipo"].strip()


class TipoBaseForm(AdminModelForm):
    class Meta:
        model = TipoBase
        fields = ["nome_base"]
        labels = {
            "nome_base": "Tipo de base",
        }

    def clean_nome_base(self):
        return self.cleaned_data["nome_base"].strip()


class FatorBaseTamanhoForm(AdminModelForm):
    class Meta:
        model = FatorBaseTamanho
        fields = ["tipo_base", "tamanho", "fator_base"]
        labels = {
            "tipo_base": "Tipo de base",
            "tamanho": "Tamanho",
            "fator_base": "Fator multiplicador",
        }


class DescontoQuantidadeForm(AdminModelForm):
    class Meta:
        model = DescontoQuantidade
        fields = ["quantidade_min", "quantidade_max", "fator_desconto"]
        labels = {
            "quantidade_min": "Quantidade mínima",
            "quantidade_max": "Quantidade máxima",
            "fator_desconto": "Fator de desconto",
        }

    def clean(self):
        cleaned_data = super().clean()
        quantidade_min = cleaned_data.get("quantidade_min")
        quantidade_max = cleaned_data.get("quantidade_max")

        if quantidade_min and quantidade_max and quantidade_max < quantidade_min:
            raise ValidationError(
                "A quantidade máxima deve ser maior ou igual à quantidade mínima."
            )

        return cleaned_data
