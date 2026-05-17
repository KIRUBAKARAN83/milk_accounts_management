# Milk Billing Django Project (Professional Dashboard)

## Quick start

1. Create virtualenv:
   python -m venv venv
   source venv/bin/activate

2. Install requirements:
   pip install -r requirements.txt

3. Run migrations:
   python manage.py makemigrations
   python manage.py migrate

4. Create superuser:
   python manage.py createsuperuser

5. Run server:
   python manage.py runserver

## Notes
- Update `milkproject/settings.py` secrets for production.
- For WhatsApp, set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN in environment.


# Milk Billing System

A Django-based web application for managing milk billing records with customer accounts, monthly summaries, and PDF bill generation.

## Features

- ✅ Customer management (add, edit, delete)
- ✅ Milk entry tracking (add, edit, delete)
- ✅ Month-wise account management
- ✅ PDF bill generation (full & month-wise)
- ✅ Monthly summary reports
- ✅ Daily milk chart visualization
- ✅ Select2 searchable customer dropdown
- ✅ Bootstrap 5 responsive UI

## Installation

### Prerequisites
- Python 3.13+
- pip

### Setup

1. Clone the repository
```bash
git clone https://github.com/yourusername/milk_billing_complete.git
cd milk_billing_complete
```

2. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Apply migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Create superuser
```bash
python manage.py createsuperuser
```

6. Run development server
```bash
python manage.py runserver
```

7. Open browser
```
http://127.0.0.1:8000
```

## Usage

- **Dashboard**: View summary of customers, milk entries, and totals
- **Customers**: Manage customer profiles and view account history
- **Add Entry**: Record daily milk deliveries
- **Monthly Summary**: View aggregated monthly reports
- **PDF Bills**: Download customer bills (full or month-wise)

## Technology Stack

- **Backend**: Django 4.2.6
- **Database**: SQLite
- **Frontend**: Bootstrap 5, Chart.js, Select2
- **PDF**: ReportLab

## Project Structure

```
milk_billing_complete/
├── accounts/
│   ├── migrations/
│   ├── static/
│   │   └── accounts/
│   │       └── js/
│   │           └── chart.js
│   ├── templates/
│   │   └── accounts/
│   │       ├── home.html
│   │       ├── customer_list.html
│   │       ├── customer_detail.html
│   │       ├── customer_form.html
│   │       ├── entry_form.html
│   │       ├── bill_pdf.html
│   │       └── monthly_summary.html
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   ├── pdf_generation.py
│   └── admin.py
├── milk_billing_complete/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Configuration

Edit `milk_billing_complete/settings.py`:

```python
PRICE_PER_LITRE = 50.0  # Set your milk price
```

## API Endpoints

- `GET /` - Dashboard
- `GET /customers/` - Customer list
- `GET /customers/<id>/` - Customer detail (month-wise)
- `POST /customers/<id>/edit/` - Edit customer
- `POST /customers/<id>/delete/` - Delete customer
- `GET /customers/<id>/bill-pdf/` - Download full bill
- `GET /customers/<id>/bill-pdf/<year>/<month>/` - Download month bill
- `GET /entry/add/` - Add milk entry form
- `POST /entry/add/` - Save milk entry
- `POST /entry/<id>/edit/` - Edit milk entry
- `POST /entry/<id>/delete/` - Delete milk entry
- `GET /monthly-summary/` - Monthly summary report

## Author

kirubakaran

## License

MIT License
