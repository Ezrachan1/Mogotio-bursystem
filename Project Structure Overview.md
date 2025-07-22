constituency_bursary/
├── manage.py
├── requirements.txt
├── .env.example
├── .env
├── .gitignore
├── README.md
├── Project Structure Overview.md
├── constituency_bursary/
│ ├── **init**.py
│ ├── settings.py
│ ├── urls.py
│ ├── wsgi.py
│ ├── context_processors.py
│ ├── views.py
│ └── asgi.py
├── accounts/
│ ├── **init**.py
│ ├── models.py
│ ├── api_urls.py
│ ├── apps.py
│ ├── views.py
│ ├── forms.py
│ ├── urls.py
│ ├── admin.py
│ ├── signals.py
│ └── serializers.py
├── bursary/
│ ├── management/
│ │ ├── seed_data.py
│ │ ├── test_email.py
│ │ ├── test_outlook.py
│ ├── **init**.py
│ ├── models.py
│ ├── apps.py
│ ├── api_urls.py
│ ├── signals.py
│ ├── views.py
│ ├── serializers.py
│ ├── forms.py
│ ├── urls.py
│ ├── utils.py
│ ├── admin.py
│ └── utils.py
├── templates/
│ ├── base.html
│ ├── home.html
│ ├── 404.html
│ ├── 500.html
│ ├── emails/
│ │ ├── application_status_update.html
│ │ ├── application_status_update.txt
│ │ ├── application_submitted.html
│ │ ├── base_email.html
│ │ ├── verification_code.html
│ │ ├── verification_code.txt
│ │ ├── application_submitted.txt
│ ├── accounts/
│ │ ├── login.html
│ │ ├── register.html
│ │ ├── password_reset_done.html
│ │ ├── password_reset.html
│ │ ├── profile_edit.html
│ │ ├── password_change_done.html
│ │ ├── password_change.html
│ │ ├── password_reset_complete.html
│ │ ├── password_reset_confirm.html
│ │ ├── password_reset_email.html
│ │ ├── password_reset_subject.txt
│ │ ├── verify_email.html
│ │ └── profile.html
│ └── bursary/
│ ├── emails/
│ │ ├── application_confirmation.html
│ │ ├── verify_email.html
│ ├── application_form.html
│ ├── application_detail.html
│ ├── academic_year_form.html
│ ├── academic_year_list.html
│ ├── application_list.html
│ ├── admin_application_list.html
│ ├── academic_confirm_delete.html
│ ├── disbursement_detail.html
│ ├── disbursement_form.html 
│ ├── disbursement_list.html
│ ├── application_review.html
│ ├── application_status.html
│ ├── dashboard.html
│ ├── document_upload.html
│ ├── reports.html
│ ├── institution_form.html
│ ├── institution_list.html
│ └── admin_dashboard.html \*\*
├── static/
│ ├── css/
│ │ └── style.css
│ └── js/
│ ├── reports.js
│ └── main.js
└── media/
└── documents/
