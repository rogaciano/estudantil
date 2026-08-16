# Deploy na VPS

Este projeto foi preparado para deploy com `Gunicorn + Nginx` em uma VPS Linux.

## 1. Publicar o projeto

Você já criou o repositório:

```bash
https://github.com/rogaciano/estudantil
```

Na VPS, publique o projeto em um diretório como:

```bash
/var/www/calculadora-placas
```

Exemplo com Git:

```bash
cd /var/www
sudo git clone https://github.com/rogaciano/estudantil calculadora-placas
sudo chown -R $USER:$USER /var/www/calculadora-placas
cd /var/www/calculadora-placas
```

## 2. Criar ambiente virtual e instalar dependências

```bash
cd /var/www/calculadora-placas
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. Criar arquivo `.env`

Use o arquivo `.env.example` como base:

```bash
cp .env.example .env
```

Ajuste pelo menos:

- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`

Para este projeto, os valores esperados são:

- `DJANGO_ALLOWED_HOSTS=estudantil.caruaru.tec.br`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://estudantil.caruaru.tec.br`

## 4. Aplicar banco e estáticos

```bash
source .venv/bin/activate
python manage.py migrate
python manage.py seed_catalogo
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

## 5. Validar configuração de produção

```bash
source .venv/bin/activate
DJANGO_DEBUG=False python manage.py check --deploy
```

## 6. Configurar Gunicorn

Use `deploy/gunicorn.service.example` como base para um service do `systemd`.

Exemplo:

```bash
sudo cp deploy/gunicorn.service.example /etc/systemd/system/calculadora-placas.service
sudo systemctl daemon-reload
sudo systemctl enable calculadora-placas
sudo systemctl start calculadora-placas
sudo systemctl status calculadora-placas
```

## 7. Configurar Nginx

Use `deploy/nginx.site.example` como base.

Exemplo:

```bash
sudo cp deploy/nginx.site.example /etc/nginx/sites-available/calculadora-placas
sudo ln -s /etc/nginx/sites-available/calculadora-placas /etc/nginx/sites-enabled/calculadora-placas
sudo nginx -t
sudo systemctl reload nginx
```

## 8. HTTPS

Se usar Certbot:

```bash
sudo certbot --nginx -d estudantil.caruaru.tec.br
```

## Observações

- O projeto continua usando `SQLite`, como definido no escopo.
- Em produção, `DEBUG` deve ficar `False`.
- Os arquivos estáticos serão servidos em `/static/`.
- O proxy reverso deve enviar `X-Forwarded-Proto`, já previsto na configuração do Nginx de exemplo.
